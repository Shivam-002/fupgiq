import type { Forecast } from './types'

// empty = same origin
const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(message: string, status: number, code: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

// 4xx answers won't change on a retry
export const isRetryable = (error: Error) =>
  !(error instanceof ApiError && error.status >= 400 && error.status < 500)

export async function getForecast(at: string, signal?: AbortSignal): Promise<Forecast> {
  let response: Response
  try {
    response = await fetch(`${API_URL}/api/forecast?${new URLSearchParams({ at })}`, { signal })
  } catch (error) {
    if (signal?.aborted) throw error
    throw new ApiError("Couldn't reach the forecast service.", 0, 'NETWORK_ERROR')
  }

  const body = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(
      body?.error?.message ?? 'Something went wrong.',
      response.status,
      body?.error?.code ?? 'UNKNOWN',
    )
  }
  return body as Forecast
}
