import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../../services/api'
import type { Analytics, Business, Filters, Options } from '../../types'
import { Empty, ErrorState, Loading, money, number, Panel } from '../../components/UI'

const initial: Filters = { start_date: '', end_date: '', product: '', category: '', customer: '' }
const titles: Record<string, { eyebrow: string; title: string; description: string }> = {
  overview: {
    eyebrow: 'YOUR BUSINESS AT A GLANCE',
    title: 'Overview',
    description: 'A clear view of how your business is performing.',
  },
  sales: {
    eyebrow: 'REVENUE & ORDERS',
    title: 'Sales analytics',
    description: 'Follow sales activity over time and find the patterns that matter.',
  },
  products: {
    eyebrow: 'PRODUCT PERFORMANCE',
    title: 'Products',
    description: 'See which products and categories are moving your business forward.',
  },
  customers: {
    eyebrow: 'CUSTOMER INSIGHTS',
    title: 'Customers',
    description: 'Understand who buys from your business and how much they spend.',
  },
}

function FiltersBar({
  filters,
  setFilters,
  options,
}: {
  filters: Filters
  setFilters: (filters: Filters) => void
  options: Options | undefined
}) {
  function update(key: keyof Filters, value: string) {
    setFilters({ ...filters, [key]: value })
  }
  return (
    <div className="filters">
      <div className="filter-title">
        <span>☷</span> Filters
      </div>
      <label>
        From
        <input
          type="date"
          value={filters.start_date}
          max={filters.end_date || undefined}
          onChange={(e) => update('start_date', e.target.value)}
        />
      </label>
      <label>
        To
        <input
          type="date"
          value={filters.end_date}
          min={filters.start_date || undefined}
          onChange={(e) => update('end_date', e.target.value)}
        />
      </label>
      <label>
        Product
        <select value={filters.product} onChange={(e) => update('product', e.target.value)}>
          <option value="">All products</option>
          {options?.products.map((value) => (
            <option key={value}>{value}</option>
          ))}
        </select>
      </label>
      <label>
        Category
        <select value={filters.category} onChange={(e) => update('category', e.target.value)}>
          <option value="">All categories</option>
          {options?.categories.map((value) => (
            <option key={value}>{value}</option>
          ))}
        </select>
      </label>
      <label>
        Customer
        <select value={filters.customer} onChange={(e) => update('customer', e.target.value)}>
          <option value="">All customers</option>
          {options?.customers.map((value) => (
            <option key={value}>{value}</option>
          ))}
        </select>
      </label>
      <button className="clear-button" onClick={() => setFilters(initial)}>
        Clear
      </button>
    </div>
  )
}

function Kpis({ data }: { data: Analytics }) {
  const { kpis } = data
  const cards = [
    ['Total revenue', money(kpis.revenue), '↗'],
    ['Orders', number(kpis.orders), '▣'],
    ['Units sold', number(kpis.units), '▦'],
    ['Avg. order value', money(kpis.average_order_value), '◉'],
    ['Gross profit', kpis.gross_profit === null ? 'Unavailable' : money(kpis.gross_profit), '◈'],
    [
      'Profit margin',
      kpis.profit_margin === null ? 'Unavailable' : `${number(kpis.profit_margin)}%`,
      '◎',
    ],
  ]
  return (
    <>
      <div className="kpi-grid">
        {cards.map(([label, value, icon]) => (
          <div className="kpi-card" key={label}>
            <div className="kpi-top">
              <span>{label}</span>
              <span className="kpi-icon">{icon}</span>
            </div>
            <strong>{value}</strong>
            <span className="kpi-caption">
              {value === 'Unavailable' ? 'Cost data was not supplied' : 'Based on current filters'}
            </span>
          </div>
        ))}
      </div>
      {!kpis.cost_available && data.recent_sales.length > 0 && (
        <p className="cost-note">
          ⓘ Profit metrics are unavailable because some sales rows do not contain cost information.
        </p>
      )}
    </>
  )
}

