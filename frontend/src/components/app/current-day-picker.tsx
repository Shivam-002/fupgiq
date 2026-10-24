import { lazy, Suspense, useState } from 'react'
import { CalendarDays } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Skeleton } from '@/components/ui/skeleton'
import { FIRST_DAY, LAST_DAY } from '@/lib/config'
import { fromDay, toDay } from '@/lib/dates'
import { formatDay, formatShortDay } from '@/lib/format'

const loadCalendar = () => import('@/components/ui/calendar')
const Calendar = lazy(() => loadCalendar().then((m) => ({ default: m.Calendar })))

interface CurrentDayPickerProps {
  at: string
  onChange: (day: string) => void
}

export function CurrentDayPicker({ at, onChange }: CurrentDayPickerProps) {
  const [open, setOpen] = useState(false)
  const day = at.slice(0, 10)
  const time = at.slice(11, 16)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        onPointerEnter={loadCalendar}
        onFocus={loadCalendar}
        render={
          <Button
            variant="outline"
            size="sm"
            className="font-normal tabular-nums"
            aria-label={`Current time, ${formatDay(day)} ${time}. Change date`}
          />
        }
      >
        <CalendarDays className="text-muted-foreground" />
        <span className="hidden text-muted-foreground sm:inline">Today</span>
        <span className="sm:hidden">{formatShortDay(day)}</span>
        <span className="hidden sm:inline">{formatDay(day)}</span>
        <span className="text-muted-foreground">{time}</span>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="end">
        <Suspense fallback={<Skeleton className="m-2 h-64 w-56" />}>
          <Calendar
            mode="single"
            selected={fromDay(day)}
            defaultMonth={fromDay(day)}
            startMonth={fromDay(FIRST_DAY)}
            endMonth={fromDay(LAST_DAY)}
            disabled={[{ before: fromDay(FIRST_DAY) }, { after: fromDay(LAST_DAY) }]}
            weekStartsOn={1}
            onSelect={(date) => {
              if (!date) return
              onChange(toDay(date))
              setOpen(false)
            }}
          />
        </Suspense>
      </PopoverContent>
    </Popover>
  )
}
