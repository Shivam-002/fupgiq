import { AlertCircle, RotateCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface QueryErrorProps {
  title?: string
  error?: Error | null
  retrying?: boolean
  onRetry: () => void
}

export function QueryError({
  title = 'Something went wrong',
  error,
  retrying = false,
  onRetry,
}: QueryErrorProps) {
  return (
    <Card role="alert" className="min-h-112 justify-center">
      <CardContent className="flex flex-col items-center gap-4 py-10 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-destructive/10 ring-8 ring-destructive/5">
          <AlertCircle className="size-6 text-destructive" />
        </div>
        <div className="max-w-md space-y-1.5">
          <p className="text-base font-semibold">{title}</p>
          {error?.message && <p className="text-sm text-muted-foreground">{error.message}</p>}
        </div>
        <Button variant="outline" onClick={onRetry} disabled={retrying} className="mt-1">
          <RotateCw className={cn(retrying && 'animate-spin')} />
          {retrying ? 'Trying again…' : 'Try again'}
        </Button>
      </CardContent>
    </Card>
  )
}
