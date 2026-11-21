import axios from 'axios'
import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext'
import { eventsApi, type EventCategory, type EventFormat, type EventModerationItem, type EventModerationParams, type EventModerationReviewResponse, type EventRejectionCategory } from '../../services/eventsApi'
import './event-moderation.css'

const categories: EventCategory[] = ['technical', 'cultural', 'academic', 'sports', 'business', 'entertainment', 'social', 'political', 'workshop', 'other']
const rejectionCategories: Array<{ value: EventRejectionCategory; label: string }> = [
  { value: 'incomplete', label: 'Incomplete information' },
  { value: 'unverifiable', label: 'Invalid or unverifiable details' },
  { value: 'duplicate', label: 'Duplicate event' },
  { value: 'misleading', label: 'Misleading information' },
  { value: 'policy_violation', label: 'Policy violation' },
  { value: 'inappropriate', label: 'Inappropriate content' },
  { value: 'other', label: 'Other' },
]

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
  const [pendingCount, setPendingCount] = useState(0)
  const [nextPage, setNextPage] = useState<number | null>(null)
  const [recentReviews, setRecentReviews] = useState<Array<{ item: EventModerationItem; result: EventModerationReviewResponse }>>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [reviewingId, setReviewingId] = useState('')
  const [rejectingId, setRejectingId] = useState('')
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [rejectionCategory, setRejectionCategory] = useState<Record<string, EventRejectionCategory | ''>>({})
  const [filters, setFilters] = useState({ search: '', category: '', format: '', city: '', hub: '', submitted_after: '', submitted_before: '' })
  const [activeFilters, setActiveFilters] = useState<EventModerationParams>({})

  const loadQueue = useCallback(async (page = 1, append = false, params = activeFilters) => {
    if (append) setLoadingMore(true)
    else setLoading(true)
    setError('')
    try {
      const response = await eventsApi.getModerationQueue(page, params)
      setItems((previous) => append ? [...previous, ...response.results] : response.results)
      setPendingCount(response.count)
      setNextPage(response.next ? Number(new URL(response.next, window.location.origin).searchParams.get('page')) : null)
    } catch (loadError) {
      setError(getError(loadError))
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [activeFilters])

  useEffect(() => {
    const timer = setTimeout(() => { void loadQueue(1) }, 0)
    return () => clearTimeout(timer)
  }, [loadQueue])

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextFilters: EventModerationParams = {
      search: filters.search.trim() || undefined,
      category: (filters.category || undefined) as EventCategory | undefined,
      format: (filters.format || undefined) as EventFormat | undefined,
      city: filters.city.trim() || undefined,
      hub: filters.hub.trim() || undefined,
      submitted_after: filters.submitted_after || undefined,
      submitted_before: filters.submitted_before || undefined,
    }
    setActiveFilters(nextFilters)
  }

  function clearFilters() {
    const empty = { search: '', category: '', format: '', city: '', hub: '', submitted_after: '', submitted_before: '' }
    setFilters(empty)
    setActiveFilters({})
  }

  async function review(item: EventModerationItem, decision: 'approve' | 'reject') {
    const reviewNotes = (notes[item.id] || '').trim()
    const category = rejectionCategory[item.id]
    if (decision === 'reject' && (!reviewNotes || !category)) {
      setError('Choose a rejection category and explain what the organiser needs to change.')
      return
    }
    if (reviewingId) return
    setReviewingId(item.id)
    setError('')
    try {
      const result = await eventsApi.reviewEvent(item.id, {
        decision,
        review_notes: reviewNotes,
        ...(decision === 'reject' && category ? { review_category: category } : {}),
      })
      setRecentReviews((previous) => [{ item, result }, ...previous].slice(0, 8))
      setItems((previous) => previous.filter((entry) => entry.id !== item.id))
      setPendingCount((previous) => Math.max(0, previous - 1))
      setRejectingId('')
      setNotes((previous) => { const next = { ...previous }; delete next[item.id]; return next })
      setRejectionCategory((previous) => { const next = { ...previous }; delete next[item.id]; return next })
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
        <div className="event-moderation-section-heading"><div><span>AWAITING REVIEW</span><h2 id="pending-events-title">Pending submissions</h2></div><strong title="Pending events matching the current filters">{pendingCount}</strong></div>

        <form className="event-moderation-filters" onSubmit={applyFilters}>
          <label>Event title<input type="search" value={filters.search} onChange={(event) => setFilters((previous) => ({ ...previous, search: event.currentTarget.value }))} placeholder="Search titles" /></label>
          <label>Category<select value={filters.category} onChange={(event) => setFilters((previous) => ({ ...previous, category: event.currentTarget.value }))}><option value="">All categories</option>{categories.map((value) => <option key={value} value={value}>{value.replaceAll('_', ' ')}</option>)}</select></label>
          <label>Format<select value={filters.format} onChange={(event) => setFilters((previous) => ({ ...previous, format: event.currentTarget.value }))}><option value="">All formats</option><option value="offline">Offline</option><option value="online">Online</option><option value="hybrid">Hybrid</option></select></label>
          <label>City<input value={filters.city} onChange={(event) => setFilters((previous) => ({ ...previous, city: event.currentTarget.value }))} placeholder="Any city" /></label>
          <label>Organising Hub<input value={filters.hub} onChange={(event) => setFilters((previous) => ({ ...previous, hub: event.currentTarget.value }))} placeholder="Hub name or ID" /></label>
          <label>Submitted from<input type="date" value={filters.submitted_after} onChange={(event) => setFilters((previous) => ({ ...previous, submitted_after: event.currentTarget.value }))} /></label>
          <label>Submitted through<input type="date" value={filters.submitted_before} onChange={(event) => setFilters((previous) => ({ ...previous, submitted_before: event.currentTarget.value }))} /></label>
          <div className="event-moderation-filter-actions"><button type="submit" disabled={loading}>Apply filters</button><button type="button" className="quiet" onClick={clearFilters} disabled={loading}>Clear</button></div>
        </form>

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
                {item.venue_address && <p className="event-moderation-address">Address: {item.venue_address}</p>}
                {item.online_access_instructions && <p className="event-moderation-address">Private access instructions: {item.online_access_instructions}</p>}
                {item.online_join_url && <a className="event-moderation-link" href={item.online_join_url} target="_blank" rel="noopener noreferrer">Open joining link</a>}
                {item.moderation_history.length > 0 && <details className="event-moderation-prior-history"><summary>Previous moderation ({item.moderation_history.length})</summary>{item.moderation_history.map((review) => <p key={review.id}>{review.decision}{review.review_category ? ` · ${review.review_category.replaceAll('_', ' ')}` : ''} · {formatDate(review.reviewed_at)}{review.reviewer_username ? ` by @${review.reviewer_username}` : ''}{review.review_notes ? ` — ${review.review_notes}` : ''}</p>)}</details>}
                <label className="event-moderation-comment-label" htmlFor={`review-notes-${item.id}`}>Moderator comment {rejectingId === item.id ? '(required)' : '(optional)'}</label>
                <textarea id={`review-notes-${item.id}`} value={notes[item.id] || ''} onChange={(event) => setNotes((previous) => ({ ...previous, [item.id]: event.currentTarget.value }))} maxLength={5000} rows={3} />
                {rejectingId === item.id && <label className="event-moderation-reject-category">Rejection category<select value={rejectionCategory[item.id] || ''} onChange={(event) => setRejectionCategory((previous) => ({ ...previous, [item.id]: event.currentTarget.value as EventRejectionCategory | '' }))}><option value="">Choose a category</option>{rejectionCategories.map((category) => <option key={category.value} value={category.value}>{category.label}</option>)}</select></label>}
                <div className="event-moderation-actions">
                  <button type="button" className="approve" disabled={Boolean(reviewingId)} onClick={() => void review(item, 'approve')}>{reviewingId === item.id ? 'Saving…' : 'Approve and publish'}</button>
                  {rejectingId === item.id ? <><button type="button" className="reject" disabled={Boolean(reviewingId) || !(notes[item.id] || '').trim() || !rejectionCategory[item.id]} onClick={() => void review(item, 'reject')}>Confirm rejection</button><button type="button" className="quiet" disabled={Boolean(reviewingId)} onClick={() => setRejectingId('')}>Cancel</button></> : <button type="button" className="reject" disabled={Boolean(reviewingId)} onClick={() => { setError(''); setRejectingId(item.id) }}>Reject</button>}
                </div>
              </div>
            </article>
          ))}
        </div>
        {nextPage && !loading && <button className="event-moderation-retry" type="button" disabled={loadingMore} onClick={() => void loadQueue(nextPage, true)}>{loadingMore ? 'Loading…' : 'Load more pending events'}</button>}
        {!loading && error && !error.includes('Only BYB staff') && <button className="event-moderation-retry" type="button" onClick={() => void loadQueue(1)}>Retry queue</button>}
      </section>

      {recentReviews.length > 0 && <section className="event-moderation-section event-moderation-history" aria-labelledby="recent-reviews-title"><div className="event-moderation-section-heading"><div><span>REVIEW AUDIT</span><h2 id="recent-reviews-title">Recently reviewed</h2></div></div>{recentReviews.map(({ item, result }) => <article key={result.event_id} className="event-moderation-history-row"><div><strong>{item.title}</strong><p>{result.moderation_status} by @{user?.username || 'staff'} · {formatDate(result.reviewed_at)}</p>{result.review_category && <p>{result.review_category.replaceAll('_', ' ')}</p>}{result.review_notes && <p className="event-moderation-notes">{result.review_notes}</p>}</div><span className={result.moderation_status === 'approved' ? 'is-approved' : 'is-rejected'}>{result.moderation_status}</span></article>)}</section>}
    </main>
  )
}
