export interface ForecastPoint {
  time: string
  forecast: number
}

export interface TrackRecord {
  days: number
  accuracy: number
  typicalMissMwh: number
  dailyErrorsMwh: number[]
}

export interface Forecast {
  forecastDay: string
  forecastPublishedAt: string
  forecastEnergyMwh: number
  points: ForecastPoint[]
  trackRecord: TrackRecord | null
}
