import { Columns3, FileSpreadsheet, Rows3 } from "lucide-react";
import type { ReactNode } from "react";
import { useDashboardStore } from "../../store/dashboardStore";

export function DatasetSummaryPanel() {
  const { dataset, summary } = useDashboardStore();

  if (!dataset || !summary) {
    return (
      <section className="rounded-lg border border-dashed border-slate-300 bg-white p-5 text-sm text-slate-500">
        Dataset metadata and automatic insights appear here after upload.
      </section>
    );
  }

  const schemaEntries = Object.entries(dataset.schema_json);

  return (
    <section className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex items-center gap-3">
          <FileSpreadsheet className="text-mint" size={22} />
          <div>
            <h2 className="text-base font-semibold">{dataset.dataset_name}</h2>
            <p className="text-sm text-slate-500">{dataset.source_type.toUpperCase()} dataset</p>
          </div>
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3">
          <Metric icon={<Rows3 size={18} />} label="Rows" value={dataset.rows.toLocaleString()} />
          <Metric icon={<Columns3 size={18} />} label="Columns" value={dataset.columns.toLocaleString()} />
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {schemaEntries.slice(0, 12).map(([column, type]) => (
            <span key={column} className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
              {column}: {type}
            </span>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-base font-semibold">Automatic insights</h2>
        <div className="mt-4 grid gap-3">
          {summary.insights.map((insight) => (
            <p key={insight} className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
              {insight}
            </p>
          ))}
        </div>
      </div>
    </section>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-md bg-slate-50 p-3">
      <div className="flex items-center gap-2 text-slate-500">
        {icon}
        <span className="text-xs font-medium uppercase">{label}</span>
      </div>
      <p className="mt-2 text-xl font-semibold">{value}</p>
    </div>
  );
}
