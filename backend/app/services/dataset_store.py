from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import pandas as pd

from app.analytics.profiling import build_column_profiles
from app.models.schemas import ColumnType, DatasetMetadata


@dataclass
class DatasetRecord:
    id: str
    dataset_name: str
    source_type: str
    dataframe: pd.DataFrame
    schema_json: dict[str, ColumnType]
    raw_metadata: dict[str, Any] = field(default_factory=dict)

    def metadata(self) -> DatasetMetadata:
        preview = self.dataframe.head(10).where(pd.notnull(self.dataframe), None).to_dict("records")
        return DatasetMetadata(
            id=self.id,
            dataset_name=self.dataset_name,
            source_type=self.source_type,
            rows=int(self.dataframe.shape[0]),
            columns=int(self.dataframe.shape[1]),
            schema_json=self.schema_json,
            column_profiles=build_column_profiles(self.dataframe, self.schema_json),
            preview=preview,
        )


class InMemoryDatasetStore:
    def __init__(self) -> None:
        self._datasets: dict[str, DatasetRecord] = {}

    def create(
        self,
        dataset_name: str,
        source_type: str,
        dataframe: pd.DataFrame,
        schema_json: dict[str, ColumnType],
        raw_metadata: dict[str, Any] | None = None,
    ) -> DatasetRecord:
        record = DatasetRecord(
            id=str(uuid4()),
            dataset_name=dataset_name,
            source_type=source_type,
            dataframe=dataframe,
            schema_json=schema_json,
            raw_metadata=raw_metadata or {},
        )
        self._datasets[record.id] = record
        return record

    def get(self, dataset_id: str) -> DatasetRecord | None:
        return self._datasets.get(dataset_id)

    def list(self) -> list[DatasetMetadata]:
        return [record.metadata() for record in self._datasets.values()]


dataset_store = InMemoryDatasetStore()
