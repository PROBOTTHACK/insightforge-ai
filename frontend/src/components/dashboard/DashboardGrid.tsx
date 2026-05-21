import type { DashboardConfig } from "../../types/dashboard";
import { WidgetRenderer } from "./WidgetRenderer";

interface DashboardGridProps {
  dashboard?: DashboardConfig;
}

export function DashboardGrid({ dashboard }: DashboardGridProps) {
  if (!dashboard) {
    return (
      <section id="dashboard" className="rounded-lg border border-dashed border-slate-300 bg-white p-6 text-center text-sm text-slate-500">
        Generate a dashboard to render backend-provided widgets here.
      </section>
    );
  }

  return (
    <section id="dashboard" className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-xl font-semibold">{dashboard.dashboardName}</h2>
        <span className="rounded-md bg-white px-3 py-1 text-xs font-medium text-slate-500 ring-1 ring-slate-200">
          {dashboard.widgets.length} widgets
        </span>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {dashboard.widgets.map((widget, index) => (
          <WidgetRenderer key={`${widget.type}-${index}`} widget={widget} />
        ))}
      </div>
    </section>
  );
}
