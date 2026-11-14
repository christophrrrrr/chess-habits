import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { mockFetch } from '../test/fetchMock'
import { clockProfile, contrast, rule, ruleCheck } from '../test/fixtures'

const player = {
  id: 1,
  platform: 'chesscom',
  username: 'chrisaxm',
  display_name: null,
  notes: null,
  created_at: '2026-11-12T00:00:00',
  updated_at: '2026-11-12T00:00:00',
  last_imported_at: null,
}

const run = {
  id: 7,
  player_id: 1,
  status: 'done',
  games_analyzed: 300,
  created_at: '2026-11-12T00:00:00',
  finished_at: '2026-11-12T00:00:01',
  findings: [
    {
      ...contrast,
      id: 1,
      time_class: 'rapid',
      label: 'no_effect',
      title: 'Rapid: no clear tilt after a loss',
    },
    { ...clockProfile, id: 3 },
    { ...contrast, id: 2, title: 'Bullet: you score worse right after a loss' },
  ],
}

afterEach(() => {
  vi.unstubAllGlobals()
  window.location.hash = ''
})

describe('players page', () => {
  it('lists players and adds a new one', async () => {
    const calls = mockFetch([
      ['GET', /\/players$/, () => ({ body: [player] })],
      ['POST', /\/players$/, () => ({ status: 201, body: { ...player, id: 2, username: 'magnus' } })],
    ])
    render(<App />)
    expect(await screen.findByText('chrisaxm')).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText('chess.com username'), 'Magnus')
    await userEvent.click(screen.getByRole('button', { name: 'Add' }))
    await waitFor(() => expect(window.location.hash).toBe('#/players/2'))
    const post = calls.find((c) => c.method === 'POST')
    expect(JSON.parse(post!.body!)).toMatchObject({ username: 'Magnus', platform: 'chesscom' })
  })

  it('shows the API error when adding fails', async () => {
    mockFetch([
      ['GET', /\/players$/, () => ({ body: [] })],
      [
        'POST',
        /\/players$/,
        () => ({ status: 422, body: { detail: 'no chess.com account with that name' } }),
      ],
    ])
    render(<App />)
    expect(await screen.findByText(/No accounts yet/)).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('chess.com username'), 'nobody')
    await userEvent.click(screen.getByRole('button', { name: 'Add' }))
    expect(await screen.findByText('no chess.com account with that name')).toBeInTheDocument()
  })

  it('shows a clear message when the games service is down', async () => {
    mockFetch([['GET', /\/players$/, () => 'network-error']])
    render(<App />)
    expect(await screen.findByText(/games service is not reachable/)).toBeInTheDocument()
  })

  it('deletes a player after confirmation', async () => {
    vi.stubGlobal('confirm', () => true)
    const calls = mockFetch([
      ['GET', /\/players$/, () => ({ body: [player] })],
      ['DELETE', /\/players\/1$/, () => ({ status: 204 })],
    ])
    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Delete chrisaxm' }))
    await waitFor(() => expect(calls.some((c) => c.method === 'DELETE')).toBe(true))
  })
})

