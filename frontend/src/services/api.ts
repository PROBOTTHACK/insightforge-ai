import axios from "axios";
import type { AggregationType, ChartType, ChartWidget, DashboardAskResponse, DashboardConfig, DatasetMetadata, DatasetSummary } from "../types/dashboard";

const DEPLOYED_API_BASE_URL = "https://insightforge-ai-yycn.onrender.com";
const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const configuredApiIsLocal =
  configuredApiBaseUrl?.includes("localhost") || configuredApiBaseUrl?.includes("127.0.0.1");

export const API_BASE_URL =
  configuredApiBaseUrl && !(import.meta.env.PROD && configuredApiIsLocal)
    ? configuredApiBaseUrl
    : DEPLOYED_API_BASE_URL;

const api = axios.create({
  baseURL: API_BASE_URL
});

export async function uploadDataset(file: File): Promise<DatasetMetadata> {
  const formData = new FormData();
  formData.append("file", file);
  const extension = file.name.split(".").pop()?.toLowerCase();
  const endpoint = extension === "xlsx" || extension === "xls" ? "/upload/excel" : extension === "json" ? "/upload/json" : "/upload/csv";
  const { data } = await api.post<DatasetMetadata>(endpoint, formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function getDatasetSummary(datasetId: string): Promise<DatasetSummary> {
  const { data } = await api.get<DatasetSummary>(`/dataset/${datasetId}/summary`);
  return data;
}

export async function generateDashboard(datasetId: string, prompt: string): Promise<DashboardConfig> {
  const { data } = await api.post<DashboardConfig>("/ai/generate-dashboard", {
    datasetId,
    prompt
  });
  return data;
}

export async function buildCustomChart(input: {
  datasetId: string;
  chartType: ChartType;
  xAxis?: string | null;
  yAxis?: string | null;
  aggregation: AggregationType;
  title?: string | null;
}): Promise<ChartWidget> {
  const { data } = await api.post<ChartWidget>("/dashboard/custom-chart", input);
  return data;
}

export async function askDashboard(input: {
  datasetId: string;
  question: string;
  dashboard?: DashboardConfig;
  selectedWidgetIndexes: number[];
}): Promise<DashboardAskResponse> {
  const { data } = await api.post<DashboardAskResponse>("/dashboard/ask", input);
  return data;
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.data?.detail) {
      return typeof error.response.data.detail === "string"
        ? error.response.data.detail
        : JSON.stringify(error.response.data.detail);
    }

    if (error.code === "ERR_NETWORK") {
      return `Could not reach backend at ${API_BASE_URL}. Check Render is awake and CORS allows this frontend.`;
    }

    return error.message;
  }

  return error instanceof Error ? error.message : "Request failed.";
}
