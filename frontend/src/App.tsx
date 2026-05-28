import { AIPromptPanel } from "./components/dashboard/AIPromptPanel";
import { DashboardChat } from "./components/dashboard/DashboardChat";
import { DashboardGrid } from "./components/dashboard/DashboardGrid";
import { DatasetSummaryPanel } from "./components/dashboard/DatasetSummaryPanel";
import { ManualChartBuilder } from "./components/dashboard/ManualChartBuilder";
import { AppShell } from "./components/layout/AppShell";
import { DatasetUploader } from "./components/upload/DatasetUploader";
import { useDashboardStore } from "./store/dashboardStore";

export function App() {
  const { dashboard, error } = useDashboardStore();

  return (
    <AppShell>
      <div className="space-y-5">
        <DatasetUploader />
        {error ? <div className="rounded-md border border-coral/30 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
        <DatasetSummaryPanel />
        <ManualChartBuilder />
        <AIPromptPanel />
        <DashboardGrid dashboard={dashboard} />
        <DashboardChat />
      </div>
    </AppShell>
  );
}