describe('player page', () => {
  it('shows findings per time control and switches tabs', async () => {
    window.location.hash = '#/players/1'
    mockFetch([
      ['GET', /\/players\/1$/, () => ({ body: { ...player, game_counts: { rapid: 200, bullet: 700 } } })],
      ['GET', /\/players\/1\/findings$/, () => ({ body: run })],
      ['GET', /\/players\/1\/games/, () => ({ body: { items: [], total: 0, limit: 15, offset: 0 } })],
    ])
    render(<App />)
    expect(await screen.findByText('Bullet: you score worse right after a loss')).toBeInTheDocument()
    expect(screen.getByText(/900 games/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: 'Rapid' }))
    expect(screen.getByText('Rapid: no clear tilt after a loss')).toBeInTheDocument()
    expect(screen.queryByText('Bullet: you score worse right after a loss')).not.toBeInTheDocument()
  })

  it('imports all missing months and runs the analysis', async () => {
    window.location.hash = '#/players/1'
    const calls = mockFetch([
      ['GET', /\/players\/1$/, () => ({ body: { ...player, game_counts: { blitz: 3 } } })],
      ['GET', /\/players\/1\/findings$/, () => ({ status: 404, body: { detail: 'no analysis run yet' } })],
      [
        'GET',
        /\/players\/1\/games/,
        () => ({
          body: {
            items: [
              {
                id: 5,
                url: 'https://www.chess.com/game/live/1',
                time_class: 'blitz',
                time_control: '180',
                ended_at: '2026-11-01T10:00:00',
                player_color: 'white',
                player_rating: 2380,
                opponent_username: 'opp',
                opponent_rating: 2300,
                result: 'win',
                result_detail: 'win',
                eco: 'C50',
                opening: 'Italian Game',
                ply_count: 40,
              },
            ],
            total: 1,
            limit: 15,
            offset: 0,
          },
        }),
      ],
      [
        'GET',
        /\/archives$/,
        () => ({
          body: [
            { month: '2026-09', imported: true, complete: true, game_count: 10 },
            { month: '2026-10', imported: false, complete: false, game_count: null },
            { month: '2026-11', imported: false, complete: false, game_count: null },
          ],
        }),
      ],
      [
        'POST',
        /\/imports$/,
        () => ({ body: { month: 'x', fetched: 5, new_games: 5, skipped: false, complete: true } }),
      ],
      ['POST', /\/runs$/, () => ({ status: 201, body: run })],
    ])
    render(<App />)
    expect(await screen.findByText('Italian Game')).toBeInTheDocument()
    expect(screen.getByText(/Run an analysis after importing/)).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Import from chess.com' }))
    expect(await screen.findByText('Imported 10 new games from 2 months.')).toBeInTheDocument()
    expect(calls.filter((c) => c.url.endsWith('/imports'))).toHaveLength(2)

    await userEvent.click(screen.getByRole('button', { name: 'Analyse my games' }))
    expect(await screen.findByText('Bullet: you score worse right after a loss')).toBeInTheDocument()
  })

  it('adopts a rule from a card, shows its progress and stops tracking it', async () => {
    window.location.hash = '#/players/1'
    const calls = mockFetch([
      ['GET', /\/players\/1$/, () => ({ body: { ...player, game_counts: { bullet: 700 } } })],
      [
        'GET',
        /\/players\/1\/findings$/,
        () => ({ body: { ...run, findings: [{ ...clockProfile, id: 3 }, ruleCheck] } }),
      ],
      ['GET', /\/players\/1\/rules$/, () => ({ body: [] })],
      ['POST', /\/players\/1\/rules$/, () => ({ status: 201, body: rule })],
      ['PATCH', /\/rules\/11$/, () => ({ body: { ...rule, retired_at: '2026-11-12T12:00:00' } })],
      ['GET', /\/players\/1\/games/, () => ({ body: { items: [], total: 0, limit: 15, offset: 0 } })],
    ])
    render(<App />)
    // The check belongs to a rule that is not active (yet): it is not shown on its own.
    await userEvent.click(await screen.findByRole('button', { name: 'Adopt this rule' }))
    expect(await screen.findByRole('heading', { name: ruleCheck.title })).toBeInTheDocument()
    expect(screen.getByText('Tracking ✓')).toBeInTheDocument()
    const post = calls.find((c) => c.method === 'POST')
    expect(JSON.parse(post!.body!)).toMatchObject({ kind: 'clock_checkpoint', min_share: 0.45 })

    await userEvent.click(screen.getByRole('button', { name: 'Stop tracking' }))
    await waitFor(() =>
      expect(screen.queryByRole('heading', { name: ruleCheck.title })).not.toBeInTheDocument(),
    )
    expect(JSON.parse(calls.find((c) => c.method === 'PATCH')!.body!)).toEqual({ retired: true })
  })

  it('edits notes and reports insights outages', async () => {
    window.location.hash = '#/players/1'
    const calls = mockFetch([
      ['GET', /\/players\/1$/, () => ({ body: { ...player, game_counts: {} } })],
      ['PATCH', /\/players\/1$/, () => ({ body: { ...player, notes: 'main' } })],
      ['GET', /\/players\/1\/findings$/, () => 'network-error'],
      ['GET', /\/players\/1\/games/, () => ({ body: { items: [], total: 0, limit: 15, offset: 0 } })],
      [
        'GET',
        /\/archives$/,
        () => ({ status: 503, body: { detail: 'chess.com is not reachable right now' } }),
      ],
    ])
    render(<App />)
    expect(await screen.findByText(/insights service is not reachable/)).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Edit notes' }))
    await userEvent.type(screen.getByLabelText('Notes'), 'main')
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(calls.some((c) => c.method === 'PATCH')).toBe(true))

    await userEvent.click(screen.getByRole('button', { name: 'Import from chess.com' }))
    expect(await screen.findByText('chess.com is not reachable right now')).toBeInTheDocument()
  })
})

describe('cold start banner', () => {
  it('explains slow requests while servers wake up', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    let release: (v: Response) => void = () => {}
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise<Response>((resolve) => (release = resolve))),
    )
    render(<App />)
    await vi.advanceTimersByTimeAsync(4_500)
    expect(await screen.findByRole('status')).toHaveTextContent('Waking up the servers')
    release(new Response(JSON.stringify([]), { status: 200 }))
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument())
    vi.useRealTimers()
  })
})
