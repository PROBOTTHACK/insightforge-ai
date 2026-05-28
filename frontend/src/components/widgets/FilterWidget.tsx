import type { FilterWidget as FilterWidgetType } from "../../types/dashboard";

export function FilterWidget({ widget }: { widget: FilterWidgetType }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <h3 className="text-sm font-semibold dark:text-slate-100">{widget.title}</h3>
      <select className="mt-4 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-4 focus:ring-mint/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100">
        <option>All {widget.column}</option>
        {widget.options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    </article>
  );
}
