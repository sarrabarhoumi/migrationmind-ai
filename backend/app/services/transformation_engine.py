from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any

import pandas as pd
from dateutil import parser as date_parser


TRUE_VALUES = {"1", "true", "yes", "oui", "y", "on", "active", "actif"}
FALSE_VALUES = {"0", "false", "no", "non", "n", "off", "inactive", "inactif"}


def is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or str(value).strip() == ""


def transform_value(value: Any, strategy: str, default: Any = None) -> Any:
    if strategy == "default":
        return default
    if is_empty(value):
        return default

    text = str(value).strip()

    if strategy in {"direct", "trim"}:
        return text
    if strategy == "lowercase":
        return text.lower()
    if strategy == "uppercase":
        return text.upper()
    if strategy == "split_first":
        return text.split()[0] if text.split() else default
    if strategy == "split_last":
        parts = text.split()
        return " ".join(parts[1:]) if len(parts) > 1 else default
    if strategy == "normalize_phone":
        prefix = "+" if text.startswith("+") else ""
        digits = re.sub(r"\D", "", text)
        return prefix + digits
    if strategy == "parse_date":
        iso_first = bool(re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", text))
        parsed = date_parser.parse(text, dayfirst=not iso_first, yearfirst=iso_first, fuzzy=False)
        return parsed.date().isoformat()
    if strategy == "parse_datetime":
        iso_first = bool(re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", text))
        parsed = date_parser.parse(text, dayfirst=not iso_first, yearfirst=iso_first, fuzzy=False)
        return parsed.replace(microsecond=0).isoformat(sep=" ")
    if strategy == "to_int":
        return int(float(text.replace(" ", "").replace(",", ".")))
    if strategy == "to_float":
        return float(text.replace(" ", "").replace(",", "."))
    if strategy == "to_boolean":
        normalized = text.lower()
        if normalized in TRUE_VALUES:
            return True
        if normalized in FALSE_VALUES:
            return False
        raise ValueError(f"Valeur booléenne invalide: {text}")

    raise ValueError(f"Transformation non supportée: {strategy}")


def transform_dataframe(
    dataframe: pd.DataFrame,
    target_schema: dict,
    mappings: list[dict],
) -> tuple[pd.DataFrame, list[dict]]:
    errors: list[dict] = []
    output_rows: list[dict] = []
    mapping_by_target = {item["target_field"]: item for item in mappings}

    for row_index, row in dataframe.iterrows():
        output: dict[str, Any] = {}
        for field in target_schema.get("fields", []):
            target_name = field["name"]
            mapping = mapping_by_target.get(target_name, {})
            source_name = mapping.get("source_field")
            strategy = mapping.get("transformation", "direct")
            raw_value = row.get(source_name) if source_name in dataframe.columns else None

            try:
                output[target_name] = transform_value(raw_value, strategy, field.get("default"))
            except Exception as exc:
                output[target_name] = field.get("default")
                errors.append(
                    {
                        "row": int(row_index) + 2,
                        "field": target_name,
                        "source_field": source_name,
                        "value": None if is_empty(raw_value) else str(raw_value),
                        "code": "TRANSFORMATION_ERROR",
                        "message": str(exc),
                    }
                )
        output_rows.append(output)

    return pd.DataFrame(output_rows), errors
