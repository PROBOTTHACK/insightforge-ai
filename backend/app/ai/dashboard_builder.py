from app.analytics.recommendations import recommend_visualizations, top_kpis
from app.ai.providers import select_dashboard_plan
from app.models.schemas import ChartConfig, DashboardConfig, DashboardWidget, KPIConfig, TableConfig
from app.services.dataset_store import DatasetRecord


async def generate_dashboard_from_prompt(record: DatasetRecord, prompt: str) -> DashboardConfig:
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

    return _local_dashboard(record, prompt)


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
        TableConfig(
            title="Dataset Preview",
            columns=list(record.dataframe.columns[:8]),
            rows=record.dataframe.head(8).where(record.dataframe.notnull(), None).to_dict("records"),
        ),
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
