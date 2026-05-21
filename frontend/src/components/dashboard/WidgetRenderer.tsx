import type { DashboardWidget } from "../../types/dashboard";
import { DynamicChart } from "../widgets/DynamicChart";
import { FilterWidget } from "../widgets/FilterWidget";
import { KpiCard } from "../widgets/KpiCard";
import { DataTable } from "../widgets/DataTable";

interface WidgetRendererProps {
  widget: DashboardWidget;
}

export function WidgetRenderer({ widget }: WidgetRendererProps) {
  switch (widget.type) {
    case "kpi":
      return <KpiCard widget={widget} />;
    case "chart":
      return <DynamicChart widget={widget} />;
    case "table":
      return <DataTable widget={widget} />;
    case "filter":
      return <FilterWidget widget={widget} />;
    default:
      return null;
  }
}
