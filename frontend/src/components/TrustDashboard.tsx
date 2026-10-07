import { Lightbulb, Zap } from "lucide-react";
import type { QueryResponse } from "../types";
import { ConfidenceMeter } from "./ConfidenceMeter";
import { SourceAttribution } from "./SourceAttribution";
import { TokenHeatmap } from "./TokenHeatmap";
import { formatLatency } from "../utils/formatters";

interface Props {
  result: QueryResponse;
}

export function TrustDashboard({ result }: Props) {
  const explanation = result.explanation;

  return (
    <div className="flex flex-col gap-5 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/50">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {explanation && <ConfidenceMeter score={explanation.confidence_score} level={explanation.calibration} />}
        <div className="grid flex-1 grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <Stat label="Tier used" value={result.tier_used} icon={<Zap className="h-3.5 w-3.5" />} />
          <Stat label="Total latency" value={formatLatency(result.latency_ms)} />
          <Stat label="Retrieval latency" value={formatLatency(result.retrieval_metadata.latency_ms)} />
          <Stat label="Docs used / considered" value={`${result.retrieval_metadata.num_docs_used}/${result.retrieval_metadata.num_docs_considered}`} />
        </div>
      </div>

      {result.retrieval_metadata.degradation_strategy && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
          Dynamic Agent Scheduling degraded this query via <strong>{result.retrieval_metadata.degradation_strategy}</strong> due to resource pressure.
        </div>
      )}

      {result.warnings.length > 0 && (
        <div className="rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-950/40 dark:text-red-300">
          {result.warnings.map((w, i) => (
            <p key={i}>{w}</p>
          ))}
        </div>
      )}

      {explanation && (
        <>
          <div>
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Token saliency</h4>
            <TokenHeatmap tokens={explanation.token_saliency} />
          </div>

          <div>
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Source attribution</h4>
            <SourceAttribution sources={explanation.sources} />
          </div>

          {explanation.alternate_paths.length > 0 && (
            <div>
              <h4 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <Lightbulb className="h-3.5 w-3.5" /> What-if analysis
              </h4>
              <ul className="flex flex-col gap-1.5">
                {explanation.alternate_paths.map((p, i) => (
                  <li key={i} className="rounded-lg bg-white px-3 py-2 text-xs text-slate-600 shadow-sm dark:bg-slate-900 dark:text-slate-300">
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Stat({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <div className="rounded-lg bg-white px-3 py-2 shadow-sm dark:bg-slate-900">
      <p className="flex items-center gap-1 text-[10px] uppercase tracking-wide text-slate-400">
        {icon}
        {label}
      </p>
      <p className="truncate font-semibold text-slate-700 dark:text-slate-200">{value}</p>
    </div>
  );
}
