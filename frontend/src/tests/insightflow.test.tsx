import '@testing-library/jest-dom/vitest'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthPage, AuthProvider } from '../features/auth/Auth'
import { Empty } from '../components/UI'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('core UI states', () => {
  it('requires a valid email and password before registration', () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <AuthPage mode="register" />
        </MemoryRouter>
      </AuthProvider>,
    )
    const button = screen.getByRole('button', { name: 'Create account' })
    fireEvent.click(button)
    expect(screen.getByLabelText('Email address')).toBeInvalid()
  })
  it('shows a useful sign-in error returned by the API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({
          error: { code: 'INVALID_CREDENTIALS', message: 'Email or password is incorrect.' },
        }),
      }),
    )
    render(
      <AuthProvider>
        <MemoryRouter>
          <AuthPage mode="login" />
        </MemoryRouter>
      </AuthProvider>,
    )
    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'owner@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'incorrect-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect.')
  })
  it('explains an empty dataset view', () => {
    render(
      <Empty
        title="No datasets yet"
        detail="Upload a sales spreadsheet to start building your dashboard."
      />,
    )
    expect(screen.getByText('No datasets yet')).toBeInTheDocument()
  })
})
