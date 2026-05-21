from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
from fastapi import HTTPException, UploadFile

from app.analytics.cleaning import apply_type_conversions, infer_column_types, remove_duplicates
from app.models.schemas import ApiConnectorRequest


async def dataframe_from_upload(file: UploadFile) -> tuple[pd.DataFrame, str]:
    suffix = Path(file.filename or "").suffix.lower()
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    buffer = BytesIO(content)
    if suffix == ".csv":
        df = pd.read_csv(buffer)
        source_type = "csv"
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(buffer)
        source_type = "excel"
    elif suffix == ".json":
        df = pd.read_json(buffer)
        source_type = "json"
    else:
        raise HTTPException(status_code=400, detail="Supported formats: CSV, Excel, JSON.")

    return prepare_dataframe(df), source_type


async def dataframe_from_api(request: ApiConnectorRequest) -> pd.DataFrame:
    headers = dict(request.headers)
    if request.auth_token:
        headers["Authorization"] = f"Bearer {request.auth_token}"

    url = str(request.base_url).rstrip("/") + "/" + request.endpoint.lstrip("/")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers, params=request.query_params)
        response.raise_for_status()

    payload = response.json()
    records = _extract_records(payload, request.records_path)
    return prepare_dataframe(pd.DataFrame(records))


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(axis=1, how="all")
    schema = infer_column_types(df)
    converted = apply_type_conversions(df, schema)
    return remove_duplicates(converted)


def _extract_records(payload: Any, records_path: str | None) -> list[dict[str, Any]]:
    data = payload
    if records_path:
        for part in records_path.split("."):
            if isinstance(data, dict):
                data = data.get(part)
            else:
                raise HTTPException(status_code=400, detail=f"Cannot read records path: {records_path}")

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return value
        return [data]
    raise HTTPException(status_code=400, detail="API response could not be converted to tabular records.")
