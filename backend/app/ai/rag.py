from typing import Any

import pandas as pd

from app.ai.providers import answer_dashboard_question
from app.ai.vector_store import InMemoryVectorStore, VectorDocument
from app.analytics.profiling import build_column_profiles
from app.analytics.statistics import generate_statistics
from app.models.schemas import DashboardAskRequest, DashboardAskResponse
from app.services.dataset_store import DatasetRecord


async def ask_dashboard(record: DatasetRecord, request: DashboardAskRequest) -> DashboardAskResponse:
    documents = _build_documents(record, request)
    store = InMemoryVectorStore(documents)
    selected_docs = _selected_widget_documents(documents, request.selectedWidgetIndexes)
    retrieved_docs = _dedupe_documents([*selected_docs, *store.search(request.question, limit=10)])
    context = _build_context(record, request, retrieved_docs)

    ai_answer = await answer_dashboard_question(request.question, context)
    if ai_answer:
        return DashboardAskResponse(
            answer=ai_answer["answer"],
            usedWidgets=context["usedWidgetTitles"],
            usedColumns=context["usedColumns"],
            sources=ai_answer.get("sources") or context["sourceTitles"],
            confidence=ai_answer.get("confidence", "medium"),
        )

    local = _local_answer(record.dataframe, request.question, context)
    return DashboardAskResponse(
        answer=local["answer"],
        usedWidgets=context["usedWidgetTitles"],
        usedColumns=context["usedColumns"],
        sources=context["sourceTitles"],
        confidence=local["confidence"],
    )


def _build_documents(record: DatasetRecord, request: DashboardAskRequest) -> list[VectorDocument]:
    df = record.dataframe
    profiles = build_column_profiles(df, record.schema_json)
    stats = generate_statistics(df, record.schema_json)
    documents = [
        VectorDocument(
            id="dataset:overview",
            title="Dataset overview",
            text=f"Dataset {record.dataset_name} has {df.shape[0]} rows and {df.shape[1]} columns. Schema {record.schema_json}. Statistics {stats}.",
            metadata={"kind": "dataset"},
        )
    ]

    for profile in profiles:
        column = profile.name
        documents.append(
            VectorDocument(
                id=f"column:{column}",
                title=f"Column {column}",
                text=f"Column {column}. Type {profile.type}. Role {profile.role}. {profile.warning or ''} Stats {_column_stats(df, column)}.",
                metadata={"kind": "column", "column": column},
            )
        )

    widgets = request.dashboard.widgets if request.dashboard else []
    for index, widget_model in enumerate(widgets):
        widget = widget_model.model_dump()
        title = str(widget.get("title") or f"Widget {index + 1}")
        documents.append(
            VectorDocument(
                id=f"widget:{index}",
                title=title,
                text=_widget_text(index, widget),
                metadata={"kind": "widget", "index": index, "columns": _columns_from_widgets([widget])},
            )
        )

    documents.append(
        VectorDocument(
            id="rows:sample",
            title="Dataset row sample",
            text=f"First rows: {_sample_rows(df, list(df.columns[:8]))}",
            metadata={"kind": "rows"},
        )
    )
    return documents


def _build_context(record: DatasetRecord, request: DashboardAskRequest, retrieved_docs: list[VectorDocument]) -> dict[str, Any]:
    used_columns = _used_columns(record.dataframe, request.question, retrieved_docs)
    used_widget_titles = [doc.title for doc in retrieved_docs if doc.metadata.get("kind") == "widget"]
    return {
        "question": request.question,
        "dataset": {
            "name": record.dataset_name,
            "rows": int(record.dataframe.shape[0]),
            "columns": int(record.dataframe.shape[1]),
            "schema": record.schema_json,
        },
        "retrievedDocuments": [
            {
                "id": document.id,
                "title": document.title,
                "text": document.text[:5000],
                "metadata": document.metadata,
            }
            for document in retrieved_docs
        ],
        "sourceTitles": [document.title for document in retrieved_docs],
        "usedWidgetTitles": used_widget_titles,
        "usedColumns": used_columns,
        "focusedColumnStats": {column: _column_stats(record.dataframe, column) for column in used_columns if column in record.dataframe.columns},
        "focusedRows": _sample_rows(record.dataframe, used_columns),
    }


