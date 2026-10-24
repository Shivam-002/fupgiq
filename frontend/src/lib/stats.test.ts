import { describe, expect, it } from 'vitest'
import { quantile, safetyMargin } from './stats'

describe('quantile', () => {
  it('interpolates between neighbouring values', () => {
    expect(quantile([1, 2, 3, 4], 0.5)).toBe(2.5)
  })

  it('returns the extremes at 0 and 1', () => {
    expect(quantile([5, 1, 9], 0)).toBe(1)
    expect(quantile([5, 1, 9], 1)).toBe(9)
  })

  it('does not reorder the input', () => {
    const values = [3, 1, 2]
    quantile(values, 0.5)
    expect(values).toEqual([3, 1, 2])
  })
})

describe('safetyMargin', () => {
  const dailyErrors = [-10, 0, 10, 20, 30]

  it('grows with the confidence level', () => {
    expect(safetyMargin(dailyErrors, 0.5)).toBe(10)
    expect(safetyMargin(dailyErrors, 0.9)).toBe(26)
  })

  it('is never negative when forecasts ran low', () => {
    expect(safetyMargin([-30, -20, -10], 0.9)).toBe(0)
  })
})
