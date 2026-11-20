import axios from 'axios'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import {
  hubsApi,
  type HubApplication,
  type HubApplicationStatus,
  type HubVerificationRequest,
} from '../../services/hubsApi'
import './hub-review.css'

type ReviewTab = 'applications' | 'verification'
type Paged = { count: number; next: number | null; previous: number | null }

function dateLabel(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Date unavailable' : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function getError(error: unknown) {
  if (axios.isAxiosError(error) && error.response?.status === 403) return 'Only authorised BYB staff can access Hub reviews.'
  return 'The review queue is unavailable. Please try again.'
}

export default function HubReviewPage() {
  const [tab, setTab] = useState<ReviewTab>('applications')
  const [applicationStatus, setApplicationStatus] = useState<HubApplicationStatus>('pending')
  const [verificationStatus, setVerificationStatus] = useState<HubApplicationStatus>('pending')
  const [applications, setApplications] = useState<HubApplication[]>([])
  const [verificationRequests, setVerificationRequests] = useState<HubVerificationRequest[]>([])
  const [applicationPage, setApplicationPage] = useState(1)
  const [verificationPage, setVerificationPage] = useState(1)
  const [applicationPagination, setApplicationPagination] = useState<Paged | null>(null)
  const [verificationPagination, setVerificationPagination] = useState<Paged | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busyId, setBusyId] = useState('')
  const [rejectingId, setRejectingId] = useState('')
  const [reviewNotes, setReviewNotes] = useState<Record<string, string>>({})
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let active = true
    async function load() {
      try {
        if (tab === 'applications') {
          const response = await hubsApi.getApplicationReviewQueue(applicationStatus, applicationPage)
          if (!active) return
          setApplications(response.results)
          setApplicationPagination(response)
        } else {
          const response = await hubsApi.getVerificationReviewQueue(verificationPage, verificationStatus)
          if (!active) return
          setVerificationRequests(response.results)
          setVerificationPagination(response)
        }
        if (active) setError('')
      } catch (loadError) {
        if (active) setError(getError(loadError))
      } finally {
        if (active) setLoading(false)
      }
    }
    void load()
    return () => { active = false }
  }, [tab, applicationStatus, verificationStatus, applicationPage, verificationPage, revision])

  async function reviewApplication(application: HubApplication, decision: 'approve' | 'reject') {
    const notes = (reviewNotes[application.id] || '').trim()
    if (decision === 'reject' && !notes) {
      setError('Enter a rejection reason before rejecting this application.')
      return
    }
    setBusyId(application.id)
    setError('')
    setNotice('')
    try {
      await hubsApi.reviewApplication(application.id, decision, notes)
      setApplications((previous) => previous.filter((item) => item.id !== application.id))
      setNotice(`${application.requested_name} was ${decision === 'approve' ? 'approved' : 'rejected'}.`)
      setRejectingId('')
      setRevision((value) => value + 1)
    } catch (reviewError) {
      setError(getError(reviewError))
    } finally {
      setBusyId('')
    }
  }

  async function reviewVerification(request: HubVerificationRequest, decision: 'approve' | 'reject') {
    const notes = (reviewNotes[request.id] || '').trim()
    if (decision === 'reject' && !notes) {
      setError('Enter a rejection reason before rejecting verification.')
      return
    }
    setBusyId(request.id)
    setError('')
    setNotice('')
    try {
      await hubsApi.reviewVerificationRequest(request.id, decision, notes)
      setVerificationRequests((previous) => previous.filter((item) => item.id !== request.id))
      setNotice(`${request.hub_name} verification was ${decision === 'approve' ? 'approved' : 'rejected'}.`)
      setRejectingId('')
      setRevision((value) => value + 1)
    } catch (reviewError) {
      setError(getError(reviewError))
    } finally {
      setBusyId('')
    }
  }

  return (
    <main className="hub-review-page">
      <header className="hub-review-header"><Link to="/hubs">← Back to Hubs</Link><span>BYB STAFF WORKSPACE</span><h1>Hub review</h1><p>Review Hub applications and verification requests. Only platform staff can make these decisions.</p></header>
      <div className="hub-review-tabs" role="tablist" aria-label="Hub review queues">
        <button type="button" role="tab" aria-selected={tab === 'applications'} onClick={() => { setTab('applications'); setLoading(true); setError(''); setNotice('') }}>Hub applications</button>
        <button type="button" role="tab" aria-selected={tab === 'verification'} onClick={() => { setTab('verification'); setLoading(true); setError(''); setNotice('') }}>Verification requests</button>
      </div>
      {error && <p className="hub-review-error" role="alert">{error}</p>}
      {notice && <p className="hub-review-notice" role="status">{notice}</p>}

      {tab === 'applications' ? (
        <section className="hub-review-section" aria-labelledby="hub-review-applications-title" aria-busy={loading}>
          <header className="hub-review-section-heading"><div><span>APPLICATIONS</span><h2 id="hub-review-applications-title">Hub creation requests</h2></div><label>Status <select value={applicationStatus} onChange={(event) => { setApplicationStatus(event.currentTarget.value as HubApplicationStatus); setApplicationPage(1); setLoading(true) }}><option value="pending">Pending</option><option value="approved">Approved</option><option value="rejected">Rejected</option></select></label></header>
          {loading && <p className="hub-review-state" role="status">Loading applications…</p>}
          {!loading && applications.length === 0 && <p className="hub-review-state">No {applicationStatus} Hub applications.</p>}
          <div className="hub-review-list">{applications.map((application) => (
            <article className="hub-review-card" key={application.id}>
              <div className="hub-review-card-top"><div><h3>{application.requested_name}</h3><span>/{application.requested_slug} · {application.hub_type.replaceAll('_', ' ')}</span></div><strong className={`hub-review-badge status-${application.status}`}>{application.status}</strong></div>
              <p className="hub-review-submitted">Applied by @{application.applicant_username} · {dateLabel(application.created_at)}</p>
              {application.organisation_description && <p>{application.organisation_description}</p>}
              <dl><div><dt>Parent organisation</dt><dd>{application.college_or_parent_organisation || 'Not provided'}</dd></div><div><dt>Location</dt><dd>{application.city || 'Not provided'}</dd></div><div><dt>Contact</dt><dd>{application.contact_email || 'Not provided'}</dd></div><div><dt>Website</dt><dd>{application.website || 'Not provided'}</dd></div></dl>
              {application.reviewed_at && <p className="hub-review-submitted">Reviewed {dateLabel(application.reviewed_at)}{application.reviewer_username ? ` by @${application.reviewer_username}` : ''}{application.review_notes ? ` · ${application.review_notes}` : ''}</p>}
              {application.status === 'pending' && <>
                {rejectingId === application.id && <div className="hub-review-reason"><label htmlFor={`application-reason-${application.id}`}>Reason for rejection (required)</label><textarea id={`application-reason-${application.id}`} value={reviewNotes[application.id] || ''} maxLength={5000} rows={3} onChange={(event) => setReviewNotes((previous) => ({ ...previous, [application.id]: event.currentTarget.value }))} /></div>}
                <div className="hub-review-actions"><button type="button" className="approve" disabled={Boolean(busyId)} onClick={() => void reviewApplication(application, 'approve')}>{busyId === application.id ? 'Saving…' : 'Approve and create Hub'}</button>{rejectingId === application.id ? <><button type="button" className="reject" disabled={Boolean(busyId) || !(reviewNotes[application.id] || '').trim()} onClick={() => void reviewApplication(application, 'reject')}>Confirm rejection</button><button type="button" onClick={() => setRejectingId('')}>Cancel</button></> : <button type="button" className="reject" disabled={Boolean(busyId)} onClick={() => setRejectingId(application.id)}>Reject</button>}</div>
              </>}
              {application.created_hub_id && <Link className="hub-review-open-hub" to={`/hubs/${application.created_hub_id}`}>Open Hub →</Link>}
            </article>
          ))}</div>
          {applicationPagination && (applicationPagination.previous || applicationPagination.next) && <nav className="hub-review-pagination" aria-label="Hub application review pages"><button disabled={!applicationPagination.previous} onClick={() => { setApplicationPage(applicationPagination.previous || 1); setLoading(true) }}>Previous</button><span>Page {applicationPage}</span><button disabled={!applicationPagination.next} onClick={() => { setApplicationPage(applicationPagination.next || applicationPage); setLoading(true) }}>Next</button></nav>}
        </section>
      ) : (
        <section className="hub-review-section" aria-labelledby="hub-review-verification-title" aria-busy={loading}>
          <header className="hub-review-section-heading"><div><span>VERIFICATION</span><h2 id="hub-review-verification-title">Hub identity requests</h2></div><label>Status <select value={verificationStatus} onChange={(event) => { setVerificationStatus(event.currentTarget.value as HubApplicationStatus); setVerificationPage(1); setLoading(true) }}><option value="pending">Pending</option><option value="approved">Approved</option><option value="rejected">Rejected</option></select></label></header>
          {loading && <p className="hub-review-state" role="status">Loading verification requests…</p>}
          {!loading && verificationRequests.length === 0 && <p className="hub-review-state">No {verificationStatus} verification requests.</p>}
          <div className="hub-review-list">{verificationRequests.map((request) => (
            <article className="hub-review-card" key={request.id}>
              <div className="hub-review-card-top"><div><h3>{request.hub_name}</h3><span>/{request.hub_slug} · {request.hub_type.replaceAll('_', ' ')}</span></div><strong className={`hub-review-badge status-${request.status}`}>{request.status}</strong></div>
              <p className="hub-review-submitted">Requested by @{request.requested_by_username} · {dateLabel(request.requested_at)} · {request.hub_city || 'Location not listed'}</p>
              {request.request_notes && <p>{request.request_notes}</p>}
              {request.reviewed_at && <p className="hub-review-submitted">Reviewed {dateLabel(request.reviewed_at)}{request.reviewer_username ? ` by @${request.reviewer_username}` : ''}{request.review_notes ? ` · ${request.review_notes}` : ''}</p>}
              {request.status === 'pending' && <>
                {rejectingId === request.id && <div className="hub-review-reason"><label htmlFor={`verification-reason-${request.id}`}>Reason for rejection (required)</label><textarea id={`verification-reason-${request.id}`} value={reviewNotes[request.id] || ''} maxLength={5000} rows={3} onChange={(event) => setReviewNotes((previous) => ({ ...previous, [request.id]: event.currentTarget.value }))} /></div>}
                <div className="hub-review-actions"><button type="button" className="approve" disabled={Boolean(busyId)} onClick={() => void reviewVerification(request, 'approve')}>Approve verification</button>{rejectingId === request.id ? <><button type="button" className="reject" disabled={Boolean(busyId) || !(reviewNotes[request.id] || '').trim()} onClick={() => void reviewVerification(request, 'reject')}>Confirm rejection</button><button type="button" onClick={() => setRejectingId('')}>Cancel</button></> : <button type="button" className="reject" disabled={Boolean(busyId)} onClick={() => setRejectingId(request.id)}>Reject</button>}</div>
              </>}
              <Link className="hub-review-open-hub" to={`/hubs/${request.hub}`}>View Hub →</Link>
            </article>
          ))}</div>
          {verificationPagination && (verificationPagination.previous || verificationPagination.next) && <nav className="hub-review-pagination" aria-label="Verification review pages"><button disabled={!verificationPagination.previous} onClick={() => { setVerificationPage(verificationPagination.previous || 1); setLoading(true) }}>Previous</button><span>Page {verificationPage}</span><button disabled={!verificationPagination.next} onClick={() => { setVerificationPage(verificationPagination.next || verificationPage); setLoading(true) }}>Next</button></nav>}
        </section>
      )}
    </main>
  )
}
