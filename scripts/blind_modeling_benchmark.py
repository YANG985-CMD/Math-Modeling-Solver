#!/usr/bin/env python3
"""Prepare, freeze, and score leakage-resistant modeling triage benchmarks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable


TAG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DEFAULT_WEIGHTS = {
    "routing": 0.35,
    "baseline": 0.20,
    "validation": 0.30,
    "data_risks": 0.15,
}
STABILITY_FIELDS = (
    "task_families",
    "baseline_families",
    "validation_safeguards",
    "data_risks",
)


class BenchmarkError(ValueError):
    """Raised when a benchmark artifact violates its contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BenchmarkError(f"{path} must contain one JSON object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_text(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkError(f"{location} must be a non-empty string")
    return value.strip()


def require_tag(value: Any, location: str) -> str:
    tag = require_text(value, location)
    if not TAG_PATTERN.fullmatch(tag):
        raise BenchmarkError(f"{location} must use lowercase hyphen-case: {tag!r}")
    return tag


def require_tags(value: Any, location: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        qualifier = "a list" if allow_empty else "a non-empty list"
        raise BenchmarkError(f"{location} must be {qualifier} of canonical tags")
    tags: list[str] = []
    for index, item in enumerate(value):
        tag = require_text(item, f"{location}[{index}]")
        if not TAG_PATTERN.fullmatch(tag):
            raise BenchmarkError(
                f"{location}[{index}] must use lowercase hyphen-case: {tag!r}"
            )
        tags.append(tag)
    if len(tags) != len(set(tags)):
        raise BenchmarkError(f"{location} contains duplicate tags")
    return tags


def validate_suite(suite: dict[str, Any]) -> dict[str, Any]:
    if suite.get("schema_version") != "1.0":
        raise BenchmarkError("Suite schema_version must be '1.0'")
    require_text(suite.get("suite_id"), "suite_id")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise BenchmarkError("Suite must contain at least one case")
    case_ids: set[str] = set()
    for case_index, case in enumerate(cases):
        location = f"cases[{case_index}]"
        if not isinstance(case, dict):
            raise BenchmarkError(f"{location} must be an object")
        case_id = require_tag(case.get("case_id"), f"{location}.case_id")
        if case_id in case_ids:
            raise BenchmarkError(f"Duplicate case_id: {case_id}")
        case_ids.add(case_id)
        require_text(case.get("title"), f"{location}.title")
        require_tags(
            case.get("declared_subproblem_ids"),
            f"{location}.declared_subproblem_ids",
        )
        materials = case.get("materials")
        if not isinstance(materials, list) or not materials:
            raise BenchmarkError(f"{location}.materials must be a non-empty list")
        statement_count = 0
        file_names: set[str] = set()
        hashes: set[str] = set()
        for material_index, material in enumerate(materials):
            material_location = f"{location}.materials[{material_index}]"
            if not isinstance(material, dict):
                raise BenchmarkError(f"{material_location} must be an object")
            role = require_text(material.get("role"), f"{material_location}.role")
            if role not in {"statement", "attachment", "reference"}:
                raise BenchmarkError(
                    f"{material_location}.role must be statement, attachment, or reference"
                )
            statement_count += role == "statement"
            url = require_text(material.get("url"), f"{material_location}.url")
            if not re.match(r"^(?:https?|file)://", url):
                raise BenchmarkError(f"{material_location}.url uses an unsupported scheme")
            file_name = require_text(
                material.get("file_name"), f"{material_location}.file_name"
            )
            if Path(file_name).name != file_name:
                raise BenchmarkError(f"{material_location}.file_name must be a base name")
            if file_name in file_names:
                raise BenchmarkError(f"Duplicate file_name in {case_id}: {file_name}")
            file_names.add(file_name)
            expected_hash = require_text(
                material.get("sha256"), f"{material_location}.sha256"
            ).lower()
            if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
                raise BenchmarkError(f"{material_location}.sha256 is invalid")
            if expected_hash in hashes:
                raise BenchmarkError(f"Duplicate material hash in {case_id}")
            hashes.add(expected_hash)
            if material.get("redistribution") != "external-only":
                raise BenchmarkError(
                    f"{material_location}.redistribution must be 'external-only'"
                )
        if statement_count != 1:
            raise BenchmarkError(f"{case_id} must declare exactly one statement")
    return suite


def selected_cases(suite: dict[str, Any], case_ids: list[str] | None) -> list[dict[str, Any]]:
    cases = suite["cases"]
    if not case_ids:
        return cases
    available = {case["case_id"]: case for case in cases}
    unknown = sorted(set(case_ids) - set(available))
    if unknown:
        raise BenchmarkError(f"Unknown case ids: {', '.join(unknown)}")
    return [available[case_id] for case_id in case_ids]


def download_material(url: str, destination: Path, expected_hash: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        actual_hash = sha256_file(destination)
        if actual_hash == expected_hash:
            return
        raise BenchmarkError(
            f"Existing material hash mismatch: {destination} ({actual_hash})"
        )
    temporary = destination.with_suffix(destination.suffix + ".download")
    if temporary.exists():
        temporary.unlink()
    safe_url = urllib.parse.quote(url, safe=":/?=&%")
    last_error: Exception | None = None
    for attempt in range(3):
        request = urllib.request.Request(
            safe_url, headers={"User-Agent": "math-modeling-solver"}
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response, temporary.open(
                "wb"
            ) as handle:
                shutil.copyfileobj(response, handle)
            last_error = None
            break
        except Exception as exc:
            last_error = exc
            if temporary.exists():
                temporary.unlink()
            if attempt < 2:
                time.sleep(2**attempt)
    if last_error is not None:
        raise BenchmarkError(f"Failed to download {url}: {last_error}") from last_error
    actual_hash = sha256_file(temporary)
    if actual_hash != expected_hash:
        temporary.unlink()
        raise BenchmarkError(
            f"Downloaded material hash mismatch for {url}: {actual_hash}"
        )
    temporary.replace(destination)


def prepare_suite(
    suite_path: Path, output_dir: Path, case_ids: list[str] | None = None
) -> dict[str, Any]:
    suite = validate_suite(load_json(suite_path))
    output_dir = output_dir.expanduser().resolve()
    prepared: list[dict[str, Any]] = []
    for case in selected_cases(suite, case_ids):
        case_materials: list[dict[str, Any]] = []
        for material in case["materials"]:
            destination = output_dir / case["case_id"] / material["file_name"]
            download_material(material["url"], destination, material["sha256"])
            case_materials.append(
                {
                    "role": material["role"],
                    "local_path": str(destination),
                    "sha256": sha256_file(destination),
                    "size_bytes": destination.stat().st_size,
                    "source_url": material["url"],
                }
            )
        prepared.append({"case_id": case["case_id"], "materials": case_materials})
    index = {
        "schema_version": "1.0",
        "suite_id": suite["suite_id"],
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "suite_sha256": sha256_file(suite_path),
        "policy": "Only declared statements, attachments, and references were downloaded. Solution materials are forbidden.",
        "cases": prepared,
    }
    write_json(output_dir / "material-index.json", index)
    return index


def validate_response(response: dict[str, Any], suite: dict[str, Any]) -> dict[str, Any]:
    if response.get("schema_version") != "1.0":
        raise BenchmarkError("Response schema_version must be '1.0'")
    if response.get("suite_id") != suite["suite_id"]:
        raise BenchmarkError("Response suite_id does not match the public suite")
    require_text(response.get("run_id"), "run_id")
    if response.get("solution_materials_read") is not False:
        raise BenchmarkError("solution_materials_read must be explicitly false")
    require_text(response.get("blind_attestation"), "blind_attestation")
    response_cases = response.get("cases")
    if not isinstance(response_cases, list):
        raise BenchmarkError("Response cases must be a list")
    expected_cases = {case["case_id"]: case for case in suite["cases"]}
    actual_ids = [case.get("case_id") for case in response_cases if isinstance(case, dict)]
    if len(actual_ids) != len(response_cases) or set(actual_ids) != set(expected_cases):
        raise BenchmarkError("Response must contain every suite case exactly once")
    if len(actual_ids) != len(set(actual_ids)):
        raise BenchmarkError("Response contains duplicate case ids")
    for case_index, response_case in enumerate(response_cases):
        location = f"cases[{case_index}]"
        case_id = response_case["case_id"]
        suite_case = expected_cases[case_id]
        allowed_hashes = {
            material["sha256"]: material["role"] for material in suite_case["materials"]
        }
        read_hashes = require_tags_or_hashes(
            response_case.get("materials_read_sha256"),
            f"{location}.materials_read_sha256",
        )
        unknown_hashes = sorted(set(read_hashes) - set(allowed_hashes))
        if unknown_hashes:
            raise BenchmarkError(
                f"{location} declares undeclared material hashes: {', '.join(unknown_hashes)}"
            )
        statement_hashes = {
            value for value, role in allowed_hashes.items() if role == "statement"
        }
        if not statement_hashes.issubset(read_hashes):
            raise BenchmarkError(f"{location} must read the declared problem statement")
        subproblems = response_case.get("subproblems")
        if not isinstance(subproblems, list) or not subproblems:
            raise BenchmarkError(f"{location}.subproblems must be non-empty")
        subproblem_ids: set[str] = set()
        for sub_index, subproblem in enumerate(subproblems):
            sub_location = f"{location}.subproblems[{sub_index}]"
            if not isinstance(subproblem, dict):
                raise BenchmarkError(f"{sub_location} must be an object")
            subproblem_id = require_tag(subproblem.get("id"), f"{sub_location}.id")
            if subproblem_id in subproblem_ids:
                raise BenchmarkError(f"Duplicate subproblem id in {case_id}: {subproblem_id}")
            subproblem_ids.add(subproblem_id)
            require_text(subproblem.get("objective"), f"{sub_location}.objective")
            require_tags(subproblem.get("task_families"), f"{sub_location}.task_families")
            require_tags(
                subproblem.get("baseline_families"),
                f"{sub_location}.baseline_families",
            )
            candidates = subproblem.get("candidate_models")
            if not isinstance(candidates, list) or len(candidates) < 2:
                raise BenchmarkError(f"{sub_location}.candidate_models needs at least two models")
            for candidate_index, candidate in enumerate(candidates):
                require_text(candidate, f"{sub_location}.candidate_models[{candidate_index}]")
            require_text(subproblem.get("selected_model"), f"{sub_location}.selected_model")
            require_tags(
                subproblem.get("validation_safeguards"),
                f"{sub_location}.validation_safeguards",
            )
            require_tags(
                subproblem.get("data_risks"),
                f"{sub_location}.data_risks",
                allow_empty=True,
            )
            require_text(
                subproblem.get("output_contract"), f"{sub_location}.output_contract"
            )
            assumptions = subproblem.get("assumptions")
            if not isinstance(assumptions, list):
                raise BenchmarkError(f"{sub_location}.assumptions must be a list")
            for assumption_index, assumption in enumerate(assumptions):
                require_text(assumption, f"{sub_location}.assumptions[{assumption_index}]")
        edges = response_case.get("dependency_edges")
        if not isinstance(edges, list):
            raise BenchmarkError(f"{location}.dependency_edges must be a list")
        for edge_index, edge in enumerate(edges):
            require_text(edge, f"{location}.dependency_edges[{edge_index}]")
        unresolved = response_case.get("unresolved_risks")
        if not isinstance(unresolved, list):
            raise BenchmarkError(f"{location}.unresolved_risks must be a list")
        for risk_index, risk in enumerate(unresolved):
            require_text(risk, f"{location}.unresolved_risks[{risk_index}]")
        expected_subproblem_ids = set(suite_case["declared_subproblem_ids"])
        if subproblem_ids != expected_subproblem_ids:
            raise BenchmarkError(
                f"{location} subproblem ids must be exactly: "
                f"{', '.join(sorted(expected_subproblem_ids))}"
            )
    return response


def require_tags_or_hashes(value: Any, location: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise BenchmarkError(f"{location} must be a non-empty list of SHA-256 hashes")
    hashes: list[str] = []
    for index, item in enumerate(value):
        digest = require_text(item, f"{location}[{index}]").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise BenchmarkError(f"{location}[{index}] is not a SHA-256 hash")
        hashes.append(digest)
    if len(hashes) != len(set(hashes)):
        raise BenchmarkError(f"{location} contains duplicate hashes")
    return hashes


def freeze_response(suite_path: Path, response_path: Path, output_path: Path) -> dict[str, Any]:
    suite = validate_suite(load_json(suite_path))
    response = validate_response(load_json(response_path), suite)
    payload = {
        "schema_version": "1.0",
        "suite_id": suite["suite_id"],
        "run_id": response["run_id"],
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "suite_sha256": sha256_file(suite_path),
        "response_source_sha256": sha256_file(response_path),
        "response": response,
    }
    frozen = dict(payload)
    frozen["frozen_payload_sha256"] = sha256_bytes(canonical_bytes(payload))
    write_json(output_path, frozen)
    return frozen


def validate_frozen(frozen: dict[str, Any]) -> dict[str, Any]:
    expected_hash = require_text(
        frozen.get("frozen_payload_sha256"), "frozen_payload_sha256"
    )
    payload = {key: value for key, value in frozen.items() if key != "frozen_payload_sha256"}
    actual_hash = sha256_bytes(canonical_bytes(payload))
    if actual_hash != expected_hash:
        raise BenchmarkError("Frozen response hash is invalid; the artifact was changed")
    if frozen.get("schema_version") != "1.0":
        raise BenchmarkError("Frozen response schema_version must be '1.0'")
    if not isinstance(frozen.get("response"), dict):
        raise BenchmarkError("Frozen response is missing its response object")
    return frozen


def validate_rubric(rubric: dict[str, Any]) -> dict[str, Any]:
    if rubric.get("schema_version") != "1.0":
        raise BenchmarkError("Rubric schema_version must be '1.0'")
    require_text(rubric.get("suite_id"), "rubric.suite_id")
    cases = rubric.get("cases")
    if not isinstance(cases, list) or not cases:
        raise BenchmarkError("Rubric must contain cases")
    case_ids: set[str] = set()
    for case_index, case in enumerate(cases):
        location = f"rubric.cases[{case_index}]"
        case_id = require_tag(case.get("case_id"), f"{location}.case_id")
        if case_id in case_ids:
            raise BenchmarkError(f"Rubric repeats case: {case_id}")
        case_ids.add(case_id)
        subproblems = case.get("subproblems")
        if not isinstance(subproblems, list) or not subproblems:
            raise BenchmarkError(f"{location}.subproblems must be non-empty")
        ids: set[str] = set()
        for sub_index, subproblem in enumerate(subproblems):
            sub_location = f"{location}.subproblems[{sub_index}]"
            subproblem_id = require_tag(subproblem.get("id"), f"{sub_location}.id")
            if subproblem_id in ids:
                raise BenchmarkError(f"Rubric repeats {case_id}/{subproblem_id}")
            ids.add(subproblem_id)
            required_routes = require_tags(
                subproblem.get("required_task_families"),
                f"{sub_location}.required_task_families",
            )
            accepted_routes = require_tags(
                subproblem.get("accepted_task_families", required_routes),
                f"{sub_location}.accepted_task_families",
            )
            if not set(required_routes).issubset(accepted_routes):
                raise BenchmarkError(
                    f"{sub_location}.accepted_task_families must include all required families"
                )
            require_tags(
                subproblem.get("accepted_baseline_families"),
                f"{sub_location}.accepted_baseline_families",
            )
            require_tags(
                subproblem.get("required_validation_safeguards"),
                f"{sub_location}.required_validation_safeguards",
            )
            require_tags(
                subproblem.get("required_data_risks"),
                f"{sub_location}.required_data_risks",
                allow_empty=True,
            )
    weights = rubric.get("weights", DEFAULT_WEIGHTS)
    if not isinstance(weights, dict) or set(weights) != set(DEFAULT_WEIGHTS):
        raise BenchmarkError(f"Rubric weights must contain: {', '.join(DEFAULT_WEIGHTS)}")
    if any(not isinstance(value, (int, float)) or value < 0 for value in weights.values()):
        raise BenchmarkError("Rubric weights must be non-negative numbers")
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise BenchmarkError("Rubric weights must sum to 1.0")
    return rubric


def f1_route_score(response_tags: Iterable[str], required: Iterable[str], accepted: Iterable[str]) -> float:
    response_set = set(response_tags)
    required_set = set(required)
    accepted_set = set(accepted)
    recall = len(response_set & required_set) / len(required_set) if required_set else 1.0
    precision = len(response_set & accepted_set) / len(response_set) if response_set else 0.0
    if recall + precision == 0:
        return 0.0
    return 2 * recall * precision / (recall + precision)


def recall_score(response_tags: Iterable[str], required: Iterable[str]) -> float:
    required_set = set(required)
    if not required_set:
        return 1.0
    return len(set(response_tags) & required_set) / len(required_set)


def score_run(frozen: dict[str, Any], rubric: dict[str, Any]) -> dict[str, Any]:
    response = frozen["response"]
    response_cases = {case["case_id"]: case for case in response["cases"]}
    weights = rubric.get("weights", DEFAULT_WEIGHTS)
    case_results: list[dict[str, Any]] = []
    for case_rubric in rubric["cases"]:
        case_id = case_rubric["case_id"]
        response_case = response_cases.get(case_id, {"subproblems": []})
        response_subproblems = {
            subproblem["id"]: subproblem for subproblem in response_case["subproblems"]
        }
        subproblem_results: list[dict[str, Any]] = []
        for expected in case_rubric["subproblems"]:
            actual = response_subproblems.get(expected["id"])
            if actual is None:
                component_scores = {key: 0.0 for key in DEFAULT_WEIGHTS}
            else:
                component_scores = {
                    "routing": f1_route_score(
                        actual["task_families"],
                        expected["required_task_families"],
                        expected.get(
                            "accepted_task_families",
                            expected["required_task_families"],
                        ),
                    ),
                    "baseline": float(
                        bool(
                            set(actual["baseline_families"])
                            & set(expected["accepted_baseline_families"])
                        )
                    ),
                    "validation": recall_score(
                        actual["validation_safeguards"],
                        expected["required_validation_safeguards"],
                    ),
                    "data_risks": recall_score(
                        actual["data_risks"], expected["required_data_risks"]
                    ),
                }
            score = sum(component_scores[key] * weights[key] for key in weights)
            subproblem_results.append(
                {
                    "subproblem_id": expected["id"],
                    "score": score,
                    "components": component_scores,
                    "present": actual is not None,
                }
            )
        case_score = sum(item["score"] for item in subproblem_results) / len(
            subproblem_results
        )
        case_results.append(
            {"case_id": case_id, "score": case_score, "subproblems": subproblem_results}
        )
    overall = sum(case["score"] for case in case_results) / len(case_results)
    return {"run_id": response["run_id"], "score": overall, "cases": case_results}


def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set, right_set = set(left), set(right)
    if not left_set and not right_set:
        return 1.0
    return len(left_set & right_set) / len(left_set | right_set)


def response_subproblem_map(frozen: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for case in frozen["response"]["cases"]:
        for subproblem in case["subproblems"]:
            result[(case["case_id"], subproblem["id"])] = subproblem
    return result


def stability_report(frozen_runs: list[dict[str, Any]]) -> dict[str, Any]:
    if len(frozen_runs) < 2:
        return {"run_pairs": 0, "overall": None, "fields": {field: None for field in STABILITY_FIELDS}}
    maps = [response_subproblem_map(run) for run in frozen_runs]
    field_values: dict[str, list[float]] = {field: [] for field in STABILITY_FIELDS}
    pair_results: list[dict[str, Any]] = []
    for (left_index, left), (right_index, right) in combinations(enumerate(maps), 2):
        keys = sorted(set(left) | set(right))
        pair_fields: dict[str, float] = {}
        for field in STABILITY_FIELDS:
            scores = [
                jaccard(left.get(key, {}).get(field, []), right.get(key, {}).get(field, []))
                for key in keys
            ]
            value = sum(scores) / len(scores) if scores else 1.0
            pair_fields[field] = value
            field_values[field].append(value)
        pair_results.append(
            {
                "left_run_id": frozen_runs[left_index]["response"]["run_id"],
                "right_run_id": frozen_runs[right_index]["response"]["run_id"],
                "fields": pair_fields,
                "overall": sum(pair_fields.values()) / len(pair_fields),
            }
        )
    fields = {
        field: sum(values) / len(values) if values else None
        for field, values in field_values.items()
    }
    return {
        "run_pairs": len(pair_results),
        "overall": sum(value for value in fields.values() if value is not None) / len(fields),
        "fields": fields,
        "pairs": pair_results,
    }


def render_score_csv(report: dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "run_id",
                "case_id",
                "subproblem_id",
                "score",
                "routing",
                "baseline",
                "validation",
                "data_risks",
            ],
        )
        writer.writeheader()
        for run in report["runs"]:
            for case in run["cases"]:
                for subproblem in case["subproblems"]:
                    writer.writerow(
                        {
                            "run_id": run["run_id"],
                            "case_id": case["case_id"],
                            "subproblem_id": subproblem["subproblem_id"],
                            "score": f"{subproblem['score']:.6f}",
                            **{
                                key: f"{value:.6f}"
                                for key, value in subproblem["components"].items()
                            },
                        }
                    )


def render_score_html(report: dict[str, Any], path: Path) -> None:
    run_rows = "".join(
        f"<tr><td>{html.escape(run['run_id'])}</td><td>{run['score']:.1%}</td></tr>"
        for run in report["runs"]
    )
    stability = report["stability"]
    stability_text = (
        "not available (one run)"
        if stability["overall"] is None
        else f"{stability['overall']:.1%} across {stability['run_pairs']} run pairs"
    )
    detail_rows: list[str] = []
    for run in report["runs"]:
        for case in run["cases"]:
            for subproblem in case["subproblems"]:
                components = subproblem["components"]
                detail_rows.append(
                    "<tr>"
                    f"<td>{html.escape(run['run_id'])}</td>"
                    f"<td>{html.escape(case['case_id'])}</td>"
                    f"<td>{html.escape(subproblem['subproblem_id'])}</td>"
                    f"<td>{subproblem['score']:.1%}</td>"
                    f"<td>{components['routing']:.1%}</td>"
                    f"<td>{components['baseline']:.1%}</td>"
                    f"<td>{components['validation']:.1%}</td>"
                    f"<td>{components['data_risks']:.1%}</td>"
                    "</tr>"
                )
    document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>Blind modeling benchmark</title>
<style>body{{font:14px/1.5 system-ui,sans-serif;max-width:1200px;margin:32px auto;padding:0 24px;color:#17202a}}
table{{border-collapse:collapse;width:100%;margin:12px 0 28px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}
th{{background:#f6f8fa}}.card{{display:inline-block;border:1px solid #d8dee4;border-radius:8px;padding:12px 18px;margin:0 10px 16px 0}}</style></head><body>
<h1>Blind modeling benchmark</h1><p>Suite: <code>{html.escape(report['suite_id'])}</code></p>
<div class="card"><strong>{report['summary']['mean_score']:.1%}</strong><br>mean score</div>
<div class="card"><strong>{html.escape(stability_text)}</strong><br>stability</div>
<h2>Runs</h2><table><thead><tr><th>Run</th><th>Score</th></tr></thead><tbody>{run_rows}</tbody></table>
<h2>Subproblem detail</h2><table><thead><tr><th>Run</th><th>Case</th><th>Subproblem</th><th>Total</th><th>Routing</th><th>Baseline</th><th>Validation</th><th>Risks</th></tr></thead><tbody>{''.join(detail_rows)}</tbody></table>
<p>Scores measure agreement with an isolated rubric. Stability measures pairwise Jaccard agreement across independent frozen runs; high stability alone does not imply correctness.</p>
</body></html>"""
    path.write_text(document, encoding="utf-8")


def score_benchmark(
    rubric_path: Path, frozen_paths: list[Path], output_dir: Path
) -> dict[str, Any]:
    rubric = validate_rubric(load_json(rubric_path))
    frozen_runs = [validate_frozen(load_json(path)) for path in frozen_paths]
    run_ids = [run["response"]["run_id"] for run in frozen_runs]
    if len(run_ids) != len(set(run_ids)):
        raise BenchmarkError("Frozen runs must have unique run_id values")
    if any(run["suite_id"] != rubric["suite_id"] for run in frozen_runs):
        raise BenchmarkError("Every frozen run must match the rubric suite_id")
    scored_runs = [score_run(run, rubric) for run in frozen_runs]
    stability = stability_report(frozen_runs)
    report = {
        "schema_version": "1.0",
        "suite_id": rubric["suite_id"],
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "rubric_sha256": sha256_file(rubric_path),
        "summary": {
            "runs": len(scored_runs),
            "mean_score": sum(run["score"] for run in scored_runs) / len(scored_runs),
            "min_score": min(run["score"] for run in scored_runs),
            "max_score": max(run["score"] for run in scored_runs),
        },
        "stability": stability,
        "runs": scored_runs,
    }
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": output_dir / "blind-benchmark-report.json",
        "csv": output_dir / "blind-benchmark-scores.csv",
        "html": output_dir / "blind-benchmark-report.html",
    }
    report["outputs"] = {key: str(value) for key, value in paths.items()}
    write_json(paths["json"], report)
    render_score_csv(report, paths["csv"])
    render_score_html(report, paths["html"])
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, freeze, and score blind mathematical-modeling benchmarks."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Download declared non-solution materials.")
    prepare.add_argument("--suite", type=Path, required=True)
    prepare.add_argument("--out-dir", type=Path, required=True)
    prepare.add_argument("--case", action="append", dest="case_ids")

    freeze = subparsers.add_parser("freeze", help="Validate and freeze one blind response.")
    freeze.add_argument("--suite", type=Path, required=True)
    freeze.add_argument("--response", type=Path, required=True)
    freeze.add_argument("--out", type=Path, required=True)

    score = subparsers.add_parser("score", help="Score frozen responses with an isolated rubric.")
    score.add_argument("--rubric", type=Path, required=True)
    score.add_argument("--frozen", nargs="+", type=Path, required=True)
    score.add_argument("--out-dir", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.command == "prepare":
            result = prepare_suite(args.suite, args.out_dir, args.case_ids)
            print(
                f"Prepared {len(result['cases'])} cases in {Path(args.out_dir).resolve()}"
            )
        elif args.command == "freeze":
            result = freeze_response(args.suite, args.response, args.out)
            print(
                f"Frozen run {result['run_id']} with payload SHA-256 "
                f"{result['frozen_payload_sha256']}"
            )
        else:
            result = score_benchmark(args.rubric, args.frozen, args.out_dir)
            stability = result["stability"]["overall"]
            stability_text = "n/a" if stability is None else f"{stability:.1%}"
            print(
                f"Blind benchmark: {result['summary']['mean_score']:.1%} mean score | "
                f"{stability_text} stability | {result['summary']['runs']} runs"
            )
            for kind, path in result["outputs"].items():
                print(f"{kind}: {path}")
    except BenchmarkError as exc:
        raise SystemExit(f"Benchmark contract failed: {exc}") from exc


if __name__ == "__main__":
    main()
