import type { ReactNode } from 'react'
import { QueryError } from './query-error'

interface QueryState<TData> {
  data: TData | undefined
  error: Error | null
  isPending: boolean
  isError: boolean
  isFetching: boolean
  refetch: () => unknown
}

interface AsyncBoundaryProps<TData> {
  query: QueryState<TData>
  skeleton: ReactNode
  children: (data: TData) => ReactNode
  errorView?: (error: Error | null, retry: () => void, retrying: boolean) => ReactNode
  errorTitle?: string
}

export function AsyncBoundary<TData>({
  query,
  skeleton,
  children,
  errorView,
  errorTitle,
}: AsyncBoundaryProps<TData>) {
  const { data, error, isPending, isError, isFetching, refetch } = query
  const retry = () => void refetch()

  if (isPending) return <>{skeleton}</>

  if (isError) {
    if (errorView) return <>{errorView(error, retry, isFetching)}</>
    return <QueryError title={errorTitle} error={error} retrying={isFetching} onRetry={retry} />
  }

  // disabled query
  if (data === undefined) return <>{skeleton}</>

  return <>{children(data)}</>
}
