import { create } from "zustand";
import type { DashboardConfig, DatasetMetadata, DatasetSummary } from "../types/dashboard";

interface DashboardState {
  dataset?: DatasetMetadata;
  summary?: DatasetSummary;
  dashboard?: DashboardConfig;
  prompt: string;
  loading: boolean;
  error?: string;
  setDataset: (dataset?: DatasetMetadata) => void;
  setSummary: (summary?: DatasetSummary) => void;
  setDashboard: (dashboard?: DashboardConfig) => void;
  setPrompt: (prompt: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error?: string) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  prompt: "Build a sales dashboard with monthly trends, top categories, KPIs, and a preview table.",
  loading: false,
  setDataset: (dataset) => set({ dataset }),
  setSummary: (summary) => set({ summary }),
  setDashboard: (dashboard) => set({ dashboard }),
  setPrompt: (prompt) => set({ prompt }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error })
}));
