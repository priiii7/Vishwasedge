import type { TokenSaliency } from "../types";

interface Props {
  tokens: TokenSaliency[];
}

function heatColor(importance: number): string {
  // 0 -> transparent, 1 -> strong amber/red
  const alpha = 0.15 + importance * 0.65;
  return `rgba(217, 70, 239, ${alpha.toFixed(2)})`;
}

export function TokenHeatmap({ tokens }: Props) {
  if (tokens.length === 0) {
    return <p className="text-sm text-slate-500">No saliency data available.</p>;
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {tokens.map((t, i) => (
        <span
          key={`${t.token}-${i}`}
          title={`importance: ${(t.importance * 100).toFixed(1)}%`}
          className="rounded-md px-2 py-1 text-sm font-medium text-slate-900 dark:text-slate-50"
          style={{ backgroundColor: heatColor(t.importance) }}
        >
          {t.token}
        </span>
      ))}
    </div>
  );
}
