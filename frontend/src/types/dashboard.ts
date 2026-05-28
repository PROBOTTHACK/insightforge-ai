export type ColumnType = "numerical" | "categorical" | "boolean" | "datetime" | "text";
export type ChartType = "bar" | "horizontal_bar" | "line" | "histogram" | "heatmap" | "pie" | "scatter";
export type AggregationType = "sum" | "mean" | "count" | "min" | "max" | "none";
export type ColumnRole = "metric" | "dimension" | "identifier" | "timestamp" | "text";

export interface ColumnProfile {
  name: string;
  type: ColumnType;
  role: ColumnRole;
  uniqueValues: number;
  missingValues: number;
  recommendedForKpi: boolean;
  recommendedForAxis: boolean;
  warning?: string | null;
}

export interface DatasetMetadata {
  id: string;
  dataset_name: string;
  source_type: string;
  rows: number;
  columns: number;
  schema_json: Record<string, ColumnType>;
  column_profiles: ColumnProfile[];
  preview: Record<string, unknown>[];
}

export interface KPIWidget {
  type: "kpi";
  title: string;
  value: string | number;
  delta?: string | null;
  tone?: "neutral" | "positive" | "negative";
}

export interface ChartWidget {
  type: "chart";
  chartType: ChartType;
  title: string;
  xAxis?: string | null;
  yAxis?: string | null;
  aggregation?: AggregationType;
  insight?: string | null;
  data: Record<string, unknown>[];
}

export interface TableWidget {
  type: "table";
  title: string;
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface FilterWidget {
  type: "filter";
  title: string;
  column: string;
  options: string[];
}

export type DashboardWidget = KPIWidget | ChartWidget | TableWidget | FilterWidget;

export interface DashboardConfig {
  dashboardName: string;
  datasetId: string;
  widgets: DashboardWidget[];
}

export interface DatasetSummary {
  dataset: DatasetMetadata;
  missingValues: Record<string, number>;
  duplicateRows: number;
  statistics: Record<string, unknown>;
  insights: string[];
  recommendedCharts: ChartWidget[];
}

export interface DashboardAskResponse {
  answer: string;
  usedWidgets: string[];
  usedColumns: string[];
}
