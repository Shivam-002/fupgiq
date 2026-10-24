import { useState, type ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { ApiError } from '@/lib/api'

// 4xx answers won't change on a retry
const shouldRetry = (failureCount: number, error: Error) =>
  failureCount < 1 && !(error instanceof ApiError && error.status >= 400 && error.status < 500)

export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // historical data, never stale
            staleTime: Infinity,
            refetchOnWindowFocus: false,
            retry: shouldRetry,
          },
        },
      }),
  )

  return (
    <QueryClientProvider client={client}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
    </QueryClientProvider>
  )
}
