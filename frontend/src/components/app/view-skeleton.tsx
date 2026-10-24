import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

export function ViewSkeleton() {
  return (
    <div role="status" aria-label="Loading forecast" className="grid gap-4">
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <StatTileSkeleton hint={false} />
        <StatTileSkeleton />
        <StatTileSkeleton />
        <StatTileSkeleton slider />
      </div>
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-64 max-w-[80%]" />
          <Skeleton className="h-4 w-40" />
        </CardHeader>
        <CardContent>
          <ChartAreaSkeleton />
        </CardContent>
      </Card>
    </div>
  )
}

function StatTileSkeleton({ hint = true, slider = false }: { hint?: boolean; slider?: boolean }) {
  return (
    <Card className="h-full gap-2">
      <CardHeader className="flex items-center justify-between">
        <Skeleton className="h-4 w-28 max-w-[70%]" />
        <Skeleton className="size-4 rounded-sm" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-7 w-24 sm:h-8" />
        {slider && <Skeleton className="mt-4 mb-1 h-1 w-full rounded-full" />}
        {hint && <Skeleton className="mt-2 h-3 w-20" />}
      </CardContent>
    </Card>
  )
}

export function ChartAreaSkeleton() {
  return (
    <div aria-hidden className="relative h-88 w-full">
      <div className="absolute inset-x-0 top-1 bottom-13 flex flex-col justify-between">
        {Array.from({ length: 5 }, (_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-3 w-10 shrink-0" />
            <div className="h-px flex-1 bg-border" />
          </div>
        ))}
      </div>

      <div className="absolute top-1 right-0 bottom-13 left-13 animate-pulse">
        <svg className="size-full" viewBox="0 0 100 40" preserveAspectRatio="none">
          <path
            d="M0,30 C12,31 22,24 36,20 S60,13 74,15 S92,9 100,6"
            fill="none"
            stroke="var(--muted-foreground)"
            strokeOpacity={0.2}
            strokeWidth={2}
            strokeLinecap="round"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      </div>

      <div className="absolute inset-x-0 bottom-6 flex justify-between pl-13">
        {Array.from({ length: 8 }, (_, i) => (
          <Skeleton key={i} className={i % 2 ? 'hidden h-3 w-9 sm:block' : 'h-3 w-9'} />
        ))}
      </div>
    </div>
  )
}
