import { lazy, Suspense, useEffect, useState, type FormEvent } from 'react'
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from 'react-router-dom'
import { AuthPage, AuthProvider, Protected, useAuth } from '../features/auth/Auth'
import { api, ApiError, json } from '../services/api'
import type { Business, User } from '../types'
import { ErrorState, Loading } from '../components/UI'
import { DatasetsPage } from '../features/datasets/DatasetsPage'

const AnalyticsPage = lazy(() =>
  import('../features/analytics/AnalyticsPage').then((module) => ({
    default: module.AnalyticsPage,
  })),
)

const client = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 30_000 } } })
const sections = ['overview', 'sales', 'products', 'customers', 'datasets', 'settings'] as const
const labels: Record<string, string> = {
  overview: 'Overview',
  sales: 'Sales',
  products: 'Products',
  customers: 'Customers',
  datasets: 'Datasets',
  settings: 'Business settings',
}
const icons: Record<string, string> = {
  overview: '◫',
  sales: '↗',
  products: '▦',
  customers: '♙',
  datasets: '▤',
  settings: '⚙',
}

function Workspace() {
  const { section = 'overview' } = useParams()
  const navigate = useNavigate()
  const { user, logout, setUser } = useAuth()
  const queryClient = useQueryClient()
  const [selected, setSelected] = useState<number>(() =>
    Number(localStorage.getItem('insightflow_business') || 0),
  )
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const me = useQuery({ queryKey: ['me'], queryFn: () => api<User>('/api/auth/me') })
  const businessQuery = useQuery({
    queryKey: ['businesses'],
    queryFn: () => api<Business[]>('/api/businesses'),
    enabled: me.isSuccess,
  })
  useEffect(() => {
    if (me.data && user?.id !== me.data.id) setUser(me.data)
  }, [me.data, user?.id, setUser])
  if (me.error instanceof ApiError && me.error.status === 401) {
    return <Navigate to="/login" replace />
  }
  if (me.isLoading || businessQuery.isLoading) return <Loading />
  if (me.error || businessQuery.error)
    return (
      <ErrorState
        message={
          (me.error || (businessQuery.error as Error))?.message || 'Unable to load workspace.'
        }
        retry={() => {
          void me.refetch()
          void businessQuery.refetch()
        }}
      />
    )
  const businesses = businessQuery.data || []
  const business = businesses.find((item) => item.id === selected) || businesses[0]
  async function create(event: FormEvent) {
    event.preventDefault()
    setError('')
    setCreating(true)
    try {
      const created = await api<Business>('/api/businesses', json({ name: newName }))
      setSelected(created.id)
      localStorage.setItem('insightflow_business', String(created.id))
      setNewName('')
      await queryClient.invalidateQueries({ queryKey: ['businesses'] })
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to create business.')
    } finally {
      setCreating(false)
    }
  }
  if (!business)
    return (
      <main className="onboarding">
        <div className="brand">
          <span className="brand-mark">◈</span> InsightFlow
        </div>
        <div className="onboarding-card">
          <span className="step">01 / YOUR WORKSPACE</span>
          <h1>First, tell us about your business.</h1>
          <p className="muted">
            A workspace keeps your sales data and analytics together. You can add more businesses
            later.
          </p>
          <form onSubmit={create}>
            <label>
              Business name
              <input
                required
                minLength={2}
                maxLength={120}
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. Courtside Supply Co."
              />
            </label>
            {error && (
              <p className="alert" role="alert">
                {error}
              </p>
            )}
            <button className="button primary" disabled={creating}>
              {creating ? 'Creating…' : 'Create workspace →'}
            </button>
          </form>
        </div>
      </main>
    )
  const active = sections.includes(section as (typeof sections)[number]) ? section : 'overview'
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" to="/app/overview">
          <span className="brand-mark">◈</span> InsightFlow
        </Link>
        <div className="workspace-label">WORKSPACE</div>
        <select
          aria-label="Select business"
          className="business-select"
          value={business.id}
          onChange={(e) => {
            const id = Number(e.target.value)
            setSelected(id)
            localStorage.setItem('insightflow_business', String(id))
            navigate('/app/overview')
          }}
        >
          {businesses.map((item) => (
            <option value={item.id} key={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <nav aria-label="Main navigation">
          <div className="nav-label">ANALYTICS</div>
          {sections.slice(0, 4).map((item) => (
            <Link
              key={item}
              className={`nav-link ${active === item ? 'active' : ''}`}
              to={`/app/${item}`}
            >
              <span>{icons[item]}</span>
              {labels[item]}
            </Link>
          ))}
          <div className="nav-label data-label">MANAGE</div>
          {sections.slice(4).map((item) => (
            <Link
              key={item}
              className={`nav-link ${active === item ? 'active' : ''}`}
              to={`/app/${item}`}
            >
              <span>{icons[item]}</span>
              {labels[item]}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="account-avatar">
            {(me.data?.name || user?.name || 'U').charAt(0).toUpperCase()}
          </div>
          <div className="account-meta">
            <strong>{me.data?.name || user?.name}</strong>
            <small>{me.data?.email || user?.email}</small>
          </div>
          <button
            className="logout"
            aria-label="Log out"
            title="Log out"
            onClick={() => {
              logout()
              navigate('/login')
            }}
          >
            ↪
          </button>
        </div>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <span className="breadcrumb">
            Workspace <span>/</span> {labels[active]}
          </span>
          <div className="topbar-right">
            <span className="live-dot" /> Connected to your data
          </div>
        </header>
        <main className="content">
          {active === 'datasets' ? (
            <DatasetsPage business={business} />
          ) : active === 'settings' ? (
            <SettingsPage
              business={business}
              businesses={businesses}
              onSelect={(id) => {
                setSelected(id)
                localStorage.setItem('insightflow_business', String(id))
              }}
            />
          ) : (
            <Suspense fallback={<Loading />}>
              <AnalyticsPage section={active} business={business} />
            </Suspense>
          )}
        </main>
      </div>
    </div>
  )
}

function SettingsPage({
  business,
  businesses,
  onSelect,
}: {
  business: Business
  businesses: Business[]
  onSelect: (id: number) => void
}) {
  const [name, setName] = useState(business.name)
  useEffect(() => {
    setName(business.name)
  }, [business.id, business.name])
  const [newName, setNewName] = useState('')
  const [message, setMessage] = useState('')
  const queryClient = useQueryClient()
  async function rename(event: FormEvent) {
    event.preventDefault()
    try {
      await api(`/api/businesses/${business.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ name }),
      })
      await queryClient.invalidateQueries({ queryKey: ['businesses'] })
      setMessage('Business name updated.')
    } catch (cause) {
      setMessage((cause as Error).message)
    }
  }
  async function add(event: FormEvent) {
    event.preventDefault()
    try {
      const item = await api<Business>('/api/businesses', json({ name: newName }))
      await queryClient.invalidateQueries({ queryKey: ['businesses'] })
      onSelect(item.id)
      setNewName('')
      setMessage('Workspace created.')
    } catch (cause) {
      setMessage((cause as Error).message)
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">WORKSPACE</p>
          <h1>Business settings</h1>
          <p>Manage your business workspaces.</p>
        </div>
      </div>
      <div className="settings-grid">
        <section className="panel">
          <h2>Business details</h2>
          <p className="muted">Changes to the name are visible to you immediately.</p>
          <form onSubmit={rename}>
            <label>
              Business name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                minLength={2}
              />
            </label>
            <button className="button primary">Save changes</button>
          </form>
        </section>
        <section className="panel">
          <h2>Add a workspace</h2>
          <p className="muted">Keep each business and its datasets separate.</p>
          <form onSubmit={add}>
            <label>
              New business name
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                required
                minLength={2}
                placeholder="Business name"
              />
            </label>
            <button className="button secondary">Create business</button>
          </form>
          <p className="helper">
            {businesses.length} workspace{businesses.length === 1 ? '' : 's'} on your account
          </p>
        </section>
      </div>
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}
    </>
  )
}

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

export default function App() {
  return (
    <QueryClientProvider client={client}>
      <AuthProvider>
        <BrowserRouter>
          <ScrollToTop />
          <Routes>
            <Route path="/login" element={<AuthPage mode="login" />} />
            <Route path="/register" element={<AuthPage mode="register" />} />
            <Route path="/app" element={<Navigate to="/app/overview" replace />} />
            <Route
              path="/app/:section"
              element={
                <Protected>
                  <Workspace />
                </Protected>
              }
            />
            <Route path="*" element={<Navigate to="/app" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
