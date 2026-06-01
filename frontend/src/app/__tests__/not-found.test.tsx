import { describe, it, expect } from 'vitest'
import { renderToString } from 'react-dom/server'
import NotFound from '../not-found'

describe('Not Found page', () => {
  it('renders 404 text and dashboard link', () => {
    const html = renderToString(<NotFound />)
    expect(html).toContain('404')
    expect(html).toContain('Page not found')
    expect(html).toContain('dashboard/overview')
  })
})
