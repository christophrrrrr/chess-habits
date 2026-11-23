import { describe, expect, it } from 'vitest'
import { METHODS, methodsSectionFor } from './methods'
import { TILE_NAMES } from './tiles'

describe('methods', () => {
  it('has unique section ids that fit the route', () => {
    const ids = METHODS.map((s) => s.id)
    expect(new Set(ids).size).toBe(ids.length)
    for (const id of ids) expect(id).toMatch(/^[a-z-]+$/)
  })

  it('links every analysis with a tile to a section that exists', () => {
    const ids = new Set(METHODS.map((s) => s.id))
    for (const key of [...Object.keys(TILE_NAMES), 'rule_check']) {
      expect(ids.has(methodsSectionFor(key))).toBe(true)
    }
  })

  it('falls back to the statistics for an analysis it does not know yet', () => {
    expect(methodsSectionFor('something_new')).toBe('statistics')
  })
})
