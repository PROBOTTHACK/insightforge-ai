import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { KPIWidget } from "../../types/dashboard";

export function KpiCard({ widget }: { widget: KPIWidget }) {
  const tone = widget.tone ?? "neutral";
  const Icon = tone === "positive" ? ArrowUpRight : tone === "negative" ? ArrowDownRight : Minus;
  const toneClass = tone === "positive" ? "text-mint" : tone === "negative" ? "text-coral" : "text-slate-500";

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-medium text-slate-500">{widget.title}</h3>
        <Icon className={toneClass} size={18} />
      </div>
      <p className="mt-3 break-words text-2xl font-semibold">{widget.value}</p>
      {widget.delta ? <p className={`mt-2 text-xs font-medium ${toneClass}`}>{widget.delta}</p> : null}
    </article>
  );
}