def _widget_text(index: int, widget: dict[str, Any]) -> str:
    return (
        f"Widget {index}. Title {widget.get('title')}. Type {widget.get('type')}. Chart type {widget.get('chartType')}. "
        f"X axis {widget.get('xAxis')}. Y axis {widget.get('yAxis')}. Aggregation {widget.get('aggregation')}. "
        f"Value {widget.get('value')}. Insight {widget.get('insight')}. Columns {widget.get('columns')}. "
        f"Data {widget.get('data') or widget.get('rows')}."
    )


def _column_stats(df: pd.DataFrame, column: str) -> dict[str, Any]:
    if column not in df.columns:
        return {}
    series = df[column]
    if pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if numeric.empty:
            return {"count": 0}
        return {
            "count": int(numeric.count()),
            "sum": float(numeric.sum()),
            "mean": float(numeric.mean()),
            "min": float(numeric.min()),
            "max": float(numeric.max()),
            "median": float(numeric.median()),
        }
    counts = series.fillna("Unknown").astype(str).value_counts().head(10)
    return {"uniqueValues": int(series.nunique(dropna=True)), "topValues": counts.to_dict()}


def _local_answer(df: pd.DataFrame, question: str, context: dict[str, Any]) -> dict[str, Any]:
    column = _target_column(df, question, context["usedColumns"])
    operation = _operation(question)
    if column and pd.api.types.is_numeric_dtype(df[column]):
        numeric = pd.to_numeric(df[column], errors="coerce").dropna()
        if not numeric.empty:
            value = {
                "sum": numeric.sum(),
                "max": numeric.max(),
                "min": numeric.min(),
                "mean": numeric.mean(),
                "count": numeric.count(),
            }[operation]
            label = {"sum": "total", "max": "maximum", "min": "minimum", "mean": "average", "count": "count"}[operation]
            return {"answer": f"The {label} {column} is {float(value):,.2f}.", "confidence": "high"}

    if context["retrievedDocuments"]:
        best = context["retrievedDocuments"][0]
        return {
            "answer": f"Based on {best['title']}: {best['text'][:350]}",
            "confidence": "medium",
        }
    return {"answer": "I could not find enough retrieved dashboard context to answer that.", "confidence": "low"}


def _operation(question: str) -> str:
    lowered = question.lower()
    if any(word in lowered for word in ["maximum", "max", "highest", "largest"]):
        return "max"
    if any(word in lowered for word in ["minimum", "min", "lowest", "smallest"]):
        return "min"
    if any(word in lowered for word in ["average", "avg", "mean"]):
        return "mean"
    if "count" in lowered or "how many" in lowered:
        return "count"
    return "sum"


def _target_column(df: pd.DataFrame, question: str, used_columns: list[str]) -> str | None:
    lowered = question.lower()
    for column in df.columns:
        if column.lower() in lowered or column.lower().replace("_", " ") in lowered:
            return column
    for column in used_columns:
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            return column
    return None


def _selected_widget_documents(documents: list[VectorDocument], selected_indexes: list[int]) -> list[VectorDocument]:
    selected_ids = {f"widget:{index}" for index in selected_indexes}
    return [document for document in documents if document.id in selected_ids]


def _dedupe_documents(documents: list[VectorDocument]) -> list[VectorDocument]:
    seen: set[str] = set()
    deduped: list[VectorDocument] = []
    for document in documents:
        if document.id in seen:
            continue
        deduped.append(document)
        seen.add(document.id)
    return deduped


def _used_columns(df: pd.DataFrame, question: str, documents: list[VectorDocument]) -> list[str]:
    lowered = question.lower()
    columns: list[str] = []
    for column in df.columns:
        if column.lower() in lowered or column.lower().replace("_", " ") in lowered:
            columns.append(column)
    for document in documents:
        for column in document.metadata.get("columns", []) or []:
            if column in df.columns and column not in columns:
                columns.append(column)
        column = document.metadata.get("column")
        if column in df.columns and column not in columns:
            columns.append(column)
    return columns


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


def _sample_rows(df: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    sample_columns = [column for column in columns if column in df.columns] or list(df.columns[:8])
    sample = df[sample_columns].head(20)
    return sample.where(pd.notnull(sample), None).to_dict("records")
