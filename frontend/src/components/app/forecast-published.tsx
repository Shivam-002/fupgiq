import { FileClock } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDateTime } from '@/lib/format'

export function ForecastPublished({ publishedAt }: { publishedAt: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-card ring-1 ring-foreground/10">
        <FileClock className="size-4 text-muted-foreground" />
      </div>
      <div className="leading-tight">
        <p className="text-xs text-muted-foreground">Forecast published</p>
        <p className="font-medium whitespace-nowrap tabular-nums">{formatDateTime(publishedAt)}</p>
      </div>
    </div>
  )
}

export function ForecastPublishedSkeleton() {
  return (
    <div aria-hidden className="flex items-center gap-3">
      <Skeleton className="size-9 rounded-lg" />
      <div className="grid gap-1.5">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-4 w-32" />
      </div>
    </div>
  )
}
