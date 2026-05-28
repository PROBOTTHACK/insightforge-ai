import type { DashboardConfig } from "../../types/dashboard";
import { useDashboardStore } from "../../store/dashboardStore";
import { WidgetRenderer } from "./WidgetRenderer";

interface DashboardGridProps {
  dashboard?: DashboardConfig;
}

export function DashboardGrid({ dashboard }: DashboardGridProps) {
  const { selectedWidgetIndexes, toggleSelectedWidget } = useDashboardStore();

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
        <div className="flex items-center gap-2">
          <span className="rounded-md bg-white px-3 py-1 text-xs font-medium text-slate-500 ring-1 ring-slate-200">
            {dashboard.widgets.length} widgets
          </span>
          <button className="rounded-md bg-white px-3 py-1 text-xs font-medium text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50" onClick={() => window.print()} type="button">
            Export PDF
          </button>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {dashboard.widgets.map((widget, index) => (
          <div
            className={`${gridSpanFor(widget.type)} rounded-lg transition ${
              selectedWidgetIndexes.includes(index) ? "outline outline-2 outline-mint outline-offset-2" : "outline-none"
            }`}
            key={`${widget.type}-${index}`}
            onClick={() => toggleSelectedWidget(index)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") toggleSelectedWidget(index);
            }}
            role="button"
            tabIndex={0}
          >
            <WidgetRenderer widget={widget} />
          </div>
        ))}
      </div>
    </section>
  );
}

function gridSpanFor(type: string) {
  if (type === "table") return "md:col-span-2 xl:col-span-4";
  if (type === "chart") return "md:col-span-2";
  return "";
}
