import { vi } from 'vitest'

type Handler = (url: string, init?: RequestInit) => { status?: number; body?: unknown } | 'network-error'

/** Replace global fetch with a router: first handler whose pattern matches wins. */
export function mockFetch(routes: Array<[method: string, pattern: RegExp, handler: Handler]>) {
  const calls: Array<{ method: string; url: string; body?: string }> = []
  const fn = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    const method = init?.method ?? 'GET'
    calls.push({ method, url, body: init?.body as string | undefined })
    const route = routes.find(([m, p]) => m === method && p.test(url))
    if (!route) return new Response(JSON.stringify({ detail: 'not mocked' }), { status: 404 })
    const result = route[2](url, init)
    if (result === 'network-error') throw new TypeError('Failed to fetch')
    const status = result.status ?? 200
    return new Response(status === 204 ? null : JSON.stringify(result.body ?? null), { status })
  })
  vi.stubGlobal('fetch', fn)
  return calls
}
