import { render, screen, waitFor, within } from '@testing-library/react'
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
  it('shows one tile per finding, switches time control and opens a finding', async () => {
    window.location.hash = '#/players/1'
    mockFetch([
      ['GET', /\/players\/1$/, () => ({ body: { ...player, game_counts: { rapid: 200, bullet: 700 } } })],
      ['GET', /\/players\/1\/findings$/, () => ({ body: run })],
    ])
    render(<App />)
    // The time control with the most games comes first.
    expect(
      await screen.findByRole('link', { name: /You score worse right after a loss/ }),
    ).toBeInTheDocument()
    expect(screen.getByText(/900 games/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Time trouble.*19%/ })).toBeInTheDocument()
    expect(screen.getByText('Compare with a grandmaster')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('link', { name: /Rapid/ }))
    expect(await screen.findByRole('link', { name: /No clear tilt after a loss/ })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /You score worse/ })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('link', { name: /No clear tilt after a loss/ }))
    expect(
      await screen.findByRole('heading', { name: 'Rapid: no clear tilt after a loss' }),
    ).toBeInTheDocument()
    expect(window.location.hash).toBe('#/players/1/rapid/time_trouble_score')
    await userEvent.click(screen.getByRole('link', { name: /chrisaxm · Rapid/ }))
    expect(await screen.findByRole('link', { name: /No clear tilt after a loss/ })).toBeInTheDocument()
  })

  it('says so when a linked finding is not in the latest analysis', async () => {
    window.location.hash = '#/players/1/blitz/clock_profile'
    mockFetch([
      ['GET', /\/players\/1$/, () => ({ body: { ...player, game_counts: { blitz: 10 } } })],
      ['GET', /\/players\/1\/findings$/, () => ({ body: run })],
    ])
    render(<App />)
    expect(await screen.findByText('This result is not in the latest analysis.')).toBeInTheDocument()
  })

  it('imports all missing months, runs the analysis and lists recent games', async () => {
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
            limit: 30,
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
    expect(await screen.findByText(/Run an analysis after importing/)).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Import from chess.com' }))
    expect(await screen.findByText('Imported 10 new games from 2 months.')).toBeInTheDocument()
    expect(calls.filter((c) => c.url.endsWith('/imports'))).toHaveLength(2)

    await userEvent.click(screen.getByRole('button', { name: 'Analyse my games' }))
    expect(
      await screen.findByRole('link', { name: /You score worse right after a loss/ }),
    ).toBeInTheDocument()

    await userEvent.click(screen.getByRole('link', { name: /Recent games/ }))
    expect(await screen.findByText('Italian Game')).toBeInTheDocument()
  })

  it('adopts a rule from a card, shows its tile and progress, and stops tracking it', async () => {
    window.location.hash = '#/players/1/bullet/clock_profile'
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
    ])
    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Adopt this rule' }))
    expect(await screen.findByText('Tracking ✓')).toBeInTheDocument()
    const post = calls.find((c) => c.method === 'POST')
    expect(JSON.parse(post!.body!)).toMatchObject({ kind: 'clock_checkpoint', min_share: 0.45 })

    await userEvent.click(screen.getByRole('link', { name: /chrisaxm · Bullet/ }))
    // The check of the new rule is not a habit tile of its own: it shows on the rule tile.
    await userEvent.click(await screen.findByRole('link', { name: /Your rule.*93%/ }))
    expect(await screen.findByRole('heading', { name: ruleCheck.title })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Stop tracking' }))
    await waitFor(() => expect(window.location.hash).toBe('#/players/1/bullet'))
    expect(await screen.findByRole('link', { name: /Time trouble/ })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Your rule/ })).not.toBeInTheDocument()
    expect(JSON.parse(calls.find((c) => c.method === 'PATCH')!.body!)).toEqual({ retired: true })
  })

  it('edits notes and reports insights outages', async () => {
    window.location.hash = '#/players/1'
    const calls = mockFetch([
      ['GET', /\/players\/1$/, () => ({ body: { ...player, game_counts: {} } })],
      ['PATCH', /\/players\/1$/, () => ({ body: { ...player, notes: 'main' } })],
      ['GET', /\/players\/1\/findings$/, () => 'network-error'],
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

describe('grandmaster comparison', () => {
  const hikaru = { ...player, id: 2, username: 'hikaru', display_name: 'Hikaru Nakamura', kind: 'reference' }
  const side = (value: number, n: number) => ({ value, ci_low: value - 0.03, ci_high: value + 0.03, n })
  const comparison = {
    player_id: 1,
    reference_id: 2,
    player_run: { ...run, findings: undefined },
    reference_run: { ...run, id: 8, player_id: 2, games_analyzed: 6100 },
    blocks: [
      {
        time_class: 'rapid',
        rows: [
          {
            key: 'time_trouble',
            name: 'Games with time trouble',
            unit: 'share',
            better: 'lower',
            you: side(0.2, 100),
            reference: side(0.1, 50),
            difference: { value: 0.1, ci_low: -0.02, ci_high: 0.22 },
            q_value: 0.3,
            verdict: 'similar',
          },
        ],
      },
      {
        time_class: 'blitz',
        rows: [
          {
            key: 'time_trouble',
            name: 'Games with time trouble',
            unit: 'share',
            better: 'lower',
            you: side(0.31, 900),
            reference: side(0.08, 4000),
            difference: { value: 0.23, ci_low: 0.2, ci_high: 0.26 },
            q_value: 0.001,
            verdict: 'different',
          },
          {
            key: 'onset_move',
            name: 'Time trouble usually starts at move',
            unit: 'move',
            better: null,
            you: { value: 28, ci_low: null, ci_high: null, n: 280 },
            reference: null,
            difference: null,
            q_value: null,
            verdict: 'descriptive',
          },
        ],
      },
    ],
  }

  it('lists grandmasters apart from your own accounts', async () => {
    mockFetch([['GET', /\/players$/, () => ({ body: [player, hikaru] })]])
    render(<App />)
    const gms = await screen.findByRole('region', { name: 'Grandmasters' })
    expect(within(gms).getByText('hikaru')).toBeInTheDocument()
    expect(within(screen.getByRole('region', { name: 'Tracked accounts' })).queryByText('hikaru')).toBeNull()
  })

  it('picks a grandmaster, imports their last 12 months, analyses them and compares', async () => {
    window.location.hash = '#/players/1'
    let analysed = false
    const months = Array.from({ length: 14 }, (_, i) => ({
      month: `2025-${String(i + 1).padStart(2, '0')}`
        .replace('2025-13', '2026-01')
        .replace('2025-14', '2026-02'),
      imported: false,
      complete: false,
      game_count: null,
    }))
    const calls = mockFetch([
      ['GET', /\/players\/1$/, () => ({ body: { ...player, kind: 'player', game_counts: { blitz: 900 } } })],
      ['GET', /\/players\/1\/findings$/, () => ({ body: run })],
      ['GET', /\/players$/, () => ({ body: [player] })],
      ['POST', /\/players$/, () => ({ status: 201, body: hikaru })],
      ['GET', /\/players\/2$/, () => ({ body: { ...hikaru, game_counts: {} } })],
      [
        'GET',
        /\/players\/1\/compare\/2$/,
        () => (analysed ? { body: comparison } : { status: 404, body: { detail: 'no analysis run yet' } }),
      ],
      ['GET', /\/players\/2\/archives$/, () => ({ body: months })],
      [
        'POST',
        /\/players\/2\/imports$/,
        () => ({ body: { month: 'x', fetched: 500, new_games: 500, skipped: false, complete: true } }),
      ],
      [
        'POST',
        /\/players\/2\/runs$/,
        () => {
          analysed = true
          return { status: 201, body: { ...run, player_id: 2 } }
        },
      ],
    ])
    render(<App />)
    await userEvent.click(await screen.findByRole('link', { name: /Compare with a grandmaster/ }))
    await userEvent.click(await screen.findByRole('button', { name: /Hikaru Nakamura/ }))
    expect(JSON.parse(calls.find((c) => c.method === 'POST')!.body!)).toMatchObject({
      username: 'hikaru',
      kind: 'reference',
    })
    await waitFor(() => expect(window.location.hash).toBe('#/players/1/compare/2'))

    await userEvent.click(await screen.findByRole('button', { name: 'Prepare Hikaru Nakamura' }))
    // Opens on blitz, the time control where both have the most games.
    const card = await screen.findByRole('article', { name: 'Games with time trouble' })
    expect(within(card).getByText('31%')).toBeInTheDocument()
    expect(within(card).getByText('8%')).toBeInTheDocument()
    expect(within(card).getByText('Clearly different')).toBeInTheDocument()
    expect(screen.getByText('move 28')).toBeInTheDocument()
    const imports = calls.filter((c) => c.url.endsWith('/players/2/imports'))
    expect(imports).toHaveLength(12)
    expect(JSON.parse(imports[0].body!)).toEqual({ month: '2025-03' })

    await userEvent.click(screen.getByRole('button', { name: 'Rapid' }))
    expect(await screen.findByText('No clear difference')).toBeInTheDocument()
  })

  it('asks you to analyse your own games first', async () => {
    window.location.hash = '#/players/1/compare'
    mockFetch([
      ['GET', /\/players\/1$/, () => ({ body: { ...player, game_counts: {} } })],
      ['GET', /\/players\/1\/findings$/, () => ({ status: 404, body: { detail: 'no analysis run yet' } })],
    ])
    render(<App />)
    expect(await screen.findByText(/Analyse your own games first/)).toBeInTheDocument()
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

describe('methods page', () => {
  it('lists every section and marks the one a card linked to', async () => {
    window.location.hash = '#/methods/clock'
    render(<App />)
    expect(screen.getByRole('heading', { name: 'How it’s measured' })).toBeInTheDocument()
    const clock = screen.getByRole('region', { name: 'Clock profile' })
    expect(clock).toHaveClass('methods__section--active')
    expect(within(clock).getByText('Time trouble')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Statistics and labels' })).not.toHaveClass(
      'methods__section--active',
    )
  })

  it('is linked from the header and from a finding card', async () => {
    window.location.hash = '#/players/1/rapid/time_trouble_score'
    mockFetch([
      ['GET', /\/players\/1$/, () => ({ body: { ...player, game_counts: { rapid: 200, bullet: 700 } } })],
      ['GET', /\/players\/1\/findings$/, () => ({ body: run })],
    ])
    render(<App />)
    expect(screen.getByRole('link', { name: 'How it’s measured' })).toHaveAttribute('href', '#/methods')
    const link = await screen.findByRole('link', { name: 'How is this measured?' })
    expect(link).toHaveAttribute('href', '#/methods/clock')
    await userEvent.click(link)
    expect(await screen.findByRole('region', { name: 'Clock profile' })).toHaveClass(
      'methods__section--active',
    )
  })
})
