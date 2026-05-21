from typing import Any

import pandas as pd

from app.models.schemas import ChartConfig, ColumnType


def recommend_visualizations(df: pd.DataFrame, schema: dict[str, ColumnType]) -> list[ChartConfig]:
    charts: list[ChartConfig] = []
    numeric = [column for column, kind in schema.items() if kind == "numerical"]
    categorical = [column for column, kind in schema.items() if kind == "categorical"]
    datetime = [column for column, kind in schema.items() if kind == "datetime"]

    if datetime and numeric:
        date_col, metric = datetime[0], numeric[0]
        data = (
            df.assign(__date=pd.to_datetime(df[date_col], errors="coerce"))
            .dropna(subset=["__date"])
            .set_index("__date")
            .resample("ME")[metric]
            .sum()
            .reset_index()
        )
        data[date_col] = data["__date"].dt.strftime("%Y-%m")
        charts.append(
            ChartConfig(
                chartType="line",
                title=f"{metric} over time",
                xAxis=date_col,
                yAxis=metric,
                data=data[[date_col, metric]].to_dict("records"),
            )
        )

    if categorical and numeric:
        category, metric = categorical[0], numeric[0]
        grouped = (
            df.groupby(category)[metric]
            .sum(numeric_only=True)
            .sort_values(ascending=False)
            .head(8)
            .reset_index()
        )
        charts.append(
            ChartConfig(
                chartType="bar",
                title=f"{metric} by {category}",
                xAxis=category,
                yAxis=metric,
                data=grouped.to_dict("records"),
            )
        )

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
    numeric = [column for column, kind in schema.items() if kind == "numerical"]
    kpis: list[dict[str, Any]] = [
        {"title": "Rows", "value": f"{len(df):,}", "tone": "neutral"},
        {"title": "Columns", "value": f"{len(df.columns):,}", "tone": "neutral"},
    ]
    for column in numeric[:2]:
        value = pd.to_numeric(df[column], errors="coerce").sum()
        kpis.append({"title": f"Total {column}", "value": f"{value:,.2f}", "tone": "positive"})
    return kpis
