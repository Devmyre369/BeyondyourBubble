import { useState, type FormEvent } from 'react'

import { hubsApi, type HubDetail } from '../../services/hubsApi'
import './hub-verification.css'

const STATUS_LABELS: Record<HubDetail['verification_status'], string> = {
  not_requested: 'Not requested',
  pending: 'Pending BYB review',
  approved: 'Verified by BYB',
  rejected: 'Request declined',
}

export default function HubVerificationPanel({ hub }: { hub: HubDetail }) {
  const [verificationStatus, setVerificationStatus] = useState(hub.verification_status)
  const [canRequest, setCanRequest] = useState(hub.can_request_verification)
  const [reviewNotes, setReviewNotes] = useState(hub.verification_review_notes)
  const [requestNotes, setRequestNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) return
    setSubmitting(true)
    setError('')
    setSuccess('')
    try {
      await hubsApi.requestVerification(hub.id, requestNotes.trim())
      setVerificationStatus('pending')
      setCanRequest(false)
      setReviewNotes('')
      setRequestNotes('')
      setSuccess('Your verification request was sent to BYB staff.')
    } catch {
      setError('We could not submit the verification request. Refresh the page and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="hub-verification-panel" aria-labelledby="hub-verification-title">
      <div className="hub-verification-copy">
        <span>BYB IDENTITY REVIEW</span>
        <h2 id="hub-verification-title">Verification</h2>
        <p>Verification requests are reviewed by BYB staff. Hub Owners and Admins cannot approve their own Hub.</p>
      </div>
      <strong className={`hub-verification-status status-${verificationStatus}`} role="status">{STATUS_LABELS[verificationStatus]}</strong>
      {reviewNotes && <p className="hub-verification-review-notes">BYB review: {reviewNotes}</p>}
      {error && <p className="hub-verification-error" role="alert">{error}</p>}
      {success && <p className="hub-verification-success" role="status">{success}</p>}
      {canRequest && <form className="hub-verification-form" onSubmit={(event) => void submit(event)}>
        <label htmlFor={`verification-notes-${hub.id}`}>Information for the review team (optional)</label>
        <textarea id={`verification-notes-${hub.id}`} value={requestNotes} maxLength={5000} rows={3} onChange={(event) => setRequestNotes(event.currentTarget.value)} />
        <button type="submit" disabled={submitting}>{submitting ? 'Sending request…' : verificationStatus === 'rejected' ? 'Request verification again' : 'Request verification'}</button>
      </form>}
    </section>
  )
}
