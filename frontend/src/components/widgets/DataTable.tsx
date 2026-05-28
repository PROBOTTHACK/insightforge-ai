import type { TableWidget } from "../../types/dashboard";

export function DataTable({ widget }: { widget: TableWidget }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 md:col-span-2 xl:col-span-4">
      <h3 className="text-sm font-semibold dark:text-slate-100">{widget.title}</h3>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
          <thead>
            <tr>
              {widget.columns.map((column) => (
                <th key={column} className="whitespace-nowrap px-3 py-2 text-left text-xs font-semibold uppercase text-slate-500">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {widget.rows.map((row, index) => (
              <tr key={index}>
                {widget.columns.map((column) => (
                  <td key={column} className="max-w-64 truncate px-3 py-2 text-slate-700 dark:text-slate-300">
                    {String(row[column] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
