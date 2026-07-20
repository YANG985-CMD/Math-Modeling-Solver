#!/usr/bin/env python3
"""Run a model command and automatically record its inspectable experiment result."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from register_experiment import (
    find_experiment,
    project_root_for_registry,
    read_registry,
    record,
    write_registry,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inside_project(root: Path, value: Path) -> Path:
    path = value if value.is_absolute() else root / value
    path = path.expanduser().resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("result and manifest paths must stay inside the project") from exc
    return path


def git_commit(root: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def validate_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("result JSON must be an object")
    metric = value.get("value")
    if not isinstance(metric, (int, float)) or isinstance(metric, bool):
        raise ValueError("result JSON value must be numeric")
    feasible = value.get("feasible")
    if not isinstance(feasible, bool):
        raise ValueError("result JSON feasible must be boolean")
    if value.get("fidelity") not in {"passed", "failed", "not_required"}:
        raise ValueError("result JSON fidelity is invalid")
    candidates = value.get("candidates_evaluated")
    if not isinstance(candidates, int) or isinstance(candidates, bool) or candidates < 1:
        raise ValueError("result JSON candidates_evaluated must be a positive integer")
    notes = value.get("notes", "")
    if not isinstance(notes, str):
        raise ValueError("result JSON notes must be text")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--id", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--result-json", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path)
    parser.add_argument("--timeout-seconds", type=int)
    raw = sys.argv[1:]
    if "--" not in raw:
        parser.error("separate the model command with --")
    separator = raw.index("--")
    args = parser.parse_args(raw[:separator])
    args.command = raw[separator + 1 :]
    return args


def main() -> int:
    args = parse_args()
    command = args.command
    if not command:
        print(json.dumps({"status": "failed", "issues": ["command is required"]}))
        return 2
    if args.timeout_seconds is not None and args.timeout_seconds < 1:
        print(json.dumps({"status": "failed", "issues": ["timeout must be positive"]}))
        return 2
    registry_path = args.registry.expanduser().resolve()
    root = project_root_for_registry(registry_path)
    try:
        result_path = inside_project(root, args.result_json)
        manifest_path = inside_project(
            root,
            args.manifest_out
            or result_path.with_name(result_path.stem + "-run-manifest.json"),
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        environment.update(
            {
                "MMS_EXPERIMENT_ID": args.id,
                "MMS_RESULT_JSON": str(result_path),
                "MMS_PROJECT_ROOT": str(root),
            }
        )
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=args.timeout_seconds,
        )
        runtime_minutes = max((time.perf_counter() - started) / 60.0, 1e-9)
        stdout_path = result_path.with_suffix(result_path.suffix + ".stdout.log")
        stderr_path = result_path.with_suffix(result_path.suffix + ".stderr.log")
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        manifest: dict[str, Any] = {
            "schema_version": "1.0",
            "status": "executed" if completed.returncode == 0 else "command_failed",
            "experiment_id": args.id,
            "run_id": args.run_id,
            "command": command,
            "working_directory": str(root),
            "return_code": completed.returncode,
            "runtime_minutes": runtime_minutes,
            "result_json": str(result_path),
            "stdout_log": str(stdout_path),
            "stderr_log": str(stderr_path),
            "environment": {
                "os": platform.platform(),
                "python": sys.version,
                "executable": sys.executable,
                "git_commit": git_commit(root),
            },
        }
        if completed.returncode != 0:
            write_json(manifest_path, manifest)
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return 2
        if not result_path.is_file() or result_path.stat().st_size == 0:
            raise ValueError("command completed but did not create the result JSON")
        result = validate_result(
            json.loads(result_path.read_text(encoding="utf-8-sig"))
        )
        registry = read_registry(registry_path)
        relative_result = result_path.relative_to(root).as_posix()
        record_args = SimpleNamespace(
            id=args.id,
            run_id=args.run_id,
            value=float(result["value"]),
            feasible=result["feasible"],
            fidelity=result["fidelity"],
            candidates_evaluated=result["candidates_evaluated"],
            runtime_minutes=runtime_minutes,
            artifact=relative_result,
            notes=result.get("notes", ""),
        )
        record(record_args, registry, registry_path)
        write_registry(registry_path, registry)
        experiment = find_experiment(registry, args.id)
        manifest.update(
            {
                "status": "recorded",
                "result_sha256": sha256(result_path),
                "registry_status": experiment["status"],
                "best_run": experiment["best_run"],
                "candidates_evaluated": result["candidates_evaluated"],
            }
        )
        write_json(manifest_path, manifest)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    except subprocess.TimeoutExpired as exc:
        print(
            json.dumps(
                {"status": "failed", "issues": [f"command timed out: {exc}"]},
                ensure_ascii=False,
            )
        )
        return 2
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "failed", "issues": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
