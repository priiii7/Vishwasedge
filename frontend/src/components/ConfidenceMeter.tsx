import { useEffect, useState } from "react";
import clsx from "clsx";

interface Props {
  score: number; // 0-1
  level: "high" | "medium" | "low";
}

const LEVEL_STYLES: Record<Props["level"], { ring: string; text: string; label: string }> = {
  high: { ring: "stroke-emerald-500", text: "text-emerald-600 dark:text-emerald-400", label: "High trust" },
  medium: { ring: "stroke-amber-500", text: "text-amber-600 dark:text-amber-400", label: "Medium trust" },
  low: { ring: "stroke-red-500", text: "text-red-600 dark:text-red-400", label: "Low trust" },
};

export function ConfidenceMeter({ score, level }: Props) {
  const [animated, setAnimated] = useState(0);
  const styles = LEVEL_STYLES[level];
  const radius = 42;
  const circumference = 2 * Math.PI * radius;

  useEffect(() => {
    const timeout = setTimeout(() => setAnimated(score), 50);
    return () => clearTimeout(timeout);
  }, [score]);

  const offset = circumference - animated * circumference;

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative h-28 w-28">
        <svg className="h-28 w-28 -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r={radius} className="stroke-slate-200 dark:stroke-slate-800" strokeWidth="8" fill="none" />
          <circle
            cx="50"
            cy="50"
            r={radius}
            className={clsx(styles.ring, "transition-all duration-700 ease-out")}
            strokeWidth="8"
            strokeLinecap="round"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold">{Math.round(score * 100)}%</span>
        </div>
      </div>
      <span className={clsx("text-sm font-medium", styles.text)}>{styles.label}</span>
    </div>
  );
}
