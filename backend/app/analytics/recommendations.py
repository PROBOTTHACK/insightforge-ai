from typing import Any

import pandas as pd

from app.analytics.chart_builder import build_chart
from app.analytics.profiling import dimension_columns, metric_columns
from app.models.schemas import ChartConfig, ColumnType


def recommend_visualizations(df: pd.DataFrame, schema: dict[str, ColumnType]) -> list[ChartConfig]:
    charts: list[ChartConfig] = []
    numeric = metric_columns(df, schema)
    categorical = [column for column in dimension_columns(df, schema) if schema[column] == "categorical"]
    datetime = [column for column, kind in schema.items() if kind == "datetime"]

    if datetime and numeric:
        date_col, metric = datetime[0], numeric[0]
        data = df.assign(__month=pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m"))
        charts.append(build_chart(data, {**schema, "__month": "categorical"}, "line", "__month", metric, "sum", f"{metric} over time"))

    if categorical and numeric:
        category, metric = categorical[0], numeric[0]
        charts.append(build_chart(df, schema, "bar", category, metric, "sum", f"{metric} by {category}"))

    if numeric:
        metric = numeric[0]
        series = pd.to_numeric(df[metric], errors="coerce").dropna()
        buckets = pd.cut(series, bins=min(10, max(3, series.nunique())), duplicates="drop")
        histogram = series.groupby(buckets, observed=True).size().reset_index(name="count")
        histogram["bucket"] = histogram[metric].astype(str)
        charts.append(
            ChartConfig(
                chartType="histogram",
                title=f"{metric} distribution",
                xAxis="bucket",
                yAxis="count",
                data=histogram[["bucket", "count"]].to_dict("records"),
            )
        )

    if len(numeric) >= 2:
        left, right = numeric[:2]
        sample = df[[left, right]].dropna().head(200)
        charts.append(
            ChartConfig(
                chartType="scatter",
                title=f"{left} vs {right}",
                xAxis=left,
                yAxis=right,
                data=sample.to_dict("records"),
            )
        )

    if categorical:
        category = categorical[0]
        counts = df[category].fillna("Unknown").astype(str).value_counts().head(6).reset_index()
        counts.columns = [category, "count"]
        charts.append(
            ChartConfig(
                chartType="pie",
                title=f"{category} share",
                xAxis=category,
                yAxis="count",
                data=counts.to_dict("records"),
            )
        )

    return charts[:6]


def top_kpis(df: pd.DataFrame, schema: dict[str, ColumnType]) -> list[dict[str, Any]]:
    numeric = metric_columns(df, schema)
    kpis: list[dict[str, Any]] = [
        {"title": "Rows", "value": f"{len(df):,}", "tone": "neutral"},
        {"title": "Columns", "value": f"{len(df.columns):,}", "tone": "neutral"},
    ]
    for column in numeric[:2]:
        value = pd.to_numeric(df[column], errors="coerce").sum()
        kpis.append({"title": f"Total {column}", "value": f"{value:,.2f}", "tone": "positive"})
    return kpis
