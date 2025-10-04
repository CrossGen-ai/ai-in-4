import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders welcome message', () => {
    render(<App />)
    expect(screen.getByText(/Welcome/i)).toBeInTheDocument()
  })

  it('renders button', () => {
    render(<App />)
    expect(screen.getByRole('button', { name: /Click me/i })).toBeInTheDocument()
  })
})
