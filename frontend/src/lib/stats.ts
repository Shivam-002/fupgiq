export function quantile(values: number[], q: number) {
  const sorted = [...values].sort((a, b) => a - b)
  const pos = (sorted.length - 1) * q
  const lo = Math.floor(pos)
  const hi = Math.ceil(pos)
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo)
}

// extra energy that covers the shortfall on `confidence` of past days
export const safetyMargin = (dailyErrors: number[], confidence: number) =>
  Math.max(0, quantile(dailyErrors, confidence))
