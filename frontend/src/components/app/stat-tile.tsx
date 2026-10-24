import { useId, type ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { m } from 'motion/react'
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card'

interface StatTileProps {
  label: string
  value: ReactNode
  hint?: ReactNode
  icon?: LucideIcon
  index?: number
  children?: ReactNode
}

export function StatTile({ label, value, hint, icon: Icon, index = 0, children }: StatTileProps) {
  const labelId = useId()

  return (
    <m.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05, ease: 'easeOut' }}
    >
      <Card role="group" aria-labelledby={labelId} className="h-full gap-2">
        <CardHeader className="flex items-start justify-between gap-2">
          <CardDescription id={labelId}>{label}</CardDescription>
          {Icon && <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />}
        </CardHeader>
        <CardContent>
          <div className="text-xl font-semibold tracking-tight sm:text-2xl">{value}</div>
          {children}
          {hint && <div className="mt-1 text-xs text-muted-foreground">{hint}</div>}
        </CardContent>
      </Card>
    </m.div>
  )
}
