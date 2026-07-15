#!/usr/bin/env python3
"""Audit tabular modeling data and emit JSON, CSV, and HTML reports."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:  # pragma: no cover - exercised by CLI environments
    raise SystemExit(
        "audit_dataset.py requires pandas and numpy. Install them with "
        "'python -m pip install pandas numpy'. Excel and MAT support may also "
        "require openpyxl, xlrd, and scipy."
    ) from exc


SUPPORTED_SUFFIXES = {".csv", ".tsv", ".txt", ".dat", ".xlsx", ".xls", ".mat"}
SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2}
UNIT_PATTERN = re.compile(
    r"^\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?\s*"
    r"([A-Za-z%°℃℉μµΩ/·^-]+)\s*$"
)
HEADER_UNIT_PATTERN = re.compile(r"(?:\[([^\]]+)\]|\(([^)]+)\)|（([^）]+)）)\s*$")
IDENTIFIER_HINTS = ("编号", "序号", "代码", "编码", "流水号", "uuid")
TIME_HINTS = ("time", "date", "year", "month", "day", "时间", "日期", "年月", "年份")


@dataclass
class LoadedTable:
    source: Path
    name: str
    frame: pd.DataFrame

    @property
    def table_id(self) -> str:
        return f"{self.source.name}::{self.name}"


def add_issue(
    issues: list[dict[str, Any]],
    severity: str,
    code: str,
    scope: str,
    message: str,
    recommendation: str,
    evidence: dict[str, Any] | None = None,
) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "scope": scope,
            "message": message,
            "recommendation": recommendation,
            "evidence": evidence or {},
        }
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_value(value: Any) -> Any:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return value


def safe_cell(value: Any) -> Any:
    """Convert MATLAB object cells and other unhashable values to audit-safe text."""
    if isinstance(value, (list, tuple, dict, set, np.ndarray)):
        return repr(value)
    return value


def read_delimited(path: Path, header: int | None) -> pd.DataFrame:
    errors: list[str] = []
    separators: list[str | None]
    if path.suffix.lower() == ".tsv":
        separators = ["\t"]
    else:
        separators = [None, ",", "\t", ";"]
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin1"):
        for separator in separators:
            try:
                return pd.read_csv(
                    path,
                    sep=separator,
                    engine="python",
                    encoding=encoding,
                    header=header,
                )
            except Exception as exc:  # parsers expose several exception classes
                errors.append(f"{encoding}/{separator!r}: {exc}")
    raise ValueError("unable to parse delimited text; " + " | ".join(errors[-4:]))


def read_mat(path: Path) -> tuple[list[LoadedTable], list[dict[str, Any]]]:
    try:
        from scipy.io import loadmat
    except ImportError as exc:
        raise ValueError(
            "MAT support requires scipy; install it with 'python -m pip install scipy'"
        ) from exc

    raw = loadmat(path)
    tables: list[LoadedTable] = []
    notices: list[dict[str, Any]] = []
    for name, value in raw.items():
        if name.startswith("__"):
            continue
        array = np.asarray(value)
        if array.ndim == 0:
            frame = pd.DataFrame({name: [safe_cell(array.item())]})
        elif array.ndim == 1:
            frame = pd.DataFrame({name: [safe_cell(item) for item in array]})
        elif array.ndim == 2:
            if array.dtype.names:
                notices.append(
                    {
                        "severity": "warning",
                        "code": "unsupported_mat_struct",
                        "scope": f"{path.name}::{name}",
                        "message": "MATLAB struct arrays are not flattened automatically.",
                        "recommendation": "Export this variable as a MATLAB table or numeric matrix before auditing.",
                        "evidence": {"shape": list(array.shape)},
                    }
                )
                continue
            columns = [f"{name}_{index + 1}" for index in range(array.shape[1])]
            frame = pd.DataFrame(array, columns=columns)
            if frame.dtypes.eq("object").any():
                frame = frame.map(safe_cell) if hasattr(frame, "map") else frame.applymap(safe_cell)
        else:
            notices.append(
                {
                    "severity": "warning",
                    "code": "unsupported_mat_dimension",
                    "scope": f"{path.name}::{name}",
                    "message": f"A {array.ndim}-D MATLAB array cannot be audited as a table without a declared axis contract.",
                    "recommendation": "Select or reshape the observation and feature axes explicitly, then rerun the audit.",
                    "evidence": {"shape": list(array.shape)},
                }
            )
            continue
        tables.append(LoadedTable(path, name, frame))
    return tables, notices


def load_tables(
    paths: Iterable[Path], header: int | None, sheets: list[str] | None
) -> tuple[list[LoadedTable], list[dict[str, Any]], list[dict[str, Any]]]:
    tables: list[LoadedTable] = []
    issues: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for input_path in paths:
        path = input_path.expanduser().resolve()
        if not path.is_file():
            add_issue(
                issues,
                "error",
                "input_missing",
                str(path),
                "Input file does not exist.",
                "Correct the path or restore the immutable raw input.",
            )
            continue
        suffix = path.suffix.lower()
        sources.append(
            {
                "path": str(path),
                "name": path.name,
                "suffix": suffix,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
        if suffix not in SUPPORTED_SUFFIXES:
            add_issue(
                issues,
                "error",
                "unsupported_format",
                path.name,
                f"Unsupported input format: {suffix or '<none>'}.",
                f"Use one of: {', '.join(sorted(SUPPORTED_SUFFIXES))}.",
            )
            continue
        try:
            if suffix in {".csv", ".tsv", ".txt", ".dat"}:
                tables.append(LoadedTable(path, "data", read_delimited(path, header)))
            elif suffix in {".xlsx", ".xls"}:
                sheet_arg: Any = sheets if sheets else None
                workbooks = pd.read_excel(path, sheet_name=sheet_arg, header=header)
                if isinstance(workbooks, pd.DataFrame):
                    workbooks = {(sheets or ["data"])[0]: workbooks}
                for sheet_name, frame in workbooks.items():
                    tables.append(LoadedTable(path, str(sheet_name), frame))
            else:
                mat_tables, mat_notices = read_mat(path)
                tables.extend(mat_tables)
                issues.extend(mat_notices)
        except Exception as exc:
            hint = "Check that the file is valid and not password-protected."
            if suffix == ".xlsx":
                hint += " Install openpyxl if the Excel engine is missing."
            elif suffix == ".xls":
                hint += " Install xlrd if the legacy Excel engine is missing."
            add_issue(
                issues,
                "error",
                "input_parse_failed",
                path.name,
                f"Could not parse input: {exc}",
                hint,
            )
    return tables, issues, sources


def normalized_name(value: Any) -> str:
    return str(value).strip().casefold()


def has_identifier_hint(name: str) -> bool:
    return bool(re.search(r"(?:^|[_\s-])id(?:$|[_\s-])", name)) or any(
        hint in name for hint in IDENTIFIER_HINTS
    )


def resolve_column(frame: pd.DataFrame, requested: str | None) -> Any | None:
    if not requested:
        return None
    wanted = requested.strip().casefold()
    for column in frame.columns:
        if normalized_name(column) == wanted:
            return column
    return None


def header_unit(column: Any) -> str | None:
    match = HEADER_UNIT_PATTERN.search(str(column).strip())
    if not match:
        return None
    candidate = next((part for part in match.groups() if part), "").strip()
    return candidate if 0 < len(candidate) <= 20 else None


def infer_semantic_type(series: pd.Series, column: Any) -> str:
    nonnull = series.dropna()
    if nonnull.empty:
        return "empty"
    if nonnull.nunique(dropna=True) == 1:
        return "constant"
    name = normalized_name(column)
    unique_rate = float(nonnull.nunique(dropna=True) / len(nonnull))
    if pd.api.types.is_bool_dtype(nonnull):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(nonnull):
        return "datetime"
    if np.iscomplexobj(nonnull.to_numpy()):
        return "complex_numeric"
    if has_identifier_hint(name) and unique_rate >= 0.8:
        return "identifier"
    numeric = pd.to_numeric(nonnull, errors="coerce")
    if float(numeric.notna().mean()) >= 0.95:
        return "numeric"
    if any(hint in name for hint in TIME_HINTS):
        parsed = pd.to_datetime(nonnull, errors="coerce")
        if float(parsed.notna().mean()) >= 0.8:
            return "datetime"
    unique = int(nonnull.nunique(dropna=True))
    if unique <= max(20, int(len(nonnull) * 0.05)):
        return "categorical"
    if unique_rate >= 0.98 and nonnull.astype(str).str.len().median() <= 64:
        return "identifier"
    return "text"


def summarize_column(series: pd.Series, column: Any) -> dict[str, Any]:
    total = len(series)
    nonnull = series.dropna()
    semantic_type = infer_semantic_type(series, column)
    unique_count = int(nonnull.nunique(dropna=True)) if len(nonnull) else 0
    result: dict[str, Any] = {
        "column": str(column),
        "dtype": str(series.dtype),
        "semantic_type": semantic_type,
        "rows": total,
        "non_null_count": int(series.notna().sum()),
        "missing_count": int(series.isna().sum()),
        "missing_rate": float(series.isna().mean()) if total else 0.0,
        "unique_count": unique_count,
        "unique_rate": float(unique_count / len(nonnull)) if len(nonnull) else 0.0,
        "declared_unit": header_unit(column),
        "observed_units": [],
        "numeric": None,
        "top_values": [],
        "flags": [],
    }
    if semantic_type in {"numeric", "complex_numeric", "constant"}:
        converted = pd.to_numeric(series, errors="coerce")
        is_complex = np.iscomplexobj(converted.to_numpy())
        if is_complex:
            array = converted.to_numpy(dtype=complex)
            finite_mask = np.isfinite(array.real) & np.isfinite(array.imag)
            valid = pd.Series(np.abs(array[finite_mask]), dtype="float64")
            non_finite_count = int((~finite_mask).sum())
        else:
            numeric = converted.replace([np.inf, -np.inf], np.nan)
            valid = numeric.dropna().astype("float64")
            non_finite_count = int(converted.isin([np.inf, -np.inf]).sum())
        if len(valid):
            q1, median, q3 = valid.quantile([0.25, 0.5, 0.75]).tolist()
            iqr = q3 - q1
            if iqr > 0:
                outlier_mask = (valid < q1 - 1.5 * iqr) | (valid > q3 + 1.5 * iqr)
                extreme_mask = (valid < q1 - 3.0 * iqr) | (valid > q3 + 3.0 * iqr)
            else:
                outlier_mask = pd.Series(False, index=valid.index)
                extreme_mask = pd.Series(False, index=valid.index)
            skew = float(valid.skew()) if len(valid) >= 3 else None
            result["numeric"] = {
                "basis": "magnitude" if is_complex else "value",
                "count": int(len(valid)),
                "min": json_value(valid.min()),
                "q1": json_value(q1),
                "median": json_value(median),
                "q3": json_value(q3),
                "max": json_value(valid.max()),
                "mean": json_value(valid.mean()),
                "std": json_value(valid.std()),
                "skew": json_value(skew),
                "outlier_count_iqr": int(outlier_mask.sum()),
                "outlier_rate_iqr": float(outlier_mask.mean()),
                "extreme_count_3iqr": int(extreme_mask.sum()),
                "non_finite_count": non_finite_count,
            }
            if is_complex:
                finite_values = array[finite_mask]
                result["numeric"].update(
                    {
                        "real_min": json_value(finite_values.real.min()),
                        "real_max": json_value(finite_values.real.max()),
                        "imag_min": json_value(finite_values.imag.min()),
                        "imag_max": json_value(finite_values.imag.max()),
                    }
                )
    else:
        counts = nonnull.astype(str).value_counts(dropna=True).head(10)
        result["top_values"] = [
            {"value": str(value), "count": int(count)} for value, count in counts.items()
        ]
        observed_units = sorted(
            {
                match.group(1)
                for value in nonnull.astype(str).head(10000)
                if (match := UNIT_PATTERN.match(value))
            }
        )
        result["observed_units"] = observed_units
    return result


def add_column_issues(
    issues: list[dict[str, Any]], table_id: str, summary: dict[str, Any]
) -> None:
    scope = f"{table_id}::{summary['column']}"
    missing_rate = summary["missing_rate"]
    if missing_rate >= 0.5:
        summary["flags"].append("high_missingness")
        add_issue(
            issues,
            "warning",
            "high_missingness",
            scope,
            f"Missing rate is {missing_rate:.1%}.",
            "Verify the collection mechanism; drop, impute, or model missingness using training data only.",
            {"missing_rate": missing_rate},
        )
    if summary["semantic_type"] == "constant" and summary["rows"] >= 2:
        summary["flags"].append("constant_column")
        add_issue(
            issues,
            "warning",
            "constant_column",
            scope,
            "The field is constant and carries no variation for estimation.",
            "Remove it from model features unless it has contractual or unit meaning.",
        )
    if len(summary["observed_units"]) > 1:
        summary["flags"].append("mixed_units")
        add_issue(
            issues,
            "warning",
            "mixed_units",
            scope,
            f"Values contain multiple unit suffixes: {', '.join(summary['observed_units'])}.",
            "Convert to one declared unit before numerical parsing and retain the conversion rule.",
            {"observed_units": summary["observed_units"]},
        )
    numeric = summary.get("numeric") or {}
    outlier_count = numeric.get("outlier_count_iqr", 0)
    outlier_rate = numeric.get("outlier_rate_iqr", 0.0)
    if outlier_count >= 3 and outlier_rate >= 0.01:
        summary["flags"].append("iqr_outliers")
        add_issue(
            issues,
            "warning",
            "iqr_outliers",
            scope,
            f"Detected {outlier_count} IQR outliers ({outlier_rate:.1%}).",
            "Inspect their provenance and use robust or domain-specific limits; do not delete them automatically.",
            {"count": outlier_count, "rate": outlier_rate},
        )
    skew = numeric.get("skew")
    if skew is not None and abs(skew) >= 2:
        summary["flags"].append("extreme_skew")
        add_issue(
            issues,
            "info",
            "extreme_skew",
            scope,
            f"Absolute skewness is high ({skew:.2f}).",
            "Consider a robust scale, transformation, or distribution-aware model and report the choice.",
            {"skew": skew},
        )
    if numeric.get("non_finite_count", 0):
        summary["flags"].append("non_finite")
        add_issue(
            issues,
            "error",
            "non_finite_numeric",
            scope,
            f"Found {numeric['non_finite_count']} infinite numeric values.",
            "Trace the generating calculation and replace infinities only with a documented rule.",
        )


def exact_match_rate(left: pd.Series, right: pd.Series) -> float:
    valid = left.notna() & right.notna()
    if not valid.any():
        return 0.0
    return float(
        (left[valid].astype(str).str.strip() == right[valid].astype(str).str.strip()).mean()
    )


def audit_target(
    frame: pd.DataFrame,
    table_id: str,
    target: Any,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    series = frame[target]
    nonnull = series.dropna()
    result: dict[str, Any] = {"column": str(target), "class_distribution": []}
    unique_count = int(nonnull.nunique(dropna=True)) if len(nonnull) else 0
    classification_like = (
        not pd.api.types.is_numeric_dtype(nonnull)
        or unique_count <= max(20, int(max(len(nonnull), 1) * 0.05))
    )
    if classification_like and len(nonnull):
        counts = nonnull.astype(str).value_counts()
        result["class_distribution"] = [
            {"value": str(value), "count": int(count), "rate": float(count / len(nonnull))}
            for value, count in counts.items()
        ]
        dominant_rate = float(counts.iloc[0] / len(nonnull))
        result["dominant_class_rate"] = dominant_rate
        if unique_count > 1 and dominant_rate >= 0.8:
            add_issue(
                issues,
                "warning",
                "target_imbalance",
                f"{table_id}::{target}",
                f"The largest target class contains {dominant_rate:.1%} of labeled rows.",
                "Use stratified or group-aware validation and report per-class metrics, not accuracy alone.",
                {"dominant_class_rate": dominant_rate, "classes": unique_count},
            )
    for feature in frame.columns:
        if feature == target:
            continue
        match_rate = exact_match_rate(frame[feature], series)
        if match_rate >= 0.999:
            add_issue(
                issues,
                "error",
                "target_copy_leakage",
                f"{table_id}::{feature}",
                f"Feature matches target on {match_rate:.1%} of comparable rows.",
                "Remove the feature or prove that it is available before the prediction decision.",
                {"target": str(target), "match_rate": match_rate},
            )
            continue
        feature_numeric = pd.to_numeric(frame[feature], errors="coerce")
        target_numeric = pd.to_numeric(series, errors="coerce")
        if np.iscomplexobj(feature_numeric.to_numpy()) or np.iscomplexobj(target_numeric.to_numpy()):
            continue
        valid = feature_numeric.notna() & target_numeric.notna()
        if valid.sum() >= 10 and feature_numeric[valid].nunique() > 1 and target_numeric[valid].nunique() > 1:
            correlation = float(feature_numeric[valid].corr(target_numeric[valid]))
            if math.isfinite(correlation) and abs(correlation) >= 0.995:
                add_issue(
                    issues,
                    "warning",
                    "near_perfect_target_correlation",
                    f"{table_id}::{feature}",
                    f"Feature-target correlation is {correlation:.4f}.",
                    "Check whether the feature is target-derived, post-event, or a legitimate physical identity.",
                    {"target": str(target), "correlation": correlation},
                )
    return result


def split_labels(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    labels = series.astype(str).str.strip().str.casefold()
    train = labels.str.contains(r"train|训练", regex=True, na=False)
    evaluation = labels.str.contains(r"val|valid|test|验证|测试", regex=True, na=False)
    return train, evaluation


def audit_time(
    frame: pd.DataFrame,
    table_id: str,
    time_column: Any,
    split_column: Any | None,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    parsed = pd.to_datetime(frame[time_column], errors="coerce", utc=True)
    valid = parsed.dropna()
    result = {
        "column": str(time_column),
        "parse_rate": float(parsed.notna().mean()) if len(parsed) else 0.0,
        "monotonic_increasing": bool(valid.is_monotonic_increasing),
        "duplicate_timestamp_count": int(valid.duplicated().sum()),
        "min": json_value(valid.min()) if len(valid) else None,
        "max": json_value(valid.max()) if len(valid) else None,
    }
    if result["parse_rate"] < 0.8:
        add_issue(
            issues,
            "error",
            "time_parse_failure",
            f"{table_id}::{time_column}",
            f"Only {result['parse_rate']:.1%} of time values could be parsed.",
            "Declare one time format and time zone, then normalize the field before splitting.",
        )
        return result
    if not result["monotonic_increasing"]:
        add_issue(
            issues,
            "warning",
            "time_not_ordered",
            f"{table_id}::{time_column}",
            "Rows are not in chronological order.",
            "Sort by time before lag generation and use rolling or forward-chaining validation.",
        )
    now = pd.Timestamp.now(tz="UTC")
    future_count = int((valid > now).sum())
    result["future_timestamp_count"] = future_count
    if future_count:
        add_issue(
            issues,
            "info",
            "future_timestamps",
            f"{table_id}::{time_column}",
            f"Found {future_count} timestamps later than the audit time.",
            "Confirm that these are planned horizons rather than clock, parsing, or provenance errors.",
            {"count": future_count},
        )
    if split_column is not None:
        train_mask, eval_mask = split_labels(frame[split_column])
        train_times = parsed[train_mask].dropna()
        eval_times = parsed[eval_mask].dropna()
        if len(train_times) and len(eval_times) and train_times.max() >= eval_times.min():
            add_issue(
                issues,
                "error",
                "temporal_split_overlap",
                f"{table_id}::{split_column}",
                "Training time reaches or passes the earliest validation/test time.",
                "Rebuild the split so every evaluation observation occurs after its training window.",
                {
                    "train_max": json_value(train_times.max()),
                    "evaluation_min": json_value(eval_times.min()),
                },
            )
    return result


def audit_group_split(
    frame: pd.DataFrame,
    table_id: str,
    group_column: Any,
    split_column: Any,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    subset = frame[[group_column, split_column]].dropna()
    split_counts = subset.groupby(group_column, dropna=False)[split_column].nunique()
    overlap = split_counts[split_counts > 1]
    result = {
        "group_column": str(group_column),
        "split_column": str(split_column),
        "group_count": int(split_counts.size),
        "groups_in_multiple_splits": int(overlap.size),
        "sample_overlapping_groups": [str(value) for value in overlap.index[:20]],
    }
    if len(overlap):
        add_issue(
            issues,
            "error",
            "group_split_leakage",
            f"{table_id}::{group_column}",
            f"{len(overlap)} groups occur in more than one split.",
            "Assign every entity/group to exactly one split or use a declared grouped time design.",
            {"groups_in_multiple_splits": int(overlap.size)},
        )
    return result


def recommend_split(
    rows: int,
    target_summary: dict[str, Any] | None,
    time_column: Any | None,
    group_column: Any | None,
) -> dict[str, str]:
    if rows < 2:
        return {
            "strategy": "reshape or obtain more observations before splitting",
            "reason": "A one-row table cannot support train/validation estimation.",
        }
    if time_column is not None and group_column is not None:
        return {
            "strategy": "group-aware rolling validation",
            "reason": "Both temporal order and repeated entities must be isolated.",
        }
    if time_column is not None:
        return {
            "strategy": "rolling-origin or forward-chaining validation",
            "reason": "Random splits would train on observations later than validation rows.",
        }
    if group_column is not None:
        return {
            "strategy": "GroupKFold or grouped holdout",
            "reason": "The same entity must not appear in training and validation.",
        }
    if target_summary and target_summary.get("dominant_class_rate", 0) >= 0.8:
        return {
            "strategy": "stratified repeated cross-validation",
            "reason": "Class imbalance requires stable class proportions and per-class metrics.",
        }
    if rows < 200:
        return {
            "strategy": "repeated K-fold cross-validation",
            "reason": "The sample is small enough that one holdout estimate may be unstable.",
        }
    return {
        "strategy": "fixed holdout plus K-fold validation on training data",
        "reason": "This preserves a final untouched test set while estimating model-selection variance.",
    }


def audit_table(
    table: LoadedTable,
    target_name: str | None,
    time_name: str | None,
    group_name: str | None,
    split_name: str | None,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    frame = table.frame.copy()
    frame.columns = [str(column).strip() or f"unnamed_{index + 1}" for index, column in enumerate(frame.columns)]
    rows, columns = frame.shape
    if rows == 0 or columns == 0:
        add_issue(
            issues,
            "error",
            "empty_table",
            table.table_id,
            f"Table has shape {rows} x {columns}.",
            "Verify the sheet, variable, delimiter, and header selection.",
        )
    elif rows < 2:
        add_issue(
            issues,
            "warning",
            "insufficient_observations",
            table.table_id,
            "The parsed table contains only one observation.",
            "Check whether variables are arranged across columns and should be transposed, or obtain more observations.",
            {"rows": rows, "columns": columns},
        )
    if rows >= 2 and columns >= rows:
        add_issue(
            issues,
            "warning",
            "high_dimensional_table",
            table.table_id,
            f"Feature count ({columns}) is at least the observation count ({rows}).",
            "Use leakage-safe feature screening, regularization or dimension reduction fitted inside each training fold.",
            {"rows": rows, "columns": columns, "column_to_row_ratio": columns / rows},
        )
    try:
        duplicate_count = int(frame.duplicated().sum())
    except TypeError:
        duplicate_count = int(frame.astype(str).duplicated().sum())
    if duplicate_count:
        add_issue(
            issues,
            "warning",
            "duplicate_rows",
            table.table_id,
            f"Found {duplicate_count} fully duplicated rows ({duplicate_count / max(rows, 1):.1%}).",
            "Confirm whether repeats are valid measurements; otherwise deduplicate by a documented key.",
            {"count": duplicate_count, "rate": duplicate_count / max(rows, 1)},
        )

    column_summaries = [summarize_column(frame[column], column) for column in frame.columns]
    for summary in column_summaries:
        add_column_issues(issues, table.table_id, summary)
    complex_fields = [
        summary["column"]
        for summary in column_summaries
        if summary["semantic_type"] == "complex_numeric"
    ]
    if complex_fields:
        add_issue(
            issues,
            "info",
            "complex_numeric_fields",
            table.table_id,
            f"Found {len(complex_fields)} complex-valued fields; distribution statistics use magnitude.",
            "Declare whether the model uses real/imaginary parts, magnitude/phase, or another representation.",
            {"count": len(complex_fields), "sample_fields": complex_fields[:20]},
        )

    requested = {
        "target": (target_name, resolve_column(frame, target_name)),
        "time": (time_name, resolve_column(frame, time_name)),
        "group": (group_name, resolve_column(frame, group_name)),
        "split": (split_name, resolve_column(frame, split_name)),
    }
    for role, (name, resolved) in requested.items():
        if name and resolved is None:
            add_issue(
                issues,
                "warning",
                "declared_column_missing",
                table.table_id,
                f"Declared {role} column '{name}' is not present in this table.",
                "Check the field name or audit this sheet/variable with a separate contract.",
            )

    target_column = requested["target"][1]
    time_column = requested["time"][1]
    group_column = requested["group"][1]
    split_column = requested["split"][1]
    target_summary = (
        audit_target(frame, table.table_id, target_column, issues)
        if target_column is not None
        else None
    )
    time_summary = (
        audit_time(frame, table.table_id, time_column, split_column, issues)
        if time_column is not None
        else None
    )
    group_split_summary = (
        audit_group_split(frame, table.table_id, group_column, split_column, issues)
        if group_column is not None and split_column is not None
        else None
    )
    return {
        "table_id": table.table_id,
        "source_path": str(table.source),
        "table_name": table.name,
        "rows": rows,
        "columns": columns,
        "duplicate_row_count": duplicate_count,
        "duplicate_row_rate": duplicate_count / max(rows, 1),
        "fields": column_summaries,
        "target_audit": target_summary,
        "time_audit": time_summary,
        "group_split_audit": group_split_summary,
        "split_recommendation": recommend_split(rows, target_summary, time_column, group_column),
    }


def render_csv(report: dict[str, Any], path: Path) -> None:
    fields = [
        "table_id",
        "source_path",
        "column",
        "dtype",
        "semantic_type",
        "rows",
        "missing_count",
        "missing_rate",
        "unique_count",
        "unique_rate",
        "declared_unit",
        "observed_units",
        "outlier_rate_iqr",
        "skew",
        "flags",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for table in report["tables"]:
            for field in table["fields"]:
                numeric = field.get("numeric") or {}
                writer.writerow(
                    {
                        "table_id": table["table_id"],
                        "source_path": table["source_path"],
                        "column": field["column"],
                        "dtype": field["dtype"],
                        "semantic_type": field["semantic_type"],
                        "rows": field["rows"],
                        "missing_count": field["missing_count"],
                        "missing_rate": f"{field['missing_rate']:.6f}",
                        "unique_count": field["unique_count"],
                        "unique_rate": f"{field['unique_rate']:.6f}",
                        "declared_unit": field["declared_unit"] or "",
                        "observed_units": "|".join(field["observed_units"]),
                        "outlier_rate_iqr": numeric.get("outlier_rate_iqr", ""),
                        "skew": numeric.get("skew", ""),
                        "flags": "|".join(field["flags"]),
                    }
                )


def render_html(report: dict[str, Any], path: Path) -> None:
    counts = report["summary"]["issue_counts"]
    issue_rows = "".join(
        "<tr>"
        f"<td><span class='sev {html.escape(issue['severity'])}'>{html.escape(issue['severity'])}</span></td>"
        f"<td>{html.escape(issue['code'])}</td>"
        f"<td>{html.escape(issue['scope'])}</td>"
        f"<td>{html.escape(issue['message'])}</td>"
        f"<td>{html.escape(issue['recommendation'])}</td>"
        "</tr>"
        for issue in report["issues"]
    ) or "<tr><td colspan='5'>No issues detected.</td></tr>"
    table_sections: list[str] = []
    for table in report["tables"]:
        field_rows = "".join(
            "<tr>"
            f"<td>{html.escape(field['column'])}</td>"
            f"<td>{html.escape(field['semantic_type'])}</td>"
            f"<td>{field['missing_rate']:.1%}</td>"
            f"<td>{field['unique_count']}</td>"
            f"<td>{html.escape(field['declared_unit'] or '')}</td>"
            f"<td>{html.escape(', '.join(field['flags']))}</td>"
            "</tr>"
            for field in table["fields"]
        )
        recommendation = table["split_recommendation"]
        table_sections.append(
            f"<h2>{html.escape(table['table_id'])}</h2>"
            f"<p>{table['rows']:,} rows × {table['columns']:,} columns; "
            f"{table['duplicate_row_count']:,} duplicate rows.</p>"
            f"<p><strong>Suggested validation:</strong> {html.escape(recommendation['strategy'])} — "
            f"{html.escape(recommendation['reason'])}</p>"
            "<table><thead><tr><th>Field</th><th>Type</th><th>Missing</th>"
            "<th>Unique</th><th>Unit</th><th>Flags</th></tr></thead>"
            f"<tbody>{field_rows}</tbody></table>"
        )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Dataset audit</title><style>
body{{font:14px/1.5 system-ui,sans-serif;max-width:1440px;margin:32px auto;padding:0 24px;color:#17202a}}
h1,h2{{line-height:1.2}} .cards{{display:flex;gap:12px;flex-wrap:wrap}}
.card{{border:1px solid #d8dee4;border-radius:8px;padding:12px 18px;background:#f6f8fa}}
table{{border-collapse:collapse;width:100%;margin:12px 0 28px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}
th{{background:#f6f8fa;position:sticky;top:0}}.sev{{font-weight:700}}.error{{color:#b42318}}.warning{{color:#9a6700}}.info{{color:#0969da}}
code{{background:#f6f8fa;padding:2px 4px;border-radius:3px}}
</style></head><body>
<h1>Dataset audit</h1><p>Generated {html.escape(report['audited_at'])}. Automated flags are screening evidence, not automatic deletion rules.</p>
<div class="cards"><div class="card"><strong>{report['summary']['files']}</strong><br>files</div>
<div class="card"><strong>{report['summary']['tables']}</strong><br>tables</div>
<div class="card"><strong>{report['summary']['rows']:,}</strong><br>rows</div>
<div class="card"><strong class="error">{counts['error']}</strong> errors<br><strong class="warning">{counts['warning']}</strong> warnings<br>{counts['info']} info</div></div>
<h2>Issues</h2><table><thead><tr><th>Severity</th><th>Code</th><th>Scope</th><th>Finding</th><th>Action</th></tr></thead><tbody>{issue_rows}</tbody></table>
{''.join(table_sections)}</body></html>
"""
    path.write_text(document, encoding="utf-8")