function Trends({ data, focus }: { data: Analytics; focus: 'revenue' | 'orders' }) {
  return (
    <Panel
      title={focus === 'revenue' ? 'Revenue over time' : 'Orders over time'}
      subtitle="Daily activity from imported sales"
    >
      {data.trends.length ? (
        <div className="chart" role="img" aria-label={`Daily ${focus} chart`}>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={data.trends} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id={`fill-${focus}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#418b83" stopOpacity={0.26} />
                  <stop offset="100%" stopColor="#418b83" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#e8edf0" vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={(value) => value.slice(5)}
                tick={{ fill: '#7c8992', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#7c8992', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={55}
              />
              <Tooltip
                formatter={(value) =>
                  focus === 'revenue' ? money(Number(value)) : number(Number(value))
                }
              />
              <Area
                dataKey={focus}
                type="monotone"
                stroke="#287c73"
                strokeWidth={2.5}
                fill={`url(#fill-${focus})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <Empty
          title="No sales in this view"
          detail="Try a different date range or upload a dataset."
        />
      )}
    </Panel>
  )
}

function Categories({ data }: { data: Analytics }) {
  return (
    <Panel title="Category performance" subtitle="Revenue by product category">
      {data.categories.length ? (
        <div className="chart" role="img" aria-label="Revenue by category chart">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.categories} layout="vertical" margin={{ left: 10, right: 28 }}>
              <CartesianGrid stroke="#e8edf0" horizontal={false} />
              <XAxis
                type="number"
                tick={{ fill: '#7c8992', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                dataKey="name"
                type="category"
                width={100}
                tick={{ fill: '#465761', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip formatter={(value) => money(Number(value))} />
              <Bar dataKey="revenue" fill="#438e83" radius={[0, 4, 4, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <Empty title="No categories yet" detail="Import a dataset to see category performance." />
      )}
    </Panel>
  )
}

function ProductsTable({
  data,
  limit,
  lowest = false,
}: {
  data: Analytics
  limit?: number
  lowest?: boolean
}) {
  const products = lowest
    ? [...data.products].reverse().slice(0, 5)
    : limit
      ? data.products.slice(0, limit)
      : data.products
  return (
    <Panel
      title={lowest ? 'Lower-performing products' : limit ? 'Top products' : 'Product performance'}
      subtitle={lowest ? 'Lowest revenue in this view' : 'Ranked by revenue'}
    >
      {products.length ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Units sold</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {products.map((item) => (
                <tr key={`${item.name}-${item.category}`}>
                  <td>
                    <strong>{item.name}</strong>
                  </td>
                  <td>{item.category}</td>
                  <td>{number(item.units)}</td>
                  <td className="numeric">{money(item.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty
          title="No products found"
          detail="There are no sales matching the current filters."
        />
      )}
    </Panel>
  )
}

function CustomersTable({ data, limit }: { data: Analytics; limit?: number }) {
  const customers = limit ? data.customers.slice(0, limit) : data.customers
  return (
    <Panel
      title={limit ? 'Top customers' : 'Customer performance'}
      subtitle="Ranked by total spending"
    >
      {customers.length ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Customer</th>
                <th>Orders</th>
                <th>Average spend</th>
                <th>Total spent</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((item) => (
                <tr key={item.name}>
                  <td>
                    <strong>{item.name}</strong>
                  </td>
                  <td>{number(item.orders)}</td>
                  <td>{money(item.average_spending)}</td>
                  <td className="numeric">{money(item.spending)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty
          title="No customer data found"
          detail="Import customer names or adjust the current filters."
        />
      )}
    </Panel>
  )
}

function RecentSales({ data }: { data: Analytics }) {
  return (
    <Panel title="Recent sales" subtitle="The latest imported transactions">
      {data.recent_sales.length ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Order</th>
                <th>Product</th>
                <th>Customer</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_sales.map((item, index) => (
                <tr key={`${item.order_id}-${index}`}>
                  <td>{item.date}</td>
                  <td>{item.order_id}</td>
                  <td>
                    <strong>{item.product}</strong>
                  </td>
                  <td>{item.customer || '—'}</td>
                  <td className="numeric">{money(item.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty
          title="No recent sales"
          detail="Upload and import a sales file to see transactions here."
        />
      )}
    </Panel>
  )
}

export function AnalyticsPage({ business, section }: { business: Business; section: string }) {
  const [filters, setFilters] = useState<Filters>(initial)
  const params = new URLSearchParams(Object.entries(filters).filter(([, value]) => value))
  const data = useQuery({
    queryKey: ['analytics', business.id, section, filters],
    queryFn: () => api<Analytics>(`/api/businesses/${business.id}/analytics/${section}?${params}`),
  })
  const options = useQuery({
    queryKey: ['options', business.id],
    queryFn: () => api<Options>(`/api/businesses/${business.id}/analytics/options`),
  })
  const heading = titles[section] || titles.overview
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">{heading.eyebrow}</p>
          <h1>{heading.title}</h1>
          <p>{heading.description}</p>
        </div>
        <Link className="button primary" to="/app/datasets">
          + Add data
        </Link>
      </div>
      <FiltersBar filters={filters} setFilters={setFilters} options={options.data} />
      {data.isLoading ? (
        <Loading />
      ) : data.error ? (
        <ErrorState message={(data.error as Error).message} retry={() => void data.refetch()} />
      ) : (
        data.data && (
          <>
            <Kpis data={data.data} />
            {section === 'overview' && (
              <>
                <div className="two-col">
                  <Trends data={data.data} focus="revenue" />
                  <Categories data={data.data} />
                </div>
                <div className="two-col">
                  <ProductsTable data={data.data} limit={5} />
                  <CustomersTable data={data.data} limit={5} />
                </div>
                <RecentSales data={data.data} />
              </>
            )}
            {section === 'sales' && (
              <>
                <div className="two-col">
                  <Trends data={data.data} focus="revenue" />
                  <Trends data={data.data} focus="orders" />
                </div>
                <RecentSales data={data.data} />
              </>
            )}
            {section === 'products' && (
              <>
                <Categories data={data.data} />
                <div className="two-col">
                  <ProductsTable data={data.data} limit={5} />
                  <ProductsTable data={data.data} lowest />
                </div>
                <ProductsTable data={data.data} />
              </>
            )}
            {section === 'customers' && <CustomersTable data={data.data} />}
          </>
        )
      )}
    </>
  )
}
