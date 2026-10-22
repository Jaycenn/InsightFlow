import { useState, type ChangeEvent } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError, json } from '../../services/api'
import type { Business, Dataset, Preview, Validation } from '../../types'
import { Empty, ErrorState, Loading, Panel } from '../../components/UI'

const fields = [
  ['order_id', 'Order ID', true],
  ['date', 'Date', true],
  ['product', 'Product', true],
  ['category', 'Category', false],
  ['quantity', 'Quantity', true],
  ['unit_price', 'Unit price', true],
  ['cost', 'Unit cost', false],
  ['customer', 'Customer', false],
] as const

export function DatasetsPage({ business }: { business: Business }) {
  const queryClient = useQueryClient()
  const [activeId, setActiveId] = useState<number | null>(null)
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [validation, setValidation] = useState<Validation | null>(null)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const datasets = useQuery({
    queryKey: ['datasets', business.id],
    queryFn: () => api<Dataset[]>(`/api/businesses/${business.id}/datasets`),
  })
  const preview = useQuery({
    queryKey: ['preview', activeId],
    queryFn: () => api<Preview>(`/api/datasets/${activeId}/preview`),
    enabled: activeId !== null,
  })
  const selected = datasets.data?.find((item) => item.id === activeId)
  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setBusy(true)
    setMessage('')
    setValidation(null)
    try {
      const body = new FormData()
      body.append('file', file)
      const dataset = await api<Dataset>(`/api/businesses/${business.id}/datasets/upload`, {
        method: 'POST',
        body,
      })
      await queryClient.invalidateQueries({ queryKey: ['datasets', business.id] })
      const detail = await api<Preview>(`/api/datasets/${dataset.id}/preview`)
      queryClient.setQueryData(['preview', dataset.id], detail)
      setActiveId(dataset.id)
      setMapping(detail.suggested_mapping)
      setMessage('File uploaded. Review the suggested column mapping before importing.')
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : 'Upload failed.')
    } finally {
      setBusy(false)
      event.target.value = ''
    }
  }
  async function check(importNow: boolean) {
    if (!activeId) return
    setBusy(true)
    setMessage('')
    setValidation(null)
    try {
      const result = await api<Validation>(`/api/datasets/${activeId}/validate`, json({ mapping }))
      setValidation(result)
      if (result.valid && importNow) {
        await api<Dataset>(`/api/datasets/${activeId}/import`, json({ mapping }))
        await queryClient.invalidateQueries({ queryKey: ['datasets', business.id] })
        await queryClient.invalidateQueries({ queryKey: ['analytics', business.id] })
        setMessage(`${result.total_rows} sales rows imported successfully.`)
      } else
        setMessage(
          result.valid
            ? `${result.total_rows} rows are ready to import.`
            : `${result.error_count} issues need attention before import.`,
        )
    } catch (cause) {
      const error = cause as ApiError
      setMessage(error.message)
      if (error.details?.length)
        setValidation({
          valid: false,
          total_rows: 0,
          error_count: error.details.length,
          errors: error.details.map((item) => ({
            row: item.row ?? null,
            field: item.field ?? '',
            message: item.message,
          })),
        })
    } finally {
      setBusy(false)
    }
  }
  async function remove(item: Dataset) {
    if (
      !window.confirm(
        `Delete ${item.original_filename} and its imported sales? This cannot be undone.`,
      )
    )
      return
    try {
      await api(`/api/datasets/${item.id}`, { method: 'DELETE' })
      if (activeId === item.id) setActiveId(null)
      await queryClient.invalidateQueries({ queryKey: ['datasets', business.id] })
      await queryClient.invalidateQueries({ queryKey: ['analytics', business.id] })
      setMessage('Dataset deleted.')
    } catch (cause) {
      setMessage((cause as Error).message)
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">DATA SOURCES</p>
          <h1>Datasets</h1>
          <p>Bring your sales data in, check the columns, then explore what happened.</p>
        </div>
        <label className="button primary upload-button">
          {busy ? 'Working…' : '+ Upload dataset'}
          <input type="file" accept=".csv,.xlsx" onChange={upload} disabled={busy} />
        </label>
      </div>
      <div className="hint-bar">
        <span>ⓘ</span>
        <span>Upload a CSV or XLSX file up to 5 MB. Your data stays inside your workspace.</span>
      </div>
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}
      {datasets.isLoading ? (
        <Loading />
      ) : datasets.error ? (
        <ErrorState
          message={(datasets.error as Error).message}
          retry={() => void datasets.refetch()}
        />
      ) : (
        <Panel
          title="Your datasets"
          subtitle={`${datasets.data?.length || 0} uploaded file${datasets.data?.length === 1 ? '' : 's'}`}
        >
          {datasets.data?.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>File</th>
                    <th>Status</th>
                    <th>Records</th>
                    <th>Uploaded</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {datasets.data.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.original_filename}</strong>
                        <small className="file-type">{item.file_type.toUpperCase()}</small>
                      </td>
                      <td>
                        <span className={`status ${item.import_status}`}>{item.import_status}</span>
                      </td>
                      <td>{item.record_count.toLocaleString()}</td>
                      <td>{new Date(item.uploaded_at).toLocaleDateString()}</td>
                      <td>
                        <div className="row-actions">
                          <button
                            className="text-button"
                            onClick={() => {
                              setActiveId(item.id)
                              setValidation(null)
                              setMapping({})
                            }}
                          >
                            Preview
                          </button>
                          <button className="text-button danger" onClick={() => void remove(item)}>
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty
              title="No datasets yet"
              detail="Upload a sales spreadsheet to start building your dashboard."
            />
          )}
        </Panel>
      )}
      {activeId && (
        <Panel
          title={selected?.import_status === 'imported' ? 'Dataset preview' : 'Map your columns'}
          subtitle={selected?.original_filename || 'Review your file'}
          action={
            <button className="text-button" onClick={() => setActiveId(null)}>
              Close ✕
            </button>
          }
        >
          {preview.isLoading ? (
            <Loading />
          ) : preview.error ? (
            <ErrorState message={(preview.error as Error).message} />
          ) : (
            preview.data && (
              <>
                <div className="preview-meta">
                  {preview.data.total_rows.toLocaleString()} rows · {preview.data.columns.length}{' '}
                  columns detected
                </div>
                {selected?.import_status !== 'imported' && (
                  <>
                    <p className="muted">
                      Match your spreadsheet columns to the fields InsightFlow uses. Required fields
                      are marked with *.
                    </p>
                    <div className="mapping-grid">
                      {fields.map(([field, label, required]) => (
                        <label key={field}>
                          {label}
                          {required ? ' *' : ''}
                          <select
                            value={mapping[field] || ''}
                            onChange={(e) => {
                              setMapping({ ...mapping, [field]: e.target.value })
                              setValidation(null)
                            }}
                          >
                            <option value="">
                              {required ? 'Select a column' : 'Not provided'}
                            </option>
                            {preview.data!.columns.map((column) => (
                              <option key={column} value={column}>
                                {column}
                              </option>
                            ))}
                          </select>
                        </label>
                      ))}
                    </div>
                    <div className="button-row">
                      <button
                        className="button secondary"
                        disabled={busy}
                        onClick={() => void check(false)}
                      >
                        Validate data
                      </button>
                      <button
                        className="button primary"
                        disabled={busy}
                        onClick={() => void check(true)}
                      >
                        {busy ? 'Checking…' : 'Validate & import'}
                      </button>
                    </div>
                    {validation && !validation.valid && (
                      <div className="validation-box" role="alert">
                        <strong>{validation.error_count} issues need attention</strong>
                        <ul>
                          {validation.errors.slice(0, 15).map((issue, index) => (
                            <li key={index}>
                              {issue.row ? `Row ${issue.row}: ` : ''}
                              {issue.message}
                            </li>
                          ))}
                        </ul>
                        {validation.errors.length > 15 && <p>Showing the first 15 issues.</p>}
                      </div>
                    )}
                  </>
                )}
                <h3 className="subheading">File preview</h3>
                <div className="table-wrap preview-table">
                  <table>
                    <thead>
                      <tr>
                        {preview.data.columns.map((column) => (
                          <th key={column}>{column}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {preview.data.rows.map((row, index) => (
                        <tr key={index}>
                          {preview.data!.columns.map((column) => (
                            <td key={column}>{row[column]}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )
          )}
        </Panel>
      )}
    </>
  )
}
