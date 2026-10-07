import { useState } from "react";
import { Send, ShieldCheck } from "lucide-react";
import { useChatStore } from "../stores/chatStore";
import { useSubmitQuery } from "../api/queries";
import { TrustDashboard } from "./TrustDashboard";
import { formatLatency } from "../utils/formatters";
import clsx from "clsx";

export function ChatInterface() {
  const { messages, addMessage, updateLastMessage } = useChatStore();
  const [input, setInput] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const submitQuery = useSubmitQuery();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || submitQuery.isPending) return;

    const userMessageId = crypto.randomUUID();
    addMessage({ id: userMessageId, role: "user", content: query, timestamp: Date.now() });
    setInput("");

    const assistantMessageId = crypto.randomUUID();
    addMessage({ id: assistantMessageId, role: "assistant", content: "", timestamp: Date.now() });

    try {
      const result = await submitQuery.mutateAsync({ query });
      updateLastMessage({ content: result.response, queryResponse: result });
      setExpandedId(assistantMessageId);
    } catch (err: any) {
      updateLastMessage({ content: `⚠️ ${err?.response?.data?.detail ?? "Query failed. Is the backend running?"}` });
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-slate-400">
            <ShieldCheck className="h-10 w-10" />
            <p className="max-w-sm text-sm">
              Ask a technical question. Every answer comes with a confidence score, source attribution, and a
              token-saliency explanation.
            </p>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={clsx("flex", m.role === "user" ? "justify-end" : "justify-start")}>
            <div className={clsx("max-w-2xl", m.role === "user" ? "" : "w-full")}>
              <div
                className={clsx(
                  "rounded-2xl px-4 py-2.5 text-sm shadow-sm",
                  m.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
                )}
              >
                {m.content || (
                  <span className="inline-flex items-center gap-1 text-slate-400">
                    <Dot /> <Dot delay="150ms" /> <Dot delay="300ms" />
                  </span>
                )}
              </div>

              {m.role === "assistant" && m.queryResponse && (
                <div className="mt-2">
                  <button
                    onClick={() => setExpandedId(expandedId === m.id ? null : m.id)}
                    className="text-xs font-medium text-indigo-600 hover:underline dark:text-indigo-400"
                  >
                    {expandedId === m.id ? "Hide" : "Show"} trust dashboard · {formatLatency(m.queryResponse.latency_ms)}
                  </button>
                  {expandedId === m.id && (
                    <div className="mt-2">
                      <TrustDashboard result={m.queryResponse} />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-slate-200 p-4 dark:border-slate-800">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. What is the safe operating pressure for well W-123?"
          className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900"
        />
        <button
          type="submit"
          disabled={submitQuery.isPending || !input.trim()}
          className="flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:opacity-50"
        >
          <Send className="h-4 w-4" /> Ask
        </button>
      </form>
    </div>
  );
}

function Dot({ delay = "0ms" }: { delay?: string }) {
  return <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: delay }} />;
}
