from fastapi import APIRouter, File, HTTPException, UploadFile

from app.ai.dashboard_builder import generate_dashboard_from_prompt
from app.analytics.cleaning import detect_missing_values
from app.analytics.insights import generate_insights
from app.analytics.recommendations import recommend_visualizations
from app.analytics.statistics import generate_statistics
from app.ingestion.parsers import dataframe_from_api, dataframe_from_upload
from app.models.schemas import (
    ApiConnectorRequest,
    DashboardConfig,
    DashboardPromptRequest,
    DatasetMetadata,
    DatasetSummary,
)
from app.services.dataset_store import dataset_store
from app.analytics.cleaning import infer_column_types

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/datasets", response_model=list[DatasetMetadata])
def list_datasets() -> list[DatasetMetadata]:
    return dataset_store.list()


@router.post("/upload/csv", response_model=DatasetMetadata)
async def upload_csv(file: UploadFile = File(...)) -> DatasetMetadata:
    return await _store_upload(file)


@router.post("/upload/excel", response_model=DatasetMetadata)
async def upload_excel(file: UploadFile = File(...)) -> DatasetMetadata:
    return await _store_upload(file)


@router.post("/upload/json", response_model=DatasetMetadata)
async def upload_json(file: UploadFile = File(...)) -> DatasetMetadata:
    return await _store_upload(file)


@router.post("/connect/api", response_model=DatasetMetadata)
async def connect_api(request: ApiConnectorRequest) -> DatasetMetadata:
    try:
        df = await dataframe_from_api(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    schema = infer_column_types(df)
    record = dataset_store.create(request.dataset_name, "api", df, schema)
    return record.metadata()


@router.post("/connect/database")
def connect_database() -> dict[str, str]:
    return {"status": "planned", "message": "Database connectors arrive in Phase 2."}


@router.get("/dataset/{dataset_id}/summary", response_model=DatasetSummary)
def dataset_summary(dataset_id: str) -> DatasetSummary:
    record = _get_record(dataset_id)
    stats = generate_statistics(record.dataframe, record.schema_json)
    return DatasetSummary(
        dataset=record.metadata(),
        missingValues=detect_missing_values(record.dataframe),
        duplicateRows=0,
        statistics=stats,
        insights=generate_insights(record.dataframe, record.schema_json, stats),
        recommendedCharts=recommend_visualizations(record.dataframe, record.schema_json),
    )


@router.get("/dataset/{dataset_id}/statistics")
def dataset_statistics(dataset_id: str) -> dict:
    record = _get_record(dataset_id)
    return generate_statistics(record.dataframe, record.schema_json)


@router.get("/dataset/{dataset_id}/charts")
def dataset_charts(dataset_id: str) -> list:
    record = _get_record(dataset_id)
    return recommend_visualizations(record.dataframe, record.schema_json)


@router.get("/dataset/{dataset_id}/insights")
def dataset_insights(dataset_id: str) -> list[str]:
    record = _get_record(dataset_id)
    stats = generate_statistics(record.dataframe, record.schema_json)
    return generate_insights(record.dataframe, record.schema_json, stats)


@router.post("/ai/generate-dashboard", response_model=DashboardConfig)
async def generate_dashboard(request: DashboardPromptRequest) -> DashboardConfig:
    record = _get_record(request.datasetId)
    return await generate_dashboard_from_prompt(record, request.prompt)


async def _store_upload(file: UploadFile) -> DatasetMetadata:
    df, source_type = await dataframe_from_upload(file)
    schema = infer_column_types(df)
    record = dataset_store.create(file.filename or "Uploaded Dataset", source_type, df, schema)
    return record.metadata()


def _get_record(dataset_id: str):
    record = dataset_store.get(dataset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return record
