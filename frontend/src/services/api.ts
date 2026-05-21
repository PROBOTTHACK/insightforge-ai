import axios from "axios";
import type { DashboardConfig, DatasetMetadata, DatasetSummary } from "../types/dashboard";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
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
