import { describe, expect, it } from 'vitest'
import {
  boardFromFen,
  features,
  fitRidge,
  kingsFromFen,
  predict,
  PUZZLES,
  regionName,
  regionOf,
  smooth,
  squareAt,
  summarise,
  type Point,
} from './model'

const board = { left: 100, top: 50, width: 400, height: 400 } // 50 px squares

describe('ridge regression', () => {
  it('recovers a linear map from features to the screen', () => {
    const xs: number[][] = []
    const ts: Point[] = []
    for (let i = 0; i < 60; i++) {
      const a = Math.sin(i) * 0.2
      const b = Math.cos(i * 1.3) * 0.1
      xs.push([a, b, a * b])
      ts.push({ x: 500 + 2000 * a, y: 300 - 1500 * b })
    }
    const m = fitRidge(xs, ts, 1e-6)
    const p = predict(m, [0.1, -0.05, -0.005])
    expect(p.x).toBeCloseTo(700, 0)
    expect(p.y).toBeCloseTo(375, 0)
  })

  it('smooths towards the new point', () => {
    expect(smooth(null, { x: 10, y: 10 })).toEqual({ x: 10, y: 10 })
    expect(smooth({ x: 0, y: 0 }, { x: 10, y: 20 }, 0.5)).toEqual({ x: 5, y: 10 })
  })
})

describe('features', () => {
  it('moves with the iris inside the eye', () => {
    const lm: Point[] = Array.from({ length: 478 }, () => ({ x: 0.5, y: 0.5 }))
    // Right eye corners 33/133, lids 159/145, iris 468; left eye 263/362, 386/374, iris 473.
    Object.assign(lm, {
      33: { x: 0.3, y: 0.4 },
      133: { x: 0.4, y: 0.4 },
      159: { x: 0.35, y: 0.38 },
      145: { x: 0.35, y: 0.42 },
      468: { x: 0.35, y: 0.4 },
      263: { x: 0.7, y: 0.4 },
      362: { x: 0.6, y: 0.4 },
      386: { x: 0.65, y: 0.38 },
      374: { x: 0.65, y: 0.42 },
      473: { x: 0.65, y: 0.4 },
      1: { x: 0.5, y: 0.5 },
    })
    const centre = features(lm)
    lm[468] = { x: 0.38, y: 0.4 }
    lm[473] = { x: 0.68, y: 0.4 } // both irises move the same way: looking sideways
    const moved = features(lm)
    expect(centre).toHaveLength(14)
    expect(centre[0]).toBeCloseTo(0.5)
    expect(moved[0]).toBeCloseTo(0.2)
  })
})

describe('board geometry', () => {
  it('maps points to squares and 2x2 regions', () => {
    expect(squareAt({ x: 101, y: 449 }, board)).toEqual([0, 0]) // a1
    expect(squareAt({ x: 499, y: 51 }, board)).toEqual([7, 7]) // h8
    expect(squareAt({ x: 99, y: 100 }, board)).toBeNull()
    expect(regionOf([0, 0])).toBe(0)
    expect(regionOf([7, 7])).toBe(15)
    expect(regionName(0)).toBe('a1-b2')
    expect(regionName(15)).toBe('g7-h8')
  })

  it('summarises where the gaze went', () => {
    const atSquare = (file: number, rank: number): Point => ({
      x: board.left + file * 50 + 25,
      y: board.top + (7 - rank) * 50 + 25,
    })
    const points = [
      { x: 0, y: 0 }, // off the board
      ...Array(3).fill(atSquare(6, 7)), // g8, opponent's king zone
      ...Array(2).fill(atSquare(6, 0)), // g1, own king zone
    ]
    const s = summarise(points, board, { own: [6, 0], enemy: [6, 7] })
    expect(s.samples).toBe(6)
    expect(s.onBoard).toBe(5)
    expect(s.opponentHalf).toBeCloseTo(0.6)
    expect(s.enemyKing).toBeCloseTo(0.6)
    expect(s.ownKing).toBeCloseTo(0.4)
    expect(s.firstRegion).toBe(regionOf([6, 7]))
    expect(s.regions.reduce((a, b) => a + b, 0)).toBeCloseTo(1)
  })
})

describe('positions', () => {
  it('reads every puzzle FEN', () => {
    for (const p of PUZZLES) {
      const squares = boardFromFen(p.fen)
      expect(squares).toHaveLength(64)
      const kings = kingsFromFen(p.fen)
      expect(kings.white).not.toBeNull()
      expect(kings.black).not.toBeNull()
      expect(p.move).toMatch(/^[a-h][1-8][a-h][1-8]$/)
    }
    expect(kingsFromFen(PUZZLES[1].fen)).toEqual({ white: [6, 0], black: [6, 7] })
  })
})
