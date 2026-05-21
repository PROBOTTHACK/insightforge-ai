from typing import Any

import pandas as pd

from app.models.schemas import ColumnType


def generate_insights(
    df: pd.DataFrame,
    schema: dict[str, ColumnType],
    statistics: dict[str, Any],
) -> list[str]:
    insights: list[str] = []
    numeric_columns = [column for column, kind in schema.items() if kind == "numerical"]
    categorical_columns = [column for column, kind in schema.items() if kind == "categorical"]

    for column, values in statistics.get("numerical", {}).items():
        insights.append(
            f"{column} ranges from {values['min']:.2f} to {values['max']:.2f}, with an average of {values['mean']:.2f}."
        )

    if numeric_columns and categorical_columns:
        metric = numeric_columns[0]
        category = categorical_columns[0]
        grouped = df.groupby(category)[metric].sum(numeric_only=True).sort_values(ascending=False)
        if not grouped.empty and grouped.sum() != 0:
            top_name = str(grouped.index[0])
            share = grouped.iloc[0] / grouped.sum() * 100
            insights.append(f"{top_name} contributes {share:.1f}% of total {metric}.")

    for key, values in statistics.get("timeSeries", {}).items():
        growth = values.get("growthRate")
        if growth is not None:
            direction = "increased" if growth >= 0 else "decreased"
            insights.append(f"{key} {direction} {abs(growth):.1f}% in the latest period.")

    for relationship in statistics.get("correlation", {}).get("strongestRelationships", []):
        left, right = relationship["columns"]
        insights.append(
            f"{left} and {right} show a strong correlation of {relationship['correlation']:.2f}."
        )

    if not insights:
        insights.append("The dataset was parsed successfully, but more rows or typed columns are needed for richer insights.")

    return insights[:8]
