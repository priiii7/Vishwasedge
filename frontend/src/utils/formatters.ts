export function formatConfidence(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function formatLatency(ms: number): string {
  return ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(2)}s`;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function calibrationColor(level: "high" | "medium" | "low"): string {
  return { high: "text-trust-high", medium: "text-trust-medium", low: "text-trust-low" }[level];
}
