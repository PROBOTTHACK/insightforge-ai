import { WandSparkles } from "lucide-react";
import { generateDashboard, getApiErrorMessage } from "../../services/api";
import { useDashboardStore } from "../../store/dashboardStore";

export function AIPromptPanel() {
  const { dataset, loading, prompt, setDashboard, setError, setLoading, setPrompt } = useDashboardStore();

  async function handleGenerate() {
    if (!dataset) return;
    setLoading(true);
    setError(undefined);
    try {
      setDashboard(await generateDashboard(dataset.id, prompt));
    } catch (error) {
      setError(getApiErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold dark:text-slate-100">AI dashboard builder</h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Describe the business view you want. The backend returns widgets, charts, and layout-ready data.</p>
        </div>
        <button
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-mint px-4 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={!dataset || loading}
          onClick={() => void handleGenerate()}
          type="button"
        >
          <WandSparkles size={17} />
          Generate
        </button>
      </div>
      <textarea
        className="mt-4 min-h-24 w-full resize-y rounded-md border border-slate-200 px-3 py-2 text-sm outline-none ring-mint/20 transition placeholder:text-slate-400 focus:ring-4 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
        disabled={!dataset}
        onChange={(event) => setPrompt(event.target.value)}
        value={prompt}
      />
    </section>
  );
}
