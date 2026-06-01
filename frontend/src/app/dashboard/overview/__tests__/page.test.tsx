import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import OverviewPage from '../page'

vi.mock('@/lib/api', () => ({
  getPaperStatus: vi.fn(),
  getLiveStatus: vi.fn(),
  getStrategies: vi.fn(),
  getHealth: vi.fn(),
}))

import { getPaperStatus, getLiveStatus, getStrategies, getHealth } from '@/lib/api'

describe('OverviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    vi.mocked(getPaperStatus).mockReturnValue(new Promise(() => {}))
    vi.mocked(getLiveStatus).mockReturnValue(new Promise(() => {}))
    vi.mocked(getStrategies).mockReturnValue(new Promise(() => {}))
    vi.mocked(getHealth).mockReturnValue(new Promise(() => {}))

    const { container } = render(<OverviewPage />)
    expect(container.querySelector('.animate-spin')).toBeTruthy()
  })

  it('renders stat cards with data', async () => {
    vi.mocked(getPaperStatus).mockResolvedValue({
      balance: 10000,
      equity: 10500,
      realized_pnl: 250,
      open_positions: 2,
      running: true,
    })
    vi.mocked(getLiveStatus).mockResolvedValue({
      connected: true,
      running: true,
      exchange: 'binance',
      open_positions: 1,
    })
    vi.mocked(getStrategies).mockResolvedValue([{ id: 1, name: 'test' }])
    vi.mocked(getHealth).mockResolvedValue({ status: 'ok' })

    render(<OverviewPage />)

    expect(await screen.findByText('Overview')).toBeTruthy()
    expect(screen.getByText('Paper Balance')).toBeTruthy()
    expect(screen.getByText('Strategies')).toBeTruthy()
  })

  it('renders error banner on fetch failure', async () => {
    vi.mocked(getPaperStatus).mockRejectedValue(new Error('API down'))
    vi.mocked(getLiveStatus).mockRejectedValue(new Error('API down'))
    vi.mocked(getStrategies).mockRejectedValue(new Error('API down'))
    vi.mocked(getHealth).mockRejectedValue(new Error('API down'))

    render(<OverviewPage />)

    expect(await screen.findByText('Failed to fetch overview data')).toBeTruthy()
  })
})
