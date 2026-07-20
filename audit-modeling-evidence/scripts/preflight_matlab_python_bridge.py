#!/usr/bin/env python3
"""Preflight scalar, array, JSON, and Unicode-path exchange with MATLAB."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


SCALAR = 57.119
ARRAY = [[1.25, -2.5, 3.75], [4.0, 5.5, -6.25]]


def matlab_quote(path: Path) -> str:
    return str(path).replace("'", "''").replace("\\", "/")


def matlab_script(input_path: Path, output_path: Path) -> str:
    return f"""input_path = '{matlab_quote(input_path)}';
output_path = '{matlab_quote(output_path)}';
payload = jsondecode(fileread(input_path));
expected_array = [1.25, -2.5, 3.75; 4.0, 5.5, -6.25];
assert(abs(payload.scalar - 57.119) < 1e-12, 'Scalar mismatch');
assert(isequal(size(payload.array), size(expected_array)), 'Array shape mismatch');
assert(max(abs(payload.array - expected_array), [], 'all') < 1e-12, 'Array mismatch');
assert(strcmp(payload.unicode_token, '中文路径往返'), 'Unicode JSON mismatch');
result = struct();
result.status = 'passed';
result.scalar = payload.scalar;
result.array = payload.array;
result.unicode_token = payload.unicode_token;
result.matlab_version = version;
fid = fopen(output_path, 'w', 'n', 'UTF-8');
assert(fid >= 0, 'Cannot open output path');
cleanup = onCleanup(@() fclose(fid));
fwrite(fid, jsonencode(result), 'char');
"""


def verify_result(value: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if value.get("status") != "passed":
        issues.append("MATLAB did not return passed status")
    scalar = value.get("scalar")
    if not isinstance(scalar, (int, float)) or not math.isclose(
        float(scalar), SCALAR, rel_tol=0, abs_tol=1e-12
    ):
        issues.append("scalar round trip failed")
    if value.get("array") != ARRAY:
        issues.append("array round trip failed")
    if value.get("unicode_token") != "中文路径往返":
        issues.append("Unicode JSON round trip failed")
    if not isinstance(value.get("matlab_version"), str) or not value["matlab_version"].strip():
        issues.append("MATLAB version was not captured")
    return issues


def run_preflight(matlab: str, work_dir: Path, timeout_seconds: int) -> dict[str, Any]:
    unicode_dir = work_dir / "中文路径"
    unicode_dir.mkdir(parents=True, exist_ok=True)
    input_path = unicode_dir / "桥接输入.json"
    output_path = unicode_dir / "桥接输出.json"
    script_path = work_dir / "bridge_preflight.m"
    log_path = work_dir / "matlab-bridge-preflight.log"
    input_path.write_text(
        json.dumps(
            {
                "scalar": SCALAR,
                "array": ARRAY,
                "unicode_token": "中文路径往返",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    script_path.write_text(
        matlab_script(input_path, output_path), encoding="utf-8", newline="\n"
    )
    command = [matlab, "-batch", f"run('{matlab_quote(script_path)}')"]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout_seconds,
    )
    log_path.write_text(
        "COMMAND\n"
        + json.dumps(command, ensure_ascii=False)
        + "\n\nSTDOUT\n"
        + completed.stdout
        + "\nSTDERR\n"
        + completed.stderr,
        encoding="utf-8",
    )
    issues: list[str] = []
    returned: dict[str, Any] = {}
    if completed.returncode != 0:
        issues.append(f"MATLAB exited with code {completed.returncode}")
    elif not output_path.is_file():
        issues.append("MATLAB did not create the Unicode-path output JSON")
    else:
        try:
            value = json.loads(output_path.read_text(encoding="utf-8-sig"))
            if not isinstance(value, dict):
                issues.append("MATLAB output must be a JSON object")
            else:
                returned = value
                issues.extend(verify_result(value))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"MATLAB output JSON could not be read: {exc}")
    execution_ok = completed.returncode == 0 and output_path.is_file() and bool(returned)
    return {
        "schema_version": "1.0",
        "status": "passed" if not issues else "failed",
        "matlab_command": matlab,
        "work_dir": str(work_dir),
        "tests": {
            "scalar": "passed"
            if execution_ok and not any("scalar" in item for item in issues)
            else "failed",
            "array": "passed"
            if execution_ok and not any("array" in item for item in issues)
            else "failed",
            "json_unicode": "passed"
            if execution_ok
            and not any("Unicode" in item or "JSON" in item for item in issues)
            else "failed",
            "unicode_path": "passed"
            if completed.returncode == 0
            and output_path.is_file()
            and not any("Unicode-path" in item for item in issues)
            else "failed",
        },
        "matlab_version": returned.get("matlab_version", ""),
        "log_path": str(log_path),
        "issue_count": len(issues),
        "issues": issues,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matlab", help="MATLAB executable; defaults to PATH lookup")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    matlab = args.matlab or shutil.which("matlab")
    if not matlab:
        print(json.dumps({"status": "failed", "issues": ["MATLAB executable not found"]}))
        return 2
    if args.timeout_seconds < 1:
        print(json.dumps({"status": "failed", "issues": ["timeout must be positive"]}))
        return 2
    try:
        if args.work_dir:
            work_dir = args.work_dir.expanduser().resolve()
            work_dir.mkdir(parents=True, exist_ok=True)
            result = run_preflight(matlab, work_dir, args.timeout_seconds)
        else:
            with tempfile.TemporaryDirectory(prefix="matlab_python_bridge_") as directory:
                result = run_preflight(matlab, Path(directory), args.timeout_seconds)
                result["work_dir"] = "temporary directory removed after verification"
                result["log_path"] = "temporary log removed after verification"
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if result["status"] == "passed" else 1
    except (OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "failed", "issues": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
