import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import HistoryPage from '../page'

vi.mock('@/lib/api', () => ({
  getPaperHistory: vi.fn(),
  getLiveHistory: vi.fn(),
}))

import { getPaperHistory } from '@/lib/api'

describe('HistoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders two tab buttons', () => {
    vi.mocked(getPaperHistory).mockReturnValue(new Promise(() => {}))

    render(<HistoryPage />)
    expect(screen.getByText('Paper')).toBeTruthy()
    expect(screen.getByText('Live')).toBeTruthy()
  })

  it('renders empty state when no trades', async () => {
    vi.mocked(getPaperHistory).mockResolvedValue([])

    render(<HistoryPage />)

    expect(await screen.findByText('No trades yet.')).toBeTruthy()
  })

  it('renders trade rows with data', async () => {
    vi.mocked(getPaperHistory).mockResolvedValue([
      {
        id: 1,
        symbol: 'BTC/USDT',
        side: 'buy',
        entry_price: 50000,
        exit_price: 51000,
        quantity: 0.1,
        pnl: 100,
        exit_reason: 'target',
        opened_at: '2026-06-01T10:00:00Z',
        status: 'closed',
      },
      {
        id: 2,
        symbol: 'ETH/USDT',
        side: 'sell',
        entry_price: 3000,
        exit_price: 2900,
        quantity: 1,
        pnl: 100,
        exit_reason: 'stop_loss',
        opened_at: '2026-06-01T11:00:00Z',
        status: 'closed',
      },
    ])

    render(<HistoryPage />)

    expect(await screen.findByText('BTC/USDT')).toBeTruthy()
    expect(screen.getByText('ETH/USDT')).toBeTruthy()
    expect(screen.getByText('BUY')).toBeTruthy()
    expect(screen.getByText('SELL')).toBeTruthy()
  })
})
