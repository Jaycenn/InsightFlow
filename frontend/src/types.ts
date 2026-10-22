export type User = { id: number; name: string; email: string }
export type Business = { id: number; name: string; created_at: string }
export type Dataset = {
  id: number
  business_id: number
  original_filename: string
  file_type: string
  record_count: number
  import_status: string
  uploaded_at: string
}
export type Preview = {
  columns: string[]
  rows: Record<string, string>[]
  total_rows: number
  suggested_mapping: Record<string, string>
}
export type Validation = {
  valid: boolean
  total_rows: number
  error_count: number
  errors: { row: number | null; field: string; message: string }[]
}
export type Filters = {
  start_date: string
  end_date: string
  product: string
  category: string
  customer: string
}
export type Analytics = {
  kpis: {
    revenue: number
    gross_profit: number | null
    profit_margin: number | null
    orders: number
    units: number
    average_order_value: number
    cost_available: boolean
  }
  trends: { date: string; revenue: number; orders: number }[]
  products: { name: string; category: string; revenue: number; units: number }[]
  categories: { name: string; revenue: number; units: number }[]
  customers: { name: string; spending: number; orders: number; average_spending: number }[]
  recent_sales: {
    date: string
    order_id: string
    product: string
    customer: string | null
    quantity: number
    revenue: number
  }[]
}
export type Options = { products: string[]; categories: string[]; customers: string[] }
