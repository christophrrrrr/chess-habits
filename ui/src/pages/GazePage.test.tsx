import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { GazePage } from './GazePage'

vi.mock('../gaze/tracker', () => ({
  startTracker: vi.fn(async () => {
    const e = new Error('blocked')
    e.name = 'NotAllowedError'
    throw e
  }),
}))

describe('where you look', () => {
  it('explains the prototype and handles a blocked camera', async () => {
    render(<GazePage />)
    expect(screen.getByText(/never recorded, stored or sent anywhere/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Allow the camera and start' }))
    expect(await screen.findByText(/Camera access was blocked/)).toBeInTheDocument()
  })
})
