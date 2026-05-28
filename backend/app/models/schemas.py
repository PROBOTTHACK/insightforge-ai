from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


ColumnType = Literal["numerical", "categorical", "boolean", "datetime", "text"]
WidgetType = Literal["kpi", "chart", "table", "filter"]
ChartType = Literal["bar", "horizontal_bar", "line", "histogram", "heatmap", "pie", "scatter"]
AggregationType = Literal["sum", "mean", "count", "min", "max", "none"]
ColumnRole = Literal["metric", "dimension", "identifier", "timestamp", "text"]


class ColumnProfile(BaseModel):
    name: str
    type: ColumnType
    role: ColumnRole
    uniqueValues: int
    missingValues: int
    recommendedForKpi: bool = False
    recommendedForAxis: bool = False
    warning: str | None = None


class DatasetMetadata(BaseModel):
    id: str
    dataset_name: str
    source_type: str
    rows: int
    columns: int
    column_schema: dict[str, ColumnType] = Field(alias="schema_json")
    column_profiles: list[ColumnProfile] = Field(default_factory=list, alias="column_profiles")
    preview: list[dict[str, Any]]


class ApiConnectorRequest(BaseModel):
    dataset_name: str = "API Dataset"
    base_url: HttpUrl
    endpoint: str = ""
    headers: dict[str, str] = Field(default_factory=dict)
    auth_token: str | None = None
    query_params: dict[str, Any] = Field(default_factory=dict)
    records_path: str | None = Field(
        default=None,
        description="Optional dotted path to the array of records inside a JSON response.",
    )


class ChartConfig(BaseModel):
    type: Literal["chart"] = "chart"
    chartType: ChartType
    title: str
    xAxis: str | None = None
    yAxis: str | None = None
    aggregation: AggregationType = "sum"
    insight: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)


class KPIConfig(BaseModel):
    type: Literal["kpi"] = "kpi"
    title: str
    value: str | int | float
    delta: str | None = None
    tone: Literal["neutral", "positive", "negative"] = "neutral"


class TableConfig(BaseModel):
    type: Literal["table"] = "table"
    title: str
    columns: list[str]
    rows: list[dict[str, Any]]


class FilterConfig(BaseModel):
    type: Literal["filter"] = "filter"
    title: str
    column: str
    options: list[str]


DashboardWidget = KPIConfig | ChartConfig | TableConfig | FilterConfig


class DashboardConfig(BaseModel):
    dashboardName: str
    datasetId: str
    widgets: list[DashboardWidget]


class DashboardPromptRequest(BaseModel):
    datasetId: str
    prompt: str


class CustomChartRequest(BaseModel):
    datasetId: str
    chartType: ChartType
    xAxis: str | None = None
    yAxis: str | None = None
    aggregation: AggregationType = "sum"
    title: str | None = None


class DashboardAskRequest(BaseModel):
    datasetId: str
    question: str
    dashboard: DashboardConfig | None = None
    selectedWidgetIndexes: list[int] = Field(default_factory=list)


class DashboardAskResponse(BaseModel):
    answer: str
    usedWidgets: list[str] = Field(default_factory=list)
    usedColumns: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    provider: str = "local"


class DatasetSummary(BaseModel):
    dataset: DatasetMetadata
    missingValues: dict[str, int]
    duplicateRows: int
    statistics: dict[str, Any]
    insights: list[str]
    recommendedCharts: list[ChartConfig]
