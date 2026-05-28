import warnings

import numpy as np
import pandas as pd

from app.models.schemas import ColumnType


def infer_column_types(df: pd.DataFrame) -> dict[str, ColumnType]:
    schema: dict[str, ColumnType] = {}
    for column in df.columns:
        series = df[column].dropna()
        if series.empty:
            schema[column] = "text"
            continue

        if pd.api.types.is_bool_dtype(series):
            schema[column] = "boolean"
            continue

        if pd.api.types.is_numeric_dtype(series):
            schema[column] = "numerical"
            continue

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            parsed_dates = pd.to_datetime(series, errors="coerce")
        if parsed_dates.notna().mean() > 0.8:
            schema[column] = "datetime"
            continue

        unique_count = series.nunique(dropna=True)
        unique_ratio = unique_count / max(len(series), 1)
        schema[column] = "categorical" if unique_count <= 20 or unique_ratio <= 0.5 else "text"
    return schema


def apply_type_conversions(df: pd.DataFrame, schema: dict[str, ColumnType]) -> pd.DataFrame:
    converted = df.copy()
    for column, column_type in schema.items():
        if column_type == "datetime":
            converted[column] = pd.to_datetime(converted[column], errors="coerce")
        elif column_type == "numerical":
            converted[column] = pd.to_numeric(converted[column], errors="coerce")
        elif column_type == "boolean":
            converted[column] = converted[column].astype("boolean")
    return converted


def detect_missing_values(df: pd.DataFrame) -> dict[str, int]:
    return {column: int(count) for column, count in df.isna().sum().items()}


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().reset_index(drop=True)


def detect_outliers(df: pd.DataFrame) -> dict[str, list[int]]:
    outliers: dict[str, list[int]] = {}
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    for column in numeric_columns:
        series = df[column].dropna()
        if series.empty:
            outliers[column] = []
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers[column] = df.index[(df[column] < lower) | (df[column] > upper)].tolist()
    return outliers


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in normalized.select_dtypes(include=[np.number]).columns:
        min_value = normalized[column].min()
        max_value = normalized[column].max()
        if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
            continue
        normalized[column] = (normalized[column] - min_value) / (max_value - min_value)
    return normalized
