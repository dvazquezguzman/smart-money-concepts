import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Error from '../error'

describe('Error page', () => {
  it('renders error state with retry button', () => {
    const error = { message: 'Test error message' } as Error
    const retry = () => {}
    render(<Error error={error} unstable_retry={retry} />)
    expect(screen.getByText('Something went wrong')).toBeTruthy()
    expect(screen.getByText('Test error message')).toBeTruthy()
    expect(screen.getByText('Try Again')).toBeTruthy()
    expect(screen.getByText('Return to Dashboard')).toBeTruthy()
  })
})
