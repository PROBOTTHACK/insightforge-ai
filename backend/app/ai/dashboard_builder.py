import re

from app.analytics.chart_builder import build_chart
from app.analytics.profiling import build_column_profiles
from app.analytics.recommendations import recommend_visualizations, top_kpis
from app.ai.providers import select_dashboard_plan
from app.models.schemas import ChartConfig, DashboardConfig, DashboardWidget, KPIConfig, TableConfig
from app.services.dataset_store import DatasetRecord


async def generate_dashboard_from_prompt(record: DatasetRecord, prompt: str) -> DashboardConfig:
    explicit_chart = _chart_from_explicit_prompt(record, prompt)
    if explicit_chart:
        widgets = [
            *[KPIConfig(**item) for item in top_kpis(record.dataframe, record.schema_json)][:3],
            explicit_chart,
            _preview_table(record),
        ]
        return DashboardConfig(
            dashboardName=_title_from_prompt(prompt),
            datasetId=record.id,
            widgets=widgets,
        )

    widgets = _candidate_widgets(record)
    candidates = [_summarize_widget(index, widget) for index, widget in enumerate(widgets)]
    context = {
        "rows": int(record.dataframe.shape[0]),
        "columns": int(record.dataframe.shape[1]),
        "schema": record.schema_json,
    }
    plan = await select_dashboard_plan(prompt, context, candidates)
    if plan:
        selected = _widgets_from_plan(widgets, plan)
        if selected:
            return DashboardConfig(
                dashboardName=plan["dashboardName"],
                datasetId=record.id,
                widgets=selected,
            )

    dashboard = _local_dashboard(record, prompt)
    return dashboard


def _local_dashboard(record: DatasetRecord, prompt: str) -> DashboardConfig:
    prompt_lower = prompt.lower()
    kpis = [widget for widget in _candidate_widgets(record) if widget.type == "kpi"]
    charts = [widget for widget in _candidate_widgets(record) if isinstance(widget, ChartConfig)]
    table = [widget for widget in _candidate_widgets(record) if widget.type == "table"]

    selected_charts = charts
    if "sales" in prompt_lower or "revenue" in prompt_lower:
        selected_charts = [chart for chart in charts if chart.chartType in {"line", "bar", "pie"}] or charts
    elif "relationship" in prompt_lower or "correlation" in prompt_lower:
        selected_charts = [chart for chart in charts if chart.chartType in {"scatter", "heatmap"}] or charts
    elif "distribution" in prompt_lower:
        selected_charts = [chart for chart in charts if chart.chartType == "histogram"] or charts

    widgets = [
        *kpis[:4],
        *selected_charts[:4],
        *table[:1],
    ]

    return DashboardConfig(
        dashboardName=_title_from_prompt(prompt),
        datasetId=record.id,
        widgets=widgets,
    )


def _candidate_widgets(record: DatasetRecord) -> list[DashboardWidget]:
    return [
        *[KPIConfig(**item) for item in top_kpis(record.dataframe, record.schema_json)],
        *recommend_visualizations(record.dataframe, record.schema_json),
        _preview_table(record),
    ]


def _summarize_widget(index: int, widget: DashboardWidget) -> dict:
    summary = {"index": index, "type": widget.type, "title": widget.title}
    if isinstance(widget, ChartConfig):
        summary.update({"chartType": widget.chartType, "xAxis": widget.xAxis, "yAxis": widget.yAxis})
    return summary


def _widgets_from_plan(widgets: list[DashboardWidget], plan: dict) -> list[DashboardWidget]:
    selected: list[DashboardWidget] = []
    seen: set[int] = set()
    for raw_index in plan["widgetIndexes"]:
        if not isinstance(raw_index, int) or raw_index in seen:
            continue
        if 0 <= raw_index < len(widgets):
            selected.append(widgets[raw_index])
            seen.add(raw_index)
    return selected


def _chart_from_explicit_prompt(record: DatasetRecord, prompt: str) -> ChartConfig | None:
    mentioned = _mentioned_columns(prompt, list(record.dataframe.columns))
    if not mentioned:
        return None

    prompt_lower = prompt.lower()
    chart_type = "scatter" if "scatter" in prompt_lower else "bar"
    if "line" in prompt_lower or "trend" in prompt_lower or "time" in prompt_lower:
        chart_type = "line"
    elif "pie" in prompt_lower or "share" in prompt_lower or "proportion" in prompt_lower:
        chart_type = "pie"
    elif "histogram" in prompt_lower or "distribution" in prompt_lower:
        chart_type = "histogram"
    elif "horizontal" in prompt_lower:
        chart_type = "horizontal_bar"

    profiles = {profile.name: profile for profile in build_column_profiles(record.dataframe, record.schema_json)}
    metrics = [column for column in mentioned if profiles[column].role == "metric"]
    axes = [column for column in mentioned if profiles[column].role in {"dimension", "timestamp", "identifier"}]

    aggregation = "mean" if any(word in prompt_lower for word in ["average", "avg", "mean"]) else "sum"
    if "count" in prompt_lower:
        aggregation = "count"

    if chart_type == "histogram":
        metric = metrics[0] if metrics else mentioned[0]
        return build_chart(record.dataframe, record.schema_json, "histogram", metric, metric, "count")

    if chart_type == "scatter" and len(metrics) >= 2:
        return build_chart(record.dataframe, record.schema_json, "scatter", metrics[0], metrics[1], "none")

    x_axis = axes[0] if axes else mentioned[0]
    y_axis = metrics[0] if metrics else None
    if y_axis == x_axis:
        y_axis = metrics[1] if len(metrics) > 1 else None

    return build_chart(record.dataframe, record.schema_json, chart_type, x_axis, y_axis, aggregation)


def _mentioned_columns(prompt: str, columns: list[str]) -> list[str]:
    normalized_prompt = _normalize(prompt)
    matches: list[tuple[int, str]] = []
    for column in columns:
        normalized_column = _normalize(column)
        index = normalized_prompt.find(normalized_column)
        if index >= 0:
            matches.append((index, column))
    return [column for _, column in sorted(matches)]


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _preview_table(record: DatasetRecord) -> TableConfig:
    return TableConfig(
        title="Dataset Preview",
        columns=list(record.dataframe.columns[:8]),
        rows=record.dataframe.head(8).where(record.dataframe.notnull(), None).to_dict("records"),
    )


def _title_from_prompt(prompt: str) -> str:
    lowered = prompt.lower()
    if "sales" in lowered or "revenue" in lowered:
        return "Sales Analytics"
    if "customer" in lowered:
        return "Customer Analytics"
    if "product" in lowered:
        return "Product Performance"
    if "finance" in lowered:
        return "Financial Overview"
    return "AI Generated Dashboard"
