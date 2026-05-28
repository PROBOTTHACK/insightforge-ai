import re

import pandas as pd

from app.models.schemas import ColumnProfile, ColumnRole, ColumnType

IDENTIFIER_PATTERNS = [
    "id",
    "code",
    "postal",
    "postcode",
    "zip",
    "pin",
    "phone",
    "mobile",
    "account",
    "ssn",
    "uuid",
]

METRIC_PATTERNS = [
    "revenue",
    "sales",
    "amount",
    "price",
    "cost",
    "order",
    "orders",
    "quantity",
    "qty",
    "total",
    "profit",
    "margin",
    "rate",
    "score",
    "customer",
    "customers",
    "churn",
    "units",
]


def build_column_profiles(df: pd.DataFrame, schema: dict[str, ColumnType]) -> list[ColumnProfile]:
    profiles: list[ColumnProfile] = []
    for column, column_type in schema.items():
        role = infer_column_role(df, column, column_type)
        warning = None
        if role == "identifier":
            warning = "Looks like an identifier/code, so it is not recommended for totals or KPIs."

        profiles.append(
            ColumnProfile(
                name=column,
                type=column_type,
                role=role,
                uniqueValues=int(df[column].nunique(dropna=True)),
                missingValues=int(df[column].isna().sum()),
                recommendedForKpi=role == "metric",
                recommendedForAxis=role in {"dimension", "timestamp"},
                warning=warning,
            )
        )
    return profiles


def infer_column_role(df: pd.DataFrame, column: str, column_type: ColumnType) -> ColumnRole:
    normalized = re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_")
    tokens = set(normalized.split("_"))

    if column_type == "datetime":
        return "timestamp"
    if column_type in {"categorical", "boolean"}:
        return "identifier" if _looks_like_identifier_name(normalized, tokens) else "dimension"
    if column_type == "text":
        return "identifier" if _looks_like_identifier_name(normalized, tokens) else "text"
    if column_type != "numerical":
        return "text"

    if _looks_like_metric_name(normalized, tokens):
        return "metric"

    if _looks_like_identifier_name(normalized, tokens):
        return "identifier"

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    unique_ratio = series.nunique(dropna=True) / max(len(series), 1)
    is_integer_like = bool(((series % 1).abs() < 1e-9).all()) if not series.empty else False
    if is_integer_like and unique_ratio > 0.9 and series.min() > 99:
        return "identifier"

    return "metric"


def metric_columns(df: pd.DataFrame, schema: dict[str, ColumnType]) -> list[str]:
    return [profile.name for profile in build_column_profiles(df, schema) if profile.role == "metric"]


def dimension_columns(df: pd.DataFrame, schema: dict[str, ColumnType]) -> list[str]:
    return [profile.name for profile in build_column_profiles(df, schema) if profile.role in {"dimension", "timestamp"}]


def _looks_like_identifier_name(normalized: str, tokens: set[str]) -> bool:
    return any(pattern in normalized or pattern in tokens for pattern in IDENTIFIER_PATTERNS)


def _looks_like_metric_name(normalized: str, tokens: set[str]) -> bool:
    return any(pattern in normalized or pattern in tokens for pattern in METRIC_PATTERNS)
