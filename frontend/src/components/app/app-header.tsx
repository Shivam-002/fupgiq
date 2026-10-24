import { Wind } from 'lucide-react'
import { CurrentDayPicker } from './current-day-picker'
import { ThemeToggle } from './theme-toggle'

interface AppHeaderProps {
  at: string
  onDayChange: (day: string) => void
}

export function AppHeader({ at, onDayChange }: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-3 px-4 sm:px-6 lg:px-8">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Wind className="size-4" />
        </div>
        <div className="hidden min-w-0 leading-tight min-[360px]:block">
          <p className="truncate text-sm font-semibold">Wind Forecast Monitor</p>
          <p className="hidden truncate text-xs text-muted-foreground sm:block">Great Britain · wind power</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <CurrentDayPicker at={at} onChange={onDayChange} />
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
