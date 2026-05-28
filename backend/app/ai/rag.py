from typing import Any

import pandas as pd

from app.ai.providers import answer_dashboard_question
from app.analytics.profiling import build_column_profiles
from app.analytics.statistics import generate_statistics
from app.models.schemas import DashboardAskRequest, DashboardAskResponse
from app.services.dataset_store import DatasetRecord


async def ask_dashboard(record: DatasetRecord, request: DashboardAskRequest) -> DashboardAskResponse:
    context = _build_context(record, request)
    ai_answer = await answer_dashboard_question(request.question, context)
    if ai_answer:
        return DashboardAskResponse(
            answer=ai_answer,
            usedWidgets=context["usedWidgetTitles"],
            usedColumns=context["usedColumns"],
        )

    return DashboardAskResponse(
        answer=_local_answer(request.question, context),
        usedWidgets=context["usedWidgetTitles"],
        usedColumns=context["usedColumns"],
    )


def _build_context(record: DatasetRecord, request: DashboardAskRequest) -> dict[str, Any]:
    df = record.dataframe
    profiles = build_column_profiles(df, record.schema_json)
    mentioned_columns = _mentioned_columns(request.question, list(df.columns))
    selected_widgets = _selected_widgets(request)
    widget_columns = _columns_from_widgets(selected_widgets)
    used_columns = list(dict.fromkeys([*mentioned_columns, *widget_columns]))

    return {
        "dataset": {
            "name": record.dataset_name,
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "schema": record.schema_json,
            "columnProfiles": [profile.model_dump() for profile in profiles],
        },
        "question": request.question,
        "selectedWidgets": [_summarize_widget(widget) for widget in selected_widgets],
        "usedWidgetTitles": [str(widget.get("title", widget.get("type", "Widget"))) for widget in selected_widgets],
        "usedColumns": used_columns,
        "columnContext": _column_context(df, used_columns or mentioned_columns),
        "datasetStatistics": generate_statistics(df, record.schema_json),
        "rowSamples": _sample_rows(df, used_columns),
    }


def _selected_widgets(request: DashboardAskRequest) -> list[dict[str, Any]]:
    widgets = request.dashboard.widgets if request.dashboard else []
    selected: list[dict[str, Any]] = []
    for index in request.selectedWidgetIndexes:
        if 0 <= index < len(widgets):
            selected.append(widgets[index].model_dump())
    return selected


def _columns_from_widgets(widgets: list[dict[str, Any]]) -> list[str]:
    columns: list[str] = []
    for widget in widgets:
        for key in ["xAxis", "yAxis", "column"]:
            value = widget.get(key)
            if isinstance(value, str) and value not in columns:
                columns.append(value)
        for column in widget.get("columns", []) or []:
            if isinstance(column, str) and column not in columns:
                columns.append(column)
    return columns


def _mentioned_columns(question: str, columns: list[str]) -> list[str]:
    lowered = question.lower()
    mentioned = []
    for column in columns:
        if column.lower().replace("_", " ") in lowered or column.lower() in lowered:
            mentioned.append(column)
    return mentioned


def _column_context(df: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for column in columns:
        if column not in df.columns:
            continue
        series = df[column]
        if pd.api.types.is_numeric_dtype(series):
            numeric = pd.to_numeric(series, errors="coerce").dropna()
            context[column] = {
                "count": int(numeric.count()),
                "sum": float(numeric.sum()) if not numeric.empty else 0,
                "mean": float(numeric.mean()) if not numeric.empty else 0,
                "min": float(numeric.min()) if not numeric.empty else None,
                "max": float(numeric.max()) if not numeric.empty else None,
            }
        else:
            counts = series.fillna("Unknown").astype(str).value_counts().head(10)
            context[column] = {
                "uniqueValues": int(series.nunique(dropna=True)),
                "topValues": counts.to_dict(),
            }
    return context


def _sample_rows(df: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    sample_columns = [column for column in columns if column in df.columns]
    if not sample_columns:
        sample_columns = list(df.columns[:8])
    return df[sample_columns].head(20).where(pd.notnull(df[sample_columns]), None).to_dict("records")


def _summarize_widget(widget: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": widget.get("type"),
        "title": widget.get("title"),
        "chartType": widget.get("chartType"),
        "xAxis": widget.get("xAxis"),
        "yAxis": widget.get("yAxis"),
        "aggregation": widget.get("aggregation"),
        "insight": widget.get("insight"),
        "dataSample": widget.get("data", [])[:12],
        "value": widget.get("value"),
        "columns": widget.get("columns"),
    }


def _local_answer(question: str, context: dict[str, Any]) -> str:
    if context["selectedWidgets"]:
        widget_names = ", ".join(context["usedWidgetTitles"])
        return f"I used the selected widget context ({widget_names}). {context['selectedWidgets'][0].get('insight') or 'Ask a more specific question about the selected columns for a deeper answer.'}"
    if context["usedColumns"]:
        columns = ", ".join(context["usedColumns"])
        return f"I found context for {columns}. Configure Gemini or Hugging Face on the backend for richer natural-language dashboard answers."
    return "Select one or more widgets, or mention a column name in your question, so I can ground the answer in the dashboard data."
