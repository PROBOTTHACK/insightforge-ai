from typing import Any
from itertools import combinations

import pandas as pd

from app.models.schemas import ColumnType


def generate_statistics(df: pd.DataFrame, schema: dict[str, ColumnType]) -> dict[str, Any]:
    numeric_columns = [column for column, kind in schema.items() if kind == "numerical"]
    categorical_columns = [column for column, kind in schema.items() if kind == "categorical"]
    datetime_columns = [column for column, kind in schema.items() if kind == "datetime"]

    stats: dict[str, Any] = {
        "numerical": {},
        "categorical": {},
        "timeSeries": {},
        "correlation": {},
    }

    for column in numeric_columns:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            continue
        stats["numerical"][column] = {
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std()) if len(series) > 1 else 0,
            "min": float(series.min()),
            "max": float(series.max()),
            "sum": float(series.sum()),
        }

    for column in categorical_columns:
        counts = df[column].fillna("Unknown").astype(str).value_counts().head(10)
        stats["categorical"][column] = {
            "uniqueValues": int(df[column].nunique(dropna=True)),
            "topCategories": counts.to_dict(),
        }

    for date_column in datetime_columns:
        parsed = pd.to_datetime(df[date_column], errors="coerce")
        for metric in numeric_columns[:3]:
            grouped = (
                df.assign(__date=parsed)
                .dropna(subset=["__date"])
                .set_index("__date")
                .resample("ME")[metric]
                .sum()
                .dropna()
            )
            if len(grouped) >= 2:
                previous = grouped.iloc[-2]
                current = grouped.iloc[-1]
                growth = ((current - previous) / previous * 100) if previous else 0
                stats["timeSeries"][f"{metric}_by_{date_column}"] = {
                    "latest": float(current),
                    "previous": float(previous),
                    "growthRate": float(growth),
                    "movingAverage": grouped.rolling(window=min(3, len(grouped))).mean().tail(6).to_dict(),
                }

    if len(numeric_columns) >= 2:
        corr = df[numeric_columns].corr(numeric_only=True).round(3)
        stats["correlation"]["matrix"] = corr.fillna(0).to_dict()
        relationships: list[dict[str, Any]] = []
        for left, right in combinations(numeric_columns, 2):
            value = corr.loc[left, right]
            if abs(value) >= 0.5:
                relationships.append({"columns": [left, right], "correlation": float(value)})
        stats["correlation"]["strongestRelationships"] = sorted(
            relationships,
            key=lambda item: abs(item["correlation"]),
            reverse=True,
        )[:5]

    return stats
