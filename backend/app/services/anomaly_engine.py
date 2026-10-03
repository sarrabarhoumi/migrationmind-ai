from __future__ import annotations

import re
from typing import Any

import pandas as pd
from dateutil import parser as date_parser

from .transformation_engine import is_empty


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^\+?\d{6,18}$")


def _valid_type(value: Any, field_type: str) -> bool:
    if is_empty(value):
        return True
    text = str(value).strip()
    try:
        if field_type == "integer":
            int(float(text))
        elif field_type == "float":
            float(text)
        elif field_type in {"date", "datetime"}:
            date_parser.parse(text)
        elif field_type == "email":
            return bool(EMAIL_RE.match(text))
        elif field_type == "phone":
            return bool(PHONE_RE.match(text))
        elif field_type == "boolean":
            return isinstance(value, bool) or text.lower() in {"true", "false", "1", "0"}
        return True
    except (ValueError, TypeError, OverflowError):
        return False


def detect_anomalies(dataframe: pd.DataFrame, target_schema: dict) -> list[dict]:
    issues: list[dict] = []

    for field in target_schema.get("fields", []):
        name = field["name"]
        if name not in dataframe.columns:
            issues.append(
                {
                    "row": None,
                    "field": name,
                    "code": "MISSING_TARGET_COLUMN",
                    "severity": "error",
                    "message": "La colonne cible n'a pas été produite.",
                }
            )
            continue

        for row_index, value in dataframe[name].items():
            if field.get("required") and is_empty(value):
                issues.append(
                    {
                        "row": int(row_index) + 2,
                        "field": name,
                        "code": "REQUIRED_VALUE_MISSING",
                        "severity": "error",
                        "message": "Valeur obligatoire manquante.",
                    }
                )
            elif not _valid_type(value, field.get("type", "string")):
                issues.append(
                    {
                        "row": int(row_index) + 2,
                        "field": name,
                        "code": "INVALID_TYPE",
                        "severity": "error",
                        "message": f"Valeur invalide pour le type {field.get('type', 'string')}.",
                    }
                )

        if field.get("unique"):
            duplicate_mask = dataframe[name].notna() & dataframe[name].astype(str).duplicated(keep=False)
            for row_index in dataframe.index[duplicate_mask].tolist():
                issues.append(
                    {
                        "row": int(row_index) + 2,
                        "field": name,
                        "code": "DUPLICATE_VALUE",
                        "severity": "warning",
                        "message": f"Valeur dupliquée: {dataframe.at[row_index, name]}",
                    }
                )

    return issues
