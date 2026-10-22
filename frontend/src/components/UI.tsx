import type { ReactNode } from 'react'

export function Panel({
  title,
  subtitle,
  children,
  action,
}: {
  title: string
  subtitle?: string
  children: ReactNode
  action?: ReactNode
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  )
}
export function Empty({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty">
      <span className="empty-icon">▤</span>
      <h3>{title}</h3>
      <p>{detail}</p>
    </div>
  )
}
export function Loading() {
  return (
    <div className="state" role="status">
      Loading your workspace…
    </div>
  )
}
export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <div className="state error" role="alert">
      <strong>Something went wrong</strong>
      <p>{message}</p>
      {retry && (
        <button className="button secondary" onClick={retry}>
          Try again
        </button>
      )}
    </div>
  )
}
export const money = (value: number) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(value)
export const number = (value: number) =>
  new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value)
