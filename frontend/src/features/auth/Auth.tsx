import { createContext, useContext, useState, type FormEvent, type ReactNode } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { api, ApiError, json } from '../../services/api'
import type { User } from '../../types'

type AuthValue = { user: User | null; setUser: (user: User | null) => void; logout: () => void }
const Context = createContext<AuthValue | null>(null)
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = sessionStorage.getItem('insightflow_user')
    return stored ? (JSON.parse(stored) as User) : null
  })
  function update(next: User | null) {
    setUser(next)
    if (next) sessionStorage.setItem('insightflow_user', JSON.stringify(next))
    else sessionStorage.removeItem('insightflow_user')
  }
  function logout() {
    localStorage.removeItem('insightflow_token')
    update(null)
  }
  return <Context.Provider value={{ user, setUser: update, logout }}>{children}</Context.Provider>
}
export function useAuth() {
  const value = useContext(Context)
  if (!value) throw new Error('Auth provider missing')
  return value
}
export function Protected({ children }: { children: ReactNode }) {
  return localStorage.getItem('insightflow_token') ? children : <Navigate to="/login" replace />
}

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const { setUser } = useAuth()
  const navigate = useNavigate()
  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const result = await api<{ access_token: string; user: User }>(
        `/api/auth/${mode}`,
        json(mode === 'register' ? { name, email, password } : { email, password }),
      )
      localStorage.setItem('insightflow_token', result.access_token)
      setUser(result.user)
      navigate('/app')
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : 'Sign in failed.')
    } finally {
      setBusy(false)
    }
  }
  return (
    <main className="auth-page">
      <div className="auth-side">
        <div className="brand">
          <span className="brand-mark">◈</span> InsightFlow
        </div>
        <div>
          <p className="eyebrow light">SMART BUSINESS ANALYTICS</p>
          <h1>Clarity for every business decision.</h1>
          <p>
            Bring your sales spreadsheet into focus. Understand revenue, products, and customers in
            one calm workspace.
          </p>
        </div>
        <div className="auth-foot">Your numbers. A clearer story.</div>
      </div>
      <div className="auth-form-wrap">
        <form className="auth-card" onSubmit={submit}>
          <p className="eyebrow">WELCOME TO INSIGHTFLOW</p>
          <h2>{mode === 'login' ? 'Sign in to your workspace' : 'Create your account'}</h2>
          <p className="muted">
            {mode === 'login'
              ? 'Pick up where your business left off.'
              : 'Start understanding your sales in minutes.'}
          </p>
          {mode === 'register' && (
            <label>
              Full name
              <input
                required
                minLength={2}
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
              />
            </label>
          )}
          <label>
            Email address
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </label>
          <label>
            Password
            <input
              required
              type="password"
              minLength={mode === 'register' ? 10 : undefined}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
            />
          </label>
          {mode === 'register' && <p className="helper">Use at least 10 characters.</p>}
          {error && (
            <p className="alert" role="alert">
              {error}
            </p>
          )}
          <button className="button primary wide" disabled={busy}>
            {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
          <p className="auth-switch">
            {mode === 'login' ? 'New to InsightFlow?' : 'Already have an account?'}{' '}
            <a href={mode === 'login' ? '/register' : '/login'}>
              {mode === 'login' ? 'Create an account' : 'Sign in'}
            </a>
          </p>
        </form>
      </div>
    </main>
  )
}
