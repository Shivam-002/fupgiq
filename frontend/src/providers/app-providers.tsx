import type { ReactNode } from 'react'
import { LazyMotion, MotionConfig } from 'motion/react'
import { QueryProvider } from './query-provider'
import { ThemeProvider } from './theme-provider'

// lazy-load motion features
const loadMotionFeatures = () => import('@/lib/motion-features').then((m) => m.default)

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <QueryProvider>
        <LazyMotion features={loadMotionFeatures} strict>
          <MotionConfig reducedMotion="user">{children}</MotionConfig>
        </LazyMotion>
      </QueryProvider>
    </ThemeProvider>
  )
}
