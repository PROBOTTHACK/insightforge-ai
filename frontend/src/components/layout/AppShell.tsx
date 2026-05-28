import { BarChart3, Database, Sparkles } from "lucide-react";
import { useEffect } from "react";
import type { ReactNode } from "react";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  useEffect(() => {
    document.documentElement.classList.remove("dark");
    localStorage.removeItem("theme");
  }, []);

  return (
    <div className="min-h-screen bg-cloud text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white px-5 py-6 lg:block">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-md bg-mint text-white">
            <Sparkles size={20} />
          </div>
          <div>
            <p className="text-sm font-semibold">InsightForge AI</p>
            <p className="text-xs text-slate-500">Dynamic analytics</p>
          </div>
        </div>

        <nav className="mt-9 space-y-1">
          <a className="flex items-center gap-3 rounded-md bg-slate-100 px-3 py-2 text-sm font-medium" href="#upload">
            <Database size={17} />
            Data workspace
          </a>
          <a className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-600" href="#dashboard">
            <BarChart3 size={17} />
            Dashboard
          </a>
        </nav>
      </aside>

      <main className="lg:pl-64">
        <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">{children}</div>
      </main>
    </div>
  );
}
