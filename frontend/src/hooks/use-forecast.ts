import { useQuery } from '@tanstack/react-query'
import { getForecast } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'

export function useForecast(at: string) {
  return useQuery({
    queryKey: queryKeys.forecast(at),
    queryFn: ({ signal }) => getForecast(at, signal),
  })
}
