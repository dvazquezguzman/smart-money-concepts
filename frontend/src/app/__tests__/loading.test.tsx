import { describe, it, expect } from 'vitest'
import { renderToString } from 'react-dom/server'
import Loading from '../loading'

describe('Loading page', () => {
  it('renders a spinner and loading text', () => {
    const html = renderToString(<Loading />)
    expect(html).toContain('Loading...')
    expect(html).toContain('animate-spin')
  })
})
