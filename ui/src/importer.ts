import { gamesApi } from './api'

export interface ImportProgress {
  done: number
  total: number
  month: string
  newGames: number
}

/**
 * Imports every chess.com month that is not fully imported yet, one request per month.
 * `lastMonths` limits it to the most recent months (grandmasters: a year is plenty).
 */
export async function importMissing(
  playerId: number,
  onProgress: (p: ImportProgress) => void,
  lastMonths?: number,
): Promise<{ newGames: number; months: number }> {
  let archives = await gamesApi.listArchives(playerId)
  if (lastMonths) archives = [...archives].sort((a, b) => a.month.localeCompare(b.month)).slice(-lastMonths)
  const months = archives.filter((m) => !m.complete)
  let newGames = 0
  for (const [i, m] of months.entries()) {
    onProgress({ done: i, total: months.length, month: m.month, newGames })
    newGames += (await gamesApi.importMonth(playerId, m.month)).new_games
  }
  return { newGames, months: months.length }
}

/** How many months of a grandmaster's history are imported. */
export const REFERENCE_MONTHS = 12
