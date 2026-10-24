import { describe, expect, it } from 'vitest'
import { formatDateTime, formatDay, formatGWh, formatMW, formatPercent, formatTime } from './format'

describe('number formatting', () => {
  it('formats energy, power and percentages', () => {
    expect(formatGWh(242_900)).toBe('242.9 GWh')
    expect(formatMW(10_240)).toBe('10,240 MW')
    expect(formatPercent(0.8456)).toBe('84.6%')
  })
})

describe('UK time formatting', () => {
  it('shows times in UK local time', () => {
    expect(formatTime('2026-01-13T00:00:00Z')).toBe('00:00')
    expect(formatTime('2026-07-13T00:00:00Z')).toBe('01:00')
  })

  it('keeps the calendar day of a YYYY-MM-DD string', () => {
    expect(formatDay('2026-01-31')).toContain('31 Jan 2026')
  })

  it('formats a publish timestamp', () => {
    expect(formatDateTime('2026-01-31T07:30:00Z')).toContain('31 Jan')
    expect(formatDateTime('2026-01-31T07:30:00Z')).toContain('07:30')
  })
})
