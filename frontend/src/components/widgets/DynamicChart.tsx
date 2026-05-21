import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { ChartWidget } from "../../types/dashboard";

const palette = ["#2f9d83", "#d9665b", "#4f6fba", "#d69e2e", "#6b7280", "#8b5cf6"];

export function DynamicChart({ widget }: { widget: ChartWidget }) {
  const xAxis = widget.xAxis ?? "name";
  const yAxis = widget.yAxis ?? "value";

  return (
    <article className="min-h-80 rounded-lg border border-slate-200 bg-white p-4 md:col-span-2">
      <h3 className="text-sm font-semibold">{widget.title}</h3>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart(widget, xAxis, yAxis)}
        </ResponsiveContainer>
      </div>
    </article>
  );
}

function renderChart(widget: ChartWidget, xAxis: string, yAxis: string) {
  if (widget.chartType === "line") {
    return (
      <LineChart data={widget.data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey={xAxis} tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Line dataKey={yAxis} stroke="#2f9d83" strokeWidth={2} type="monotone" />
      </LineChart>
    );
  }

  if (widget.chartType === "pie") {
    return (
      <PieChart>
        <Tooltip />
        <Legend />
        <Pie data={widget.data} dataKey={yAxis} nameKey={xAxis} outerRadius={88}>
          {widget.data.map((_, index) => (
            <Cell key={index} fill={palette[index % palette.length]} />
          ))}
        </Pie>
      </PieChart>
    );
  }

  if (widget.chartType === "scatter") {
    return (
      <ScatterChart data={widget.data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey={xAxis} name={xAxis} tick={{ fontSize: 12 }} />
        <YAxis dataKey={yAxis} name={yAxis} tick={{ fontSize: 12 }} />
        <Tooltip cursor={{ strokeDasharray: "3 3" }} />
        <Scatter data={widget.data} fill="#4f6fba" />
      </ScatterChart>
    );
  }

  return (
    <BarChart data={widget.data} layout={widget.chartType === "horizontal_bar" ? "vertical" : "horizontal"}>
      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
      {widget.chartType === "horizontal_bar" ? (
        <>
          <XAxis type="number" tick={{ fontSize: 12 }} />
          <YAxis dataKey={xAxis} type="category" width={90} tick={{ fontSize: 12 }} />
        </>
      ) : (
        <>
          <XAxis dataKey={xAxis} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
        </>
      )}
      <Tooltip />
      <Bar dataKey={yAxis} fill="#2f9d83" radius={[4, 4, 0, 0]} />
    </BarChart>
  );
}
