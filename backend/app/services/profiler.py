from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import pandas as pd
from dateutil import parser as date_parser


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^[+()\d\s.\-]{6,}$")


def _safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def infer_type(series: pd.Series) -> str:
    non_null = series.dropna().astype(str).str.strip()
    non_null = non_null[non_null != ""]
    if non_null.empty:
        return "string"

    sample = non_null.head(100)
    email_ratio = sample.map(lambda x: bool(EMAIL_RE.match(x))).mean()
    if email_ratio >= 0.8:
        return "email"

    phone_ratio = sample.map(lambda x: bool(PHONE_RE.match(x))).mean()
    if phone_ratio >= 0.8 and sample.str.replace(r"\D", "", regex=True).str.len().median() >= 6:
        return "phone"

    numeric = pd.to_numeric(sample.str.replace(",", ".", regex=False), errors="coerce")
    numeric_ratio = numeric.notna().mean()
    if numeric_ratio >= 0.9:
        if numeric.dropna().map(lambda value: float(value).is_integer()).all():
            return "integer"
        return "float"

    def can_parse_date(value: str) -> bool:
        if len(value) < 6:
            return False
        try:
            date_parser.parse(value, fuzzy=False)
            return True
        except (ValueError, OverflowError):
            return False

    date_ratio = sample.map(can_parse_date).mean()
    if date_ratio >= 0.8:
        return "date"

    bool_values = {x.lower() for x in sample}
    if bool_values and bool_values <= {"1", "0", "true", "false", "yes", "no", "oui", "non"}:
        return "boolean"

    return "string"


def profile_csv(path: str | Path) -> dict:
    path = Path(path)
    dataframe = pd.read_csv(path, dtype=object, keep_default_na=True)
    columns = []

    for name in dataframe.columns:
        series = dataframe[name]
        non_null = series.dropna()
        samples = [_safe_value(v) for v in non_null.head(5).tolist()]
        columns.append(
            {
                "name": str(name),
                "inferred_type": infer_type(series),
                "null_count": int(series.isna().sum() + (series.astype(str).str.strip() == "").sum()),
                "unique_count": int(non_null.nunique(dropna=True)),
                "samples": samples,
            }
        )

    return {
        "filename": path.name,
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "columns": columns,
    }
