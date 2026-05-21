import { Upload } from "lucide-react";
import { useRef } from "react";
import { getApiErrorMessage, getDatasetSummary, uploadDataset } from "../../services/api";
import { useDashboardStore } from "../../store/dashboardStore";

export function DatasetUploader() {
  const inputRef = useRef<HTMLInputElement>(null);
  const { loading, setDataset, setError, setLoading, setSummary, setDashboard } = useDashboardStore();

  async function handleFile(file?: File) {
    if (!file) return;
    setLoading(true);
    setError(undefined);
    setDashboard(undefined);
    try {
      const dataset = await uploadDataset(file);
      const summary = await getDatasetSummary(dataset.id);
      setDataset(dataset);
      setSummary(summary);
    } catch (error) {
      setError(getApiErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="upload" className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">InsightForge AI</h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-600">
            Upload a CSV, Excel, or JSON file and let the backend infer schema, generate analytics, and return renderable dashboard config.
          </p>
        </div>
        <input
          ref={inputRef}
          className="hidden"
          type="file"
          accept=".csv,.xlsx,.xls,.json"
          onChange={(event) => void handleFile(event.target.files?.[0])}
        />
        <button
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={loading}
          onClick={() => inputRef.current?.click()}
          type="button"
        >
          <Upload size={17} />
          {loading ? "Processing" : "Upload dataset"}
        </button>
      </div>
    </section>
  );
}
