const UK_TZ = 'Europe/London'

const timeFormat = new Intl.DateTimeFormat('en-GB', {
  hour: '2-digit',
  minute: '2-digit',
  timeZone: UK_TZ,
})

const dateTimeFormat = new Intl.DateTimeFormat('en-GB', {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
  timeZone: UK_TZ,
})

const dayFormat = new Intl.DateTimeFormat('en-GB', {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  timeZone: UK_TZ,
})

const shortDayFormat = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
  timeZone: UK_TZ,
})

const integer = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 })

// midday UTC so the date never rolls over
function dayToDate(day: string) {
  return new Date(`${day}T12:00:00Z`)
}

export const formatTime = (iso: string) => timeFormat.format(new Date(iso))
export const formatDateTime = (iso: string) => dateTimeFormat.format(new Date(iso))
export const formatDay = (day: string) => dayFormat.format(dayToDate(day))
export const formatShortDay = (day: string) => shortDayFormat.format(dayToDate(day))

export const formatMW = (value: number) => `${integer.format(value)} MW`
export const formatGWh = (mwh: number) => `${(mwh / 1000).toFixed(1)} GWh`
export const formatPercent = (ratio: number) => `${(ratio * 100).toFixed(1)}%`
