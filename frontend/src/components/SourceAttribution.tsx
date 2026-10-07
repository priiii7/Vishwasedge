import clsx from "clsx";
import { FileText } from "lucide-react";
import type { SourceAttribution as SourceAttributionType } from "../types";
import { formatConfidence } from "../utils/formatters";

interface Props {
  sources: SourceAttributionType[];
}

export function SourceAttribution({ sources }: Props) {
  if (sources.length === 0) {
    return <p className="text-sm text-slate-500">No grounded sources met the confidence threshold.</p>;
  }

  return (
    <div className="flex flex-col gap-2">
      {sources.map((s) => (
        <div
          key={s.chunk_id}
          className="rounded-lg border border-slate-200 bg-white p-3 text-sm shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="mb-1 flex items-center justify-between gap-2">
            <span className="flex items-center gap-1.5 truncate font-medium text-slate-700 dark:text-slate-200">
              <FileText className="h-3.5 w-3.5 shrink-0 text-slate-400" />
              {s.source || "Unknown source"}
            </span>
            <span
              className={clsx(
                "shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold",
                s.confidence >= 0.85
                  ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300"
                  : "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300"
              )}
            >
              {formatConfidence(s.confidence)}
            </span>
          </div>
          <p className="text-slate-500 dark:text-slate-400">{s.reason}</p>
          <p className="mt-1.5 line-clamp-2 text-slate-600 dark:text-slate-300">{s.excerpt}</p>
        </div>
      ))}
    </div>
  );
}
