import { afterEach, describe, expect, it, vi } from 'vitest'
import { fromDay, simulatedAt, toDay } from './dates'

afterEach(() => vi.useRealTimers())

describe('simulatedAt', () => {
  it('pairs the picked day with the current UK clock time', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-05T08:15:00Z'))
    expect(simulatedAt('2026-01-12')).toBe('2026-01-12T08:15')
  })

  it('uses UK summer time when the real clock is in BST', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-24T09:40:00Z'))
    expect(simulatedAt('2026-01-12')).toBe('2026-01-12T10:40')
  })
})

describe('calendar day conversion', () => {
  it('round-trips a day string', () => {
    expect(toDay(fromDay('2026-01-31'))).toBe('2026-01-31')
  })

  it('gives local midnight of that day', () => {
    const date = fromDay('2026-01-12')
    expect([date.getFullYear(), date.getMonth(), date.getDate(), date.getHours()]).toEqual([
      2026, 0, 12, 0,
    ])
  })
})
