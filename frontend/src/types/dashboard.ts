export type ColumnType = "numerical" | "categorical" | "boolean" | "datetime" | "text";
export type ChartType = "bar" | "horizontal_bar" | "line" | "histogram" | "heatmap" | "pie" | "scatter";

export interface DatasetMetadata {
  id: string;
  dataset_name: string;
  source_type: string;
  rows: number;
  columns: number;
  schema_json: Record<string, ColumnType>;
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
