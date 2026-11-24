import { expect, test, type Page, type Route } from '@playwright/test'
import { clockProfile, contrast } from '../src/test/fixtures'

// The first test uses the real services behind the UI (empty database in CI). The others
// replace the API answers with fixtures, so the main story runs without importing from
// chess.com: CI never depends on an outside service.

const player = {
  id: 1,
  platform: 'chesscom',
  username: 'chrisaxm',
  display_name: null,
  notes: null,
  created_at: '2026-11-12T00:00:00',
  updated_at: '2026-11-12T00:00:00',
  last_imported_at: '2026-11-12T00:00:00',
}

const run = {
  id: 7,
  player_id: 1,
  status: 'done',
  games_analyzed: 900,
  created_at: '2026-11-12T00:00:00',
  finished_at: '2026-11-12T00:00:01',
  findings: [
    { ...contrast, id: 1 },
    { ...clockProfile, id: 2 },
  ],
}

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
}

/** Answers every API call from fixtures: the games service on :8001, insights on :8002. */
async function mockApi(page: Page) {
  await page.route(/:800[12]\//, (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname
    if (path === '/players') return json(route, [player])
    if (path === '/players/1') return json(route, { ...player, game_counts: { bullet: 900 } })
    if (path === '/players/1/findings') return json(route, run)
    if (path === '/players/1/rules') return json(route, [])
    if (path === '/players/1/runs') return json(route, [run])
    return json(route, { detail: 'not mocked in e2e' }, 404)
  })
}

test('home page loads from the real services', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle('Chess Habits')
  await expect(page.getByLabel('chess.com username')).toBeVisible()
  await expect(page.getByText(/games service is not reachable/)).toHaveCount(0)
})

test('main story: account → habit tile → finding page → back', async ({ page }) => {
  await mockApi(page)
  await page.goto('/')
  await page
    .getByRole('link', { name: /chrisaxm/ })
    .first()
    .click()
  await expect(page).toHaveURL(/#\/players\/1$/)

  const tile = page.getByRole('link', { name: /Cost of time trouble.*Time trouble costs you about 110 Elo/ })
  await expect(tile).toBeVisible()
  await tile.click()
  await expect(page).toHaveURL(/#\/players\/1\/bullet\/time_trouble_score$/)
  await expect(
    page.getByRole('heading', { name: 'Bullet: time trouble costs you about 110 Elo' }),
  ).toBeVisible()

  await page.goBack()
  await expect(page).toHaveURL(/#\/players\/1$/)
  await expect(tile).toBeVisible()
})

test('a clear message when the games service is down', async ({ page }) => {
  await page.route(/:8001\//, (route) => route.abort('connectionrefused'))
  await page.goto('/')
  await expect(page.getByText(/games service is not reachable/)).toBeVisible()
})
