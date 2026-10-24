import { lazy, Suspense, useState } from 'react'
import { ArrowDownUp, ShieldCheck, Target, Wind } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { formatDay, formatGWh, formatMW, formatPercent, formatTime } from '@/lib/format'
import { safetyMargin } from '@/lib/stats'
import type { Forecast, ForecastPoint, TrackRecord } from '@/lib/types'
import { StatTile } from './stat-tile'
import { ChartAreaSkeleton } from './view-skeleton'

// preload chart chunk
const chartModule = import('./day-chart')
const DayChart = lazy(() => chartModule.then((m) => ({ default: m.DayChart })))

export function ForecastView({ data }: { data: Forecast }) {
  const day = formatDay(data.forecastDay)

  return (
    <div className="grid gap-4">
      <DayTiles energyMwh={data.forecastEnergyMwh} trackRecord={data.trackRecord} />

      <Card>
        <CardHeader>
          <CardTitle role="heading" aria-level={2}>
            Wind generation · {day}
          </CardTitle>
          <CardDescription>Hourly wind forecast, in MW</CardDescription>
        </CardHeader>
        <CardContent>
          <Suspense fallback={<ChartAreaSkeleton />}>
            <DayChart points={data.points} />
          </Suspense>
          <ForecastTable day={day} points={data.points} />
        </CardContent>
      </Card>
    </div>
  )
}

// Screen-reader equivalent of the chart
function ForecastTable({ day, points }: { day: string; points: ForecastPoint[] }) {
  return (
    // sr-only doesn't shrink tables
    <div className="sr-only">
      <table>
        <caption>Hourly wind forecast for {day}</caption>
        <thead>
          <tr>
            <th scope="col">Time</th>
            <th scope="col">Forecast</th>
          </tr>
        </thead>
        <tbody>
          {points.map((p) => (
            <tr key={p.time}>
              <th scope="row">{formatTime(p.time)}</th>
              <td>{formatMW(p.forecast)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

interface DayTilesProps {
  energyMwh: number
  trackRecord: TrackRecord | null
}

function DayTiles({ energyMwh, trackRecord }: DayTilesProps) {
  const history = trackRecord ? `Past ${trackRecord.days} days` : 'No past days yet'

  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
      <StatTile index={0} icon={Wind} label="Forecast wind energy" value={formatGWh(energyMwh)} />
      <StatTile
        index={1}
        icon={Target}
        label="Forecast accuracy"
        value={trackRecord ? formatPercent(trackRecord.accuracy) : '—'}
        hint={history}
      />
      <StatTile
        index={2}
        icon={ArrowDownUp}
        label="Typical miss"
        value={trackRecord ? formatGWh(trackRecord.typicalMissMwh) : '—'}
        hint="Average per day"
      />
      <SafetyMarginTile errors={trackRecord?.dailyErrorsMwh ?? null} />
    </div>
  )
}

function SafetyMarginTile({ errors }: { errors: number[] | null }) {
  const [confidence, setConfidence] = useState(90)
  const margin = errors ? safetyMargin(errors, confidence / 100) : null

  return (
    <StatTile
      index={3}
      icon={ShieldCheck}
      label="Safety margin"
      value={margin === null ? '—' : formatGWh(margin)}
      hint={errors ? `${confidence}% chance it's enough` : 'No past days yet'}
    >
      {errors && (
        <Slider
          className="mt-3 mb-2"
          value={[confidence]}
          min={50}
          max={99}
          step={1}
          aria-label="Confidence that the safety margin is enough"
          format={{ style: 'unit', unit: 'percent' }}
          onValueChange={(next) => setConfidence(Array.isArray(next) ? next[0] : next)}
        />
      )}
    </StatTile>
  )
}
