import axios from 'axios'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext'
import { eventsApi, type EventModerationItem, type EventModerationReviewResponse } from '../../services/eventsApi'
import './event-moderation.css'

function formatDate(value: string | null) {
  if (!value) return 'Date to be announced'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Date to be announced' : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function getError(error: unknown) {
  if (axios.isAxiosError(error) && error.response?.status === 403) return 'Only BYB staff can access event moderation.'
  return 'Could not load or update the moderation queue. Please try again.'
}

export default function EventModerationPage() {
  const { user } = useAuth()
  const [items, setItems] = useState<EventModerationItem[]>([])
  const [nextPage, setNextPage] = useState<number | null>(null)
  const [recentReviews, setRecentReviews] = useState<Array<{ item: EventModerationItem; result: EventModerationReviewResponse }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reviewingId, setReviewingId] = useState('')
  const [rejectingId, setRejectingId] = useState('')
  const [notes, setNotes] = useState<Record<string, string>>({})

  const loadQueue = useCallback(async () => {
    try {
      const response = await eventsApi.getModerationQueue()
      setItems(response.results)
      setNextPage(response.next ? Number(new URL(response.next, window.location.origin).searchParams.get('page')) : null)
    } catch (loadError) {
      setError(getError(loadError))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    async function fetchQueue() {
      try {
        const response = await eventsApi.getModerationQueue()
        if (active) {
          setItems(response.results)
          setNextPage(response.next ? Number(new URL(response.next, window.location.origin).searchParams.get('page')) : null)
        }
      } catch (loadError) {
        if (active) setError(getError(loadError))
      } finally {
        if (active) setLoading(false)
      }
    }
    void fetchQueue()
    return () => { active = false }
  }, [])

  async function review(item: EventModerationItem, decision: 'approve' | 'reject') {
    const reviewNotes = (notes[item.id] || '').trim()
    if (decision === 'reject' && !reviewNotes) {
      setError('Add a reason before rejecting an event.')
      return
    }
    setReviewingId(item.id)
    setError('')
    try {
      const result = await eventsApi.reviewEvent(item.id, { decision, review_notes: reviewNotes })
      setRecentReviews((previous) => [{ item, result }, ...previous].slice(0, 8))
      setItems((previous) => previous.filter((entry) => entry.id !== item.id))
      setRejectingId('')
      setNotes((previous) => { const next = { ...previous }; delete next[item.id]; return next })
    } catch (reviewError) {
      setError(getError(reviewError))
    } finally {
      setReviewingId('')
    }
  }

  return (
    <main className="event-moderation-page">
      <header className="event-moderation-header">
        <Link to="/events">← Event discovery</Link>
        <span className="event-moderation-eyebrow">BYB STAFF WORKSPACE</span>
        <h1>Event moderation</h1>
        <p>Review Hub submissions before they appear in public discovery.</p>
        {user?.username && <span className="event-moderation-reviewer">Signed in as @{user.username}</span>}
      </header>

      {error && <p className="event-moderation-error" role="alert">{error}</p>}
      <section className="event-moderation-section" aria-labelledby="pending-events-title" aria-busy={loading}>
        <div className="event-moderation-section-heading"><div><span>AWAITING REVIEW</span><h2 id="pending-events-title">Pending submissions</h2></div><strong>{items.length}</strong></div>
        {loading && <p role="status" className="event-moderation-empty">Loading moderation queue…</p>}
        {!loading && error.includes('Only BYB staff') && <p className="event-moderation-empty">Staff access required.</p>}
        {!loading && !error && items.length === 0 && <p className="event-moderation-empty">There are no events waiting for review.</p>}
        <div className="event-moderation-list">
          {items.map((item) => (
            <article className="event-moderation-card" key={item.id}>
              <div className="event-moderation-cover">{item.cover_image_url ? <img src={item.cover_image_url} alt={`${item.title} cover`} /> : <span>BYB EVENT</span>}</div>
              <div className="event-moderation-content">
                <div className="event-moderation-card-meta"><span className="is-pending">Pending</span><span>{item.category}</span><span>{item.format}</span></div>
                <h3>{item.title}</h3>
                <p className="event-moderation-byline">By @{item.created_by_username} for <Link to={`/hubs/${item.organising_hub}`}>{item.organising_hub_name}</Link></p>
                <p className="event-moderation-description">{item.description || 'No description provided.'}</p>
                <dl><div><dt>Starts</dt><dd>{formatDate(item.starts_at)}</dd></div><div><dt>Ends</dt><dd>{formatDate(item.ends_at)}</dd></div><div><dt>Location</dt><dd>{item.format === 'online' ? 'Online' : [item.venue_name, item.city].filter(Boolean).join(', ') || 'Not provided'}</dd></div><div><dt>Submitted</dt><dd>{formatDate(item.created_at)}</dd></div></dl>
                {item.venue_address && <p className="event-moderation-address">{item.venue_address}</p>}
                {item.online_access_instructions && <p className="event-moderation-address">{item.online_access_instructions}</p>}
                {item.online_join_url && <a className="event-moderation-link" href={item.online_join_url} target="_blank" rel="noopener noreferrer">Open joining link</a>}
                {rejectingId === item.id && <div className="event-moderation-reject-form"><label htmlFor={`review-notes-${item.id}`}>Reason for rejection (required)</label><textarea id={`review-notes-${item.id}`} value={notes[item.id] || ''} onChange={(event) => setNotes((previous) => ({ ...previous, [item.id]: event.currentTarget.value }))} maxLength={5000} rows={3} /></div>}
                <div className="event-moderation-actions">
                  <button type="button" className="approve" disabled={Boolean(reviewingId)} onClick={() => void review(item, 'approve')}>{reviewingId === item.id ? 'Saving…' : 'Approve and publish'}</button>
                  {rejectingId === item.id ? <><button type="button" className="reject" disabled={Boolean(reviewingId) || !(notes[item.id] || '').trim()} onClick={() => void review(item, 'reject')}>Confirm rejection</button><button type="button" className="quiet" disabled={Boolean(reviewingId)} onClick={() => setRejectingId('')}>Cancel</button></> : <button type="button" className="reject" disabled={Boolean(reviewingId)} onClick={() => { setError(''); setRejectingId(item.id) }}>Reject</button>}
                </div>
              </div>
            </article>
          ))}
        </div>
        {nextPage && !loading && <button className="event-moderation-retry" type="button" onClick={() => {
          setLoading(true)
          void eventsApi.getModerationQueue(nextPage).then((response) => {
            setItems((previous) => [...previous, ...response.results])
            setNextPage(response.next ? Number(new URL(response.next, window.location.origin).searchParams.get('page')) : null)
          }).catch((loadError: unknown) => setError(getError(loadError))).finally(() => setLoading(false))
        }}>Load more pending events</button>}
        {!loading && error && !error.includes('Only BYB staff') && <button className="event-moderation-retry" type="button" onClick={() => { setLoading(true); setError(''); void loadQueue() }}>Retry queue</button>}
      </section>

      {recentReviews.length > 0 && <section className="event-moderation-section event-moderation-history" aria-labelledby="recent-reviews-title"><div className="event-moderation-section-heading"><div><span>REVIEW AUDIT</span><h2 id="recent-reviews-title">Recently reviewed</h2></div></div>{recentReviews.map(({ item, result }) => <article key={result.event_id} className="event-moderation-history-row"><div><strong>{item.title}</strong><p>{result.moderation_status} by @{user?.username || 'staff'} · {formatDate(result.reviewed_at)}</p>{result.review_notes && <p className="event-moderation-notes">{result.review_notes}</p>}</div><span className={result.moderation_status === 'approved' ? 'is-approved' : 'is-rejected'}>{result.moderation_status}</span></article>)}</section>}
    </main>
  )
}
