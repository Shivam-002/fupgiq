import { useReducedMotion } from 'motion/react'
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from 'recharts'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'
import { formatMW, formatTime } from '@/lib/format'
import type { ForecastPoint } from '@/lib/types'

const config = {
  forecast: { label: 'Forecast', color: 'var(--chart-2)' },
} satisfies ChartConfig

const axisLabel = { className: 'fill-muted-foreground text-xs' }
const thousands = new Intl.NumberFormat('en-GB')

export function DayChart({ points }: { points: ForecastPoint[] }) {
  const reduceMotion = useReducedMotion()
  const ticks = points.filter((_, i) => i % 3 === 0).map((p) => p.time)

  return (
    <ChartContainer config={config} className="aspect-auto h-88 w-full">
      <LineChart data={points} margin={{ top: 4, right: 12, left: 12, bottom: 20 }}>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey="time"
          ticks={ticks}
          tickFormatter={formatTime}
          tickLine={false}
          axisLine={{ stroke: 'var(--border)' }}
          tickMargin={8}
          minTickGap={24}
          label={{ ...axisLabel, value: 'Time', position: 'insideBottom', offset: -16 }}
        />
        <YAxis
          tickFormatter={(v: number) => thousands.format(v)}
          tickLine={false}
          axisLine={false}
          tickCount={5}
          width={56}
          label={{ ...axisLabel, value: 'Generation (MW)', angle: -90, position: 'insideLeft', offset: -4, style: { textAnchor: 'middle' } }}
        />
        <ChartTooltip
          content={
            <ChartTooltipContent
              labelFormatter={(_, payload) => formatTime(payload[0]?.payload.time)}
              formatter={(value, name, item) => (
                <div className="flex w-full items-center gap-2">
                  <span className="h-2.5 w-1 shrink-0 rounded-xs" style={{ backgroundColor: item.color }} />
                  <span className="text-muted-foreground">{config[name as keyof typeof config]?.label ?? name}</span>
                  <span className="ml-auto pl-4 font-mono font-medium text-foreground tabular-nums">
                    {formatMW(Number(value))}
                  </span>
                </div>
              )}
            />
          }
        />
        <Line
          dataKey="forecast"
          type="monotone"
          stroke="var(--color-forecast)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
          isAnimationActive={!reduceMotion}
        />
      </LineChart>
    </ChartContainer>
  )
}
