import { Plus } from "lucide-react";
import { useMemo, useState } from "react";
import { buildCustomChart, getApiErrorMessage } from "../../services/api";
import { useDashboardStore } from "../../store/dashboardStore";
import type { AggregationType, ChartType, ColumnProfile, DashboardConfig } from "../../types/dashboard";

const chartTypes: ChartType[] = ["bar", "horizontal_bar", "line", "pie", "histogram", "scatter"];
const aggregations: AggregationType[] = ["sum", "mean", "count", "min", "max", "none"];

export function ManualChartBuilder() {
  const { dataset, dashboard, loading, setDashboard, setError, setLoading } = useDashboardStore();
  const profiles = dataset?.column_profiles ?? [];
  const metricProfiles = profiles.filter((profile) => profile.role === "metric");
  const axisProfiles = profiles.filter((profile) => ["dimension", "timestamp", "identifier"].includes(profile.role));

  const [chartType, setChartType] = useState<ChartType>("bar");
  const [xAxis, setXAxis] = useState("");
  const [yAxis, setYAxis] = useState("");
  const [aggregation, setAggregation] = useState<AggregationType>("sum");
  const [title, setTitle] = useState("");

  const selectedYProfile = useMemo(
    () => profiles.find((profile) => profile.name === yAxis),
    [profiles, yAxis]
  );

  async function handleAddChart() {
    if (!dataset) return;
    setLoading(true);
    setError(undefined);
    try {
      const chart = await buildCustomChart({
        datasetId: dataset.id,
        chartType,
        xAxis: xAxis || null,
        yAxis: yAxis || null,
        aggregation,
        title: title || null
      });
      const nextDashboard: DashboardConfig = dashboard ?? {
        dashboardName: "Custom Dashboard",
        datasetId: dataset.id,
        widgets: []
      };
      setDashboard({
        ...nextDashboard,
        widgets: [...nextDashboard.widgets, chart]
      });
    } catch (error) {
      setError(getApiErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  if (!dataset) {
    return (
      <section className="rounded-lg border border-dashed border-slate-300 bg-white p-5 text-sm text-slate-500">
        Upload a dataset to unlock manual chart controls.
      </section>
    );
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold dark:text-slate-100">Manual chart builder</h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Choose exact columns, aggregation, and chart type. Identifier columns are allowed as axes but blocked from KPI totals.</p>
        </div>
        <button
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={loading || (!xAxis && !yAxis)}
          onClick={() => void handleAddChart()}
          type="button"
        >
          <Plus size={17} />
          Add chart
        </button>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-5">
        <Select label="Chart" value={chartType} onChange={(value) => setChartType(value as ChartType)} options={chartTypes.map((value) => ({ label: value.replace("_", " "), value }))} />
        <ColumnSelect label="X axis" value={xAxis} onChange={setXAxis} profiles={axisProfiles.length ? axisProfiles : profiles} />
        <ColumnSelect label="Y metric" value={yAxis} onChange={setYAxis} profiles={metricProfiles} includeEmpty />
        <Select label="Aggregation" value={aggregation} onChange={(value) => setAggregation(value as AggregationType)} options={aggregations.map((value) => ({ label: value, value }))} />
        <label className="block">
          <span className="text-xs font-semibold uppercase text-slate-500">Title</span>
          <input
            className="mt-1 h-10 w-full rounded-md border border-slate-200 px-3 text-sm outline-none focus:ring-4 focus:ring-mint/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Optional"
            value={title}
          />
        </label>
      </div>

      {selectedYProfile?.warning ? (
        <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{selectedYProfile.warning}</p>
      ) : null}
    </section>
  );
}

function Select({
  label,
  value,
  onChange,
  options
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { label: string; value: string }[];
}) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase text-slate-500">{label}</span>
      <select className="mt-1 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-4 focus:ring-mint/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" onChange={(event) => onChange(event.target.value)} value={value}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function ColumnSelect({
  label,
  value,
  onChange,
  profiles,
  includeEmpty = false
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  profiles: ColumnProfile[];
  includeEmpty?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase text-slate-500">{label}</span>
      <select className="mt-1 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-4 focus:ring-mint/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" onChange={(event) => onChange(event.target.value)} value={value}>
        {includeEmpty ? <option value="">None / count</option> : <option value="">Choose column</option>}
        {profiles.map((profile) => (
          <option key={profile.name} value={profile.name}>
            {profile.name} ({profile.role})
          </option>
        ))}
      </select>
    </label>
  );
}
