import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, getForecast, isRetryable } from './api'

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } })

function stubFetch(impl: (url: string) => Promise<Response>) {
  const fetchMock = vi.fn(impl)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

describe('getForecast', () => {
  it('requests the forecast for the given time and returns the body', async () => {
    const body = { forecastDay: '2026-01-13', points: [] }
    const fetchMock = stubFetch(async () => json(200, body))

    await expect(getForecast('2026-01-12T10:40')).resolves.toEqual(body)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/forecast?at=2026-01-12T10%3A40')
  })

  it('surfaces the backend error code and message', async () => {
    stubFetch(async () =>
      json(503, { error: { code: 'PROVIDER_UNAVAILABLE', message: 'Elexon is down.' } }),
    )

    const error = await getForecast('2026-01-12T10:40').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 503, code: 'PROVIDER_UNAVAILABLE', message: 'Elexon is down.' })
  })

  it('falls back to a generic error when the body is not JSON', async () => {
    stubFetch(async () => new Response('<html>Bad gateway</html>', { status: 502 }))

    await expect(getForecast('2026-01-12T10:40')).rejects.toMatchObject({
      status: 502,
      code: 'UNKNOWN',
      message: 'Something went wrong.',
    })
  })

  it('reports a network failure', async () => {
    stubFetch(async () => {
      throw new TypeError('Failed to fetch')
    })

    await expect(getForecast('2026-01-12T10:40')).rejects.toMatchObject({
      status: 0,
      code: 'NETWORK_ERROR',
    })
  })

  it('lets a cancelled request reject with the original abort error', async () => {
    const controller = new AbortController()
    const abort = new DOMException('Aborted', 'AbortError')
    stubFetch(async () => {
      controller.abort()
      throw abort
    })

    await expect(getForecast('2026-01-12T10:40', controller.signal)).rejects.toBe(abort)
  })
})

describe('isRetryable', () => {
  it.each([
    [new ApiError('down', 503, 'PROVIDER_UNAVAILABLE'), true],
    [new ApiError('offline', 0, 'NETWORK_ERROR'), true],
    [new Error('unknown'), true],
    [new ApiError('bad input', 422, 'INVALID_REQUEST'), false],
    [new ApiError('missing', 404, 'FORECAST_NOT_FOUND'), false],
  ])('%s → %s', (error, expected) => {
    expect(isRetryable(error)).toBe(expected)
  })
})
