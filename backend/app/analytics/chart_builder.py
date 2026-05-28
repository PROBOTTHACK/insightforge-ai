import pandas as pd
from fastapi import HTTPException

from app.analytics.profiling import infer_column_role
from app.models.schemas import AggregationType, ChartConfig, ChartType, ColumnType


def build_chart(
    df: pd.DataFrame,
    schema: dict[str, ColumnType],
    chart_type: ChartType,
    x_axis: str | None,
    y_axis: str | None,
    aggregation: AggregationType = "sum",
    title: str | None = None,
) -> ChartConfig:
    _validate_column(df, x_axis, "xAxis")
    _validate_column(df, y_axis, "yAxis")

    if chart_type in {"bar", "horizontal_bar", "line", "pie"}:
        if not x_axis:
            raise HTTPException(status_code=400, detail="This chart type needs an xAxis column.")
        data, y_key = _aggregate(df, x_axis, y_axis, aggregation)
    elif chart_type == "histogram":
        metric = y_axis or x_axis
        if not metric:
            raise HTTPException(status_code=400, detail="Histogram needs a numeric column.")
        series = pd.to_numeric(df[metric], errors="coerce").dropna()
        buckets = pd.cut(series, bins=min(10, max(3, series.nunique())), duplicates="drop")
        histogram = series.groupby(buckets, observed=True).size().reset_index(name="count")
        histogram["bucket"] = histogram[metric].astype(str)
        data = histogram[["bucket", "count"]].to_dict("records")
        x_axis = "bucket"
        y_key = "count"
        aggregation = "count"
    elif chart_type == "scatter":
        if not x_axis or not y_axis:
            raise HTTPException(status_code=400, detail="Scatter chart needs both xAxis and yAxis columns.")
        data = df[[x_axis, y_axis]].dropna().head(500).to_dict("records")
        y_key = y_axis
        aggregation = "none"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported chart type: {chart_type}")

    chart_title = title or _chart_title(chart_type, x_axis, y_axis, aggregation)
    return ChartConfig(
        chartType=chart_type,
        title=chart_title,
        xAxis=x_axis,
        yAxis=y_key,
        aggregation=aggregation,
        insight=_chart_insight(data, x_axis, y_key, chart_title),
        data=data,
    )


def _aggregate(
    df: pd.DataFrame,
    x_axis: str,
    y_axis: str | None,
    aggregation: AggregationType,
) -> tuple[list[dict], str]:
    if aggregation == "count" or not y_axis:
        grouped = df.groupby(x_axis).size().reset_index(name="count")
        return grouped.sort_values("count", ascending=False).head(20).to_dict("records"), "count"

    numeric = pd.to_numeric(df[y_axis], errors="coerce")
    temp = df.assign(__metric=numeric).dropna(subset=["__metric"])

    if aggregation == "mean":
        grouped = temp.groupby(x_axis)["__metric"].mean().reset_index(name=y_axis)
    elif aggregation == "min":
        grouped = temp.groupby(x_axis)["__metric"].min().reset_index(name=y_axis)
    elif aggregation == "max":
        grouped = temp.groupby(x_axis)["__metric"].max().reset_index(name=y_axis)
    elif aggregation == "none":
        return temp[[x_axis, y_axis]].head(500).to_dict("records"), y_axis
    else:
        grouped = temp.groupby(x_axis)["__metric"].sum().reset_index(name=y_axis)

    return grouped.sort_values(y_axis, ascending=False).head(20).to_dict("records"), y_axis


def _validate_column(df: pd.DataFrame, column: str | None, field_name: str) -> None:
    if column and column not in df.columns:
        raise HTTPException(status_code=400, detail=f"{field_name} column '{column}' does not exist.")


def _chart_title(chart_type: ChartType, x_axis: str | None, y_axis: str | None, aggregation: AggregationType) -> str:
    if chart_type == "histogram":
        return f"{y_axis or x_axis} distribution"
    if chart_type == "scatter":
        return f"{y_axis} vs {x_axis}"
    if y_axis:
        return f"{aggregation.title()} {y_axis} by {x_axis}"
    return f"Count by {x_axis}"


def _chart_insight(data: list[dict], x_axis: str | None, y_axis: str | None, title: str) -> str | None:
    if not data or not x_axis or not y_axis:
        return None
    numeric_rows = [row for row in data if isinstance(row.get(y_axis), int | float)]
    if not numeric_rows:
        return None
    top = max(numeric_rows, key=lambda row: row[y_axis])
    total = sum(float(row[y_axis]) for row in numeric_rows)
    if total:
        share = float(top[y_axis]) / total * 100
        return f"{top.get(x_axis)} leads this chart with {top.get(y_axis):,.2f}, representing {share:.1f}% of the displayed total."
    return f"{title} contains {len(data)} plotted records."
