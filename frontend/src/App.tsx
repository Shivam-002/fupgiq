import { useState } from 'react'
import { m } from 'motion/react'
import { AppHeader } from '@/components/app/app-header'
import { AsyncBoundary } from '@/components/app/async-boundary'
import { ForecastPublished, ForecastPublishedSkeleton } from '@/components/app/forecast-published'
import { ForecastView } from '@/components/app/forecast-view'
import { ParticleBackground } from '@/components/app/particle-background'
import { ViewSkeleton } from '@/components/app/view-skeleton'
import { useForecast } from '@/hooks/use-forecast'
import { LAST_DAY } from '@/lib/config'
import { simulatedAt } from '@/lib/dates'

const fadeIn = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.25, ease: 'easeOut' },
} as const

function App() {
  const [at, setAt] = useState(() => simulatedAt(LAST_DAY))
  const forecast = useForecast(at)

  return (
    <div className="relative isolate flex min-h-svh flex-col bg-muted/40 dark:bg-background">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-background focus:px-3 focus:py-2 focus:text-sm focus:ring-2 focus:ring-ring"
      >
        Skip to content
      </a>
      <ParticleBackground />
      <AppHeader at={at} onDayChange={(day) => setAt(simulatedAt(day))} />

      <main
        id="main"
        className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8"
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-xl font-semibold tracking-tight sm:text-2xl">Day-ahead wind forecast</h1>
            <p className="text-sm text-muted-foreground">
              The latest wind forecast for Great Britain, and how accurate past forecasts have been.
            </p>
          </div>
          <AsyncBoundary query={forecast} skeleton={<ForecastPublishedSkeleton />} errorView={() => null}>
            {(data) => <ForecastPublished publishedAt={data.forecastPublishedAt} />}
          </AsyncBoundary>
        </div>

        <AsyncBoundary query={forecast} skeleton={<ViewSkeleton />} errorTitle="Couldn't load the forecast">
          {(data) => (
            <m.div {...fadeIn}>
              <ForecastView data={data} />
            </m.div>
          )}
        </AsyncBoundary>
      </main>
    </div>
  )
}

export default App
