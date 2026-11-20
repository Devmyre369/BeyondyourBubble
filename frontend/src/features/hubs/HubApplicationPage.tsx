import axios from 'axios'
import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import {
  hubsApi,
  type HubApplication,
  type HubApplicationSubmitRequest,
  type HubDiscoveryResponse,
  type HubType,
} from '../../services/hubsApi'
import './hub-application.css'

const HUB_TYPES: Array<{ value: HubType; label: string }> = [
  { value: 'college', label: 'College' },
  { value: 'college_club', label: 'College club' },
  { value: 'college_department', label: 'College department' },
  { value: 'organisation', label: 'Organisation' },
  { value: 'company', label: 'Company' },
  { value: 'community', label: 'Community' },
]

const initialForm: HubApplicationSubmitRequest = {
  requested_name: '', requested_slug: '', hub_type: 'community',
  organisation_description: '', college_or_parent_organisation: '',
  city: '', website: '', contact_email: '',
}

function errorMessage(error: unknown) {
  if (axios.isAxiosError(error) && error.response?.data && typeof error.response.data === 'object') {
    const values = Object.values(error.response.data as Record<string, unknown>)
    const message = values.flatMap((value) => Array.isArray(value) ? value : [value]).find((value) => typeof value === 'string')
    if (typeof message === 'string') return message
  }
  return 'We could not submit your application. Please try again.'
}

function slugify(value: string) {
  return value.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 200)
}

function statusLabel(status: HubApplication['status']) {
  return status.charAt(0).toUpperCase() + status.slice(1)
}

function dateLabel(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Date unavailable' : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

export default function HubApplicationPage() {
  const [form, setForm] = useState(initialForm)
  const [slugWasEdited, setSlugWasEdited] = useState(false)
  const [applications, setApplications] = useState<HubApplication[]>([])
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState<HubDiscoveryResponse<HubApplication> | null>(null)
  const [loadingApplications, setLoadingApplications] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [reload, setReload] = useState(0)

  useEffect(() => {
    let active = true
    async function loadApplications() {
      try {
        const response = await hubsApi.getMyApplications(page)
        if (!active) return
        setApplications(response.results)
        setPagination(response)
      } catch {
        if (active) setError('Your application status could not be loaded.')
      } finally {
        if (active) setLoadingApplications(false)
      }
    }
    void loadApplications()
    return () => { active = false }
  }, [page, reload])

  function update<K extends keyof HubApplicationSubmitRequest>(field: K, value: HubApplicationSubmitRequest[K]) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) return
    setSubmitting(true)
    setError('')
    setSuccess('')
    try {
      const created = await hubsApi.submitApplication(form)
      setSuccess(`Your application for ${created.requested_name} was submitted for BYB review.`)
      setForm(initialForm)
      setSlugWasEdited(false)
      setPage(1)
      setReload((current) => current + 1)
    } catch (submitError) {
      setError(errorMessage(submitError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="hub-application-page">
      <header className="hub-application-header">
        <Link to="/hubs">← Back to Hubs</Link>
        <span>HUB APPLICATION</span>
        <h1>Apply to create a Hub</h1>
        <p>Share your organisation details. BYB staff review applications before the Hub is created.</p>
      </header>

      <div className="hub-application-layout">
        <section className="hub-application-form-card" aria-labelledby="hub-application-form-title">
          <h2 id="hub-application-form-title">Organisation details</h2>
          {error && <p className="hub-application-error" role="alert">{error}</p>}
          {success && <p className="hub-application-success" role="status">{success}</p>}
          <form onSubmit={(event) => void submit(event)}>
            <label htmlFor="application-name">Hub name</label>
            <input id="application-name" value={form.requested_name} maxLength={200} required onChange={(event) => {
              const name = event.currentTarget.value
              setForm((current) => ({ ...current, requested_name: name, ...(!slugWasEdited ? { requested_slug: slugify(name) } : {}) }))
            }} />
            <label htmlFor="application-slug">Requested Hub address</label>
            <input id="application-slug" value={form.requested_slug} maxLength={200} pattern="[a-zA-Z0-9_-]+" required onChange={(event) => {
              setSlugWasEdited(true)
              update('requested_slug', slugify(event.currentTarget.value))
            }} />
            <label htmlFor="application-type">Hub type</label>
            <select id="application-type" value={form.hub_type} onChange={(event) => update('hub_type', event.currentTarget.value as HubType)}>
              {HUB_TYPES.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
            </select>
            <label htmlFor="application-description">What is this organisation about?</label>
            <textarea id="application-description" value={form.organisation_description} maxLength={10000} rows={5} onChange={(event) => update('organisation_description', event.currentTarget.value)} />
            <label htmlFor="application-parent">College or parent organisation</label>
            <input id="application-parent" value={form.college_or_parent_organisation} maxLength={200} onChange={(event) => update('college_or_parent_organisation', event.currentTarget.value)} />
            <div className="hub-application-two-column">
              <div><label htmlFor="application-city">City</label><input id="application-city" value={form.city} maxLength={100} onChange={(event) => update('city', event.currentTarget.value)} /></div>
              <div><label htmlFor="application-email">Contact email</label><input id="application-email" type="email" value={form.contact_email} onChange={(event) => update('contact_email', event.currentTarget.value)} /></div>
            </div>
            <label htmlFor="application-website">Website</label>
            <input id="application-website" type="url" value={form.website} onChange={(event) => update('website', event.currentTarget.value)} placeholder="https://example.com" />
            <button type="submit" disabled={submitting || !form.requested_slug.trim()}>{submitting ? 'Submitting…' : 'Submit application'}</button>
          </form>
        </section>

        <section className="hub-application-status-card" aria-labelledby="hub-application-status-title" aria-busy={loadingApplications}>
          <div className="hub-application-section-heading"><div><span>YOUR REQUESTS</span><h2 id="hub-application-status-title">Application status</h2></div><button type="button" onClick={() => { setLoadingApplications(true); setReload((current) => current + 1) }}>Refresh</button></div>
          {loadingApplications && <p className="hub-application-state" role="status">Loading your applications…</p>}
          {!loadingApplications && applications.length === 0 && <p className="hub-application-state">You have not submitted a Hub application yet.</p>}
          <div className="hub-application-list">
            {applications.map((application) => (
              <article className="hub-application-item" key={application.id}>
                <div className="hub-application-item-heading"><div><h3>{application.requested_name}</h3><span>/{application.requested_slug}</span></div><strong className={`hub-application-status status-${application.status}`}>{statusLabel(application.status)}</strong></div>
                <p>{HUB_TYPES.find((type) => type.value === application.hub_type)?.label} · Submitted {dateLabel(application.created_at)}</p>
                {application.reviewed_at && <p>Reviewed {dateLabel(application.reviewed_at)}{application.reviewer_username ? ` by @${application.reviewer_username}` : ''}</p>}
                {application.review_notes && <p className="hub-application-review-notes">{application.review_notes}</p>}
                {application.created_hub_id && <Link to={`/hubs/${application.created_hub_id}`}>Open your Hub →</Link>}
              </article>
            ))}
          </div>
          {pagination && (pagination.previous !== null || pagination.next !== null) && <nav className="hub-application-pagination" aria-label="Application pages"><button type="button" disabled={!pagination.previous} onClick={() => setPage(pagination.previous || 1)}>Previous</button><span>Page {page}</span><button type="button" disabled={!pagination.next} onClick={() => setPage(pagination.next || page)}>Next</button></nav>}
        </section>
      </div>
    </main>
  )
}
