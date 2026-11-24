import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DeepPanel } from './DeepPanel'

const status = {
  positions: 3,
  engine: 1,
  engine_game_ids: [1],
  position_game_ids: [1, 2, 3],
  final_game_ids: [],
}

vi.mock('../api', () => ({ deepApi: { status: vi.fn(async () => status) } }))
const runDeep = vi.fn()
vi.mock('../deep/run', () => ({ runDeep: (...a: unknown[]) => runDeep(...a) }))

afterEach(() => runDeep.mockReset())

describe('deep analysis panel', () => {
  it('shows the status, runs with the chosen number of games and reports progress', async () => {
    let finish: (v: typeof status) => void = () => {}
    runDeep.mockImplementation((_id, _opts, onProgress: (p: unknown) => void) => {
      onProgress({ phase: 'engine', done: 2, total: 10, eta: 120 })
      return new Promise((r) => (finish = r))
    })
    const onDone = vi.fn()
    render(<DeepPanel playerId={1} onDone={onDone} />)
    expect(await screen.findByText(/1 games analysed by Stockfish, 3 games read/)).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByRole('combobox'), '100')
    await userEvent.click(screen.getByRole('button', { name: 'Run deep analysis' }))
    expect(runDeep.mock.calls[0][1]).toEqual({ engineGames: 100 })
    expect(await screen.findByText(/Stockfish: your moves: 2 of 10 · about 2 min left/)).toBeInTheDocument()
    finish(status)
    await waitFor(() => expect(onDone).toHaveBeenCalled())
  })

  it('shows an error', async () => {
    runDeep.mockRejectedValue(new Error('insights service unreachable'))
    render(<DeepPanel playerId={1} onDone={() => {}} />)
    await userEvent.click(await screen.findByRole('button', { name: 'Run deep analysis' }))
    expect(await screen.findByText('insights service unreachable')).toBeInTheDocument()
  })
})