def audit_dataset(
    input_paths: Iterable[Path],
    output_dir: Path,
    target: str | None = None,
    time_column: str | None = None,
    group: str | None = None,
    split: str | None = None,
    sheets: list[str] | None = None,
    header: int | None = 0,
) -> dict[str, Any]:
    paths = list(input_paths)
    tables, issues, sources = load_tables(paths, header, sheets)
    table_reports = [
        audit_table(table, target, time_column, group, split, issues) for table in tables
    ]
    issues.sort(
        key=lambda item: (-SEVERITY_ORDER[item["severity"]], item["scope"], item["code"])
    )
    counts = {
        severity: sum(issue["severity"] == severity for issue in issues)
        for severity in ("error", "warning", "info")
    }
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "audit_contract": {
            "target": target,
            "time": time_column,
            "group": group,
            "split": split,
            "sheets": sheets or "all",
            "header": header,
        },
        "summary": {
            "files": len(sources),
            "tables": len(table_reports),
            "rows": sum(table["rows"] for table in table_reports),
            "columns": sum(table["columns"] for table in table_reports),
            "issue_counts": counts,
            "status": "failed" if counts["error"] else ("review" if counts["warning"] else "passed"),
        },
        "sources": sources,
        "issues": issues,
        "tables": table_reports,
        "limitations": [
            "Automated outlier, skew, unit, and leakage flags require domain review.",
            "Future-information leakage cannot be ruled out without feature availability times and a prediction-time contract.",
            "MATLAB structs and arrays above two dimensions require an explicit observation/feature axis mapping.",
        ],
    }
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "dataset-audit.json"
    csv_path = output_dir / "dataset-audit-fields.csv"
    html_path = output_dir / "dataset-audit.html"
    report["outputs"] = {
        "json": str(json_path),
        "csv": str(csv_path),
        "html": str(html_path),
    }
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    render_csv(report, csv_path)
    render_html(report, html_path)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit CSV, delimited text, Excel, or MAT datasets for modeling risks."
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="Input data files.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("audit/dataset"),
        help="Directory for dataset-audit.json, CSV, and HTML reports.",
    )
    parser.add_argument("--target", help="Target/label column, matched case-insensitively.")
    parser.add_argument("--time", dest="time_column", help="Observation time column.")
    parser.add_argument("--group", help="Entity/group column that must stay isolated.")
    parser.add_argument("--split", help="Existing train/validation/test split column.")
    parser.add_argument(
        "--sheet",
        action="append",
        dest="sheets",
        help="Excel sheet to audit; repeat for multiple sheets. Default: all sheets.",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Treat the first row as data and assign generated column numbers.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = audit_dataset(
        args.inputs,
        args.out_dir,
        target=args.target,
        time_column=args.time_column,
        group=args.group,
        split=args.split,
        sheets=args.sheets,
        header=None if args.no_header else 0,
    )
    summary = report["summary"]
    print(
        f"Dataset audit: {summary['status']} | {summary['files']} files | "
        f"{summary['tables']} tables | {summary['rows']} rows | "
        f"{summary['issue_counts']['error']} errors, "
        f"{summary['issue_counts']['warning']} warnings, "
        f"{summary['issue_counts']['info']} info"
    )
    for kind, path in report["outputs"].items():
        print(f"{kind}: {path}")


if __name__ == "__main__":
    main()
