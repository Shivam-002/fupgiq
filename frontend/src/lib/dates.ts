const pad = (n: number) => String(n).padStart(2, '0')

const ukClock = new Intl.DateTimeFormat('en-GB', {
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
  timeZone: 'Europe/London',
})

// picked day + current UK time, e.g. 2026-01-12T10:40
export const simulatedAt = (day: string) => `${day}T${ukClock.format(new Date())}`

// calendar uses local midnight
export function fromDay(day: string) {
  const [y, m, d] = day.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export const toDay = (date: Date) =>
  `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
