import { Send, X } from "lucide-react";
import { useMemo, useState } from "react";
import { askDashboard, getApiErrorMessage } from "../../services/api";
import { useDashboardStore } from "../../store/dashboardStore";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function DashboardChat() {
  const { dataset, dashboard, selectedWidgetIndexes, toggleSelectedWidget, clearSelectedWidgets, setError } = useDashboardStore();
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [asking, setAsking] = useState(false);

  const showMentions = question.includes("@") && Boolean(dashboard?.widgets.length);
  const selectedTitles = useMemo(
    () => selectedWidgetIndexes.map((index) => dashboard?.widgets[index]?.title ?? `Widget ${index + 1}`),
    [dashboard, selectedWidgetIndexes]
  );

  async function handleAsk() {
    if (!dataset || !question.trim()) return;
    setAsking(true);
    setError(undefined);
    const nextMessages: Message[] = [...messages, { role: "user", content: question }];
    setMessages(nextMessages);
    try {
      const response = await askDashboard({
        datasetId: dataset.id,
        question,
        dashboard,
        selectedWidgetIndexes
      });
      setMessages([...nextMessages, { role: "assistant", content: response.answer }]);
      setQuestion("");
    } catch (error) {
      setError(getApiErrorMessage(error));
    } finally {
      setAsking(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold dark:text-slate-100">Ask this dashboard</h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Select widgets or type @ to choose widget context, then ask Gemini about the dashboard.</p>
        </div>
        {selectedWidgetIndexes.length ? (
          <button className="inline-flex h-9 items-center gap-2 rounded-md border border-slate-200 px-3 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-300" onClick={clearSelectedWidgets} type="button">
            <X size={15} />
            Clear
          </button>
        ) : null}
      </div>

      {selectedTitles.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {selectedTitles.map((title, offset) => (
            <span className="rounded-md bg-mint/10 px-2.5 py-1 text-xs font-medium text-mint" key={`${title}-${offset}`}>
              @{title}
            </span>
          ))}
        </div>
      ) : null}

      <div className="mt-4 max-h-60 space-y-3 overflow-y-auto">
        {messages.length ? (
          messages.map((message, index) => (
            <div className={`rounded-md px-3 py-2 text-sm ${message.role === "user" ? "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100" : "bg-mint/10 text-slate-700 dark:text-slate-200"}`} key={index}>
              {message.content}
            </div>
          ))
        ) : (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500 dark:bg-slate-800 dark:text-slate-400">
            Try: “Why did this chart spike?” or “Compare the selected widgets.”
          </p>
        )}
      </div>

      <div className="relative mt-4">
        {showMentions ? (
          <div className="absolute bottom-12 left-0 z-10 max-h-52 w-full overflow-y-auto rounded-md border border-slate-200 bg-white p-2 shadow-lg dark:border-slate-700 dark:bg-slate-900">
            {dashboard?.widgets.map((widget, index) => (
              <button
                className="block w-full rounded-md px-3 py-2 text-left text-sm hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
                key={`${widget.type}-${index}`}
                onClick={() => toggleSelectedWidget(index)}
                type="button"
              >
                @{widget.title ?? `${widget.type} ${index + 1}`}
              </button>
            ))}
          </div>
        ) : null}
        <div className="flex gap-2">
          <input
            className="h-11 flex-1 rounded-md border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-4 focus:ring-mint/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            disabled={!dataset}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void handleAsk();
            }}
            placeholder="Ask about selected widgets, or type @"
            value={question}
          />
          <button className="inline-flex h-11 items-center justify-center rounded-md bg-mint px-4 text-white disabled:cursor-not-allowed disabled:opacity-60" disabled={!dataset || asking || !question.trim()} onClick={() => void handleAsk()} type="button">
            <Send size={17} />
          </button>
        </div>
      </div>
    </section>
  );
}
