import axios from 'axios'
import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { eventsApi, type EventCategory, type ManagedEvent } from '../../../services/eventsApi'
import './hub-event-management.css'

function pretty(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function dateLabel(value: string | null) {
  if (!value) return 'Date to be announced'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Date to be announced' : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function errorLabel(error: unknown) {
  if (axios.isAxiosError(error) && error.response?.status === 403) return 'Your Hub management access has changed. Refresh the page to update your permissions.'
  return 'The event request failed. Please try again.'
}

const categories: EventCategory[] = ['technical', 'cultural', 'academic', 'sports', 'business', 'entertainment', 'social', 'political', 'workshop', 'other']

export default function HubEventManagement({ hubId }: { hubId: string }) {
  const [events, setEvents] = useState<ManagedEvent[]>([])
  const [nextPage, setNextPage] = useState<number | null>(1)
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState('')
  const [error, setError] = useState('')
  const [editing, setEditing] = useState<ManagedEvent | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState<EventCategory>('other')
  const [cancelId, setCancelId] = useState('')

  const loadEvents = useCallback(async (page = 1) => {
    try {
      const response = await eventsApi.getHubEvents(hubId, page)
      setEvents((previous) => page === 1 ? response.results : [...previous, ...response.results])
      const parsedNext = response.next ? Number(new URL(response.next, window.location.origin).searchParams.get('page')) : null
      setNextPage(parsedNext)
    } catch (loadError) {
      setError(errorLabel(loadError))
    } finally {
      setLoading(false)
    }
  }, [hubId])

  useEffect(() => {
    let active = true
    async function fetchEvents() {
      try {
        const response = await eventsApi.getHubEvents(hubId)
        if (!active) return
        setEvents(response.results)
        const parsedNext = response.next ? Number(new URL(response.next, window.location.origin).searchParams.get('page')) : null
        setNextPage(parsedNext)
      } catch (loadError) {
        if (active) setError(errorLabel(loadError))
      } finally {
        if (active) setLoading(false)
      }
    }
    void fetchEvents()
    return () => { active = false }
  }, [hubId])

  function startEdit(event: ManagedEvent) {
    setEditing(event)
    setTitle(event.title)
    setDescription(event.description)
    setCategory(event.category)
  }

  async function saveEdit(formEvent: FormEvent<HTMLFormElement>) {
    formEvent.preventDefault()
    if (!editing || busyId) return
    setBusyId(editing.id)
    setError('')
    try {
      const updated = await eventsApi.updateEvent(editing.id, { title: title.trim(), description: description.trim(), category })
      setEvents((previous) => previous.map((item) => item.id === updated.id ? updated : item))
      setEditing(null)
    } catch (saveError) {
      setError(errorLabel(saveError))
    } finally {
      setBusyId('')
    }
  }

  async function cancelEvent(eventId: string) {
    setBusyId(eventId)
    setError('')
    try {
      await eventsApi.cancelEvent(eventId)
      setEvents((previous) => previous.map((item) => item.id === eventId ? { ...item, status: 'cancelled' } : item))
      setCancelId('')
    } catch (cancelError) {
      setError(errorLabel(cancelError))
    } finally {
      setBusyId('')
    }
  }

  return (
    <section className="hub-event-management" aria-labelledby="hub-events-title" aria-busy={loading}>
      <header className="hub-event-management-header">
        <div><span>HUB MANAGEMENT</span><h2 id="hub-events-title">Events</h2><p>Changes to approved events are sent back to BYB moderation.</p></div>
        <Link to={`/hubs/${encodeURIComponent(hubId)}/events/create`}>+ Host an event</Link>
      </header>
      {error && <p className="hub-event-error" role="alert">{error}</p>}
      {loading && events.length === 0 && <p className="hub-event-state" role="status">Loading Hub events…</p>}
      {!loading && events.length === 0 && !error && <p className="hub-event-state">No events have been submitted for this Hub yet.</p>}
      <div className="hub-event-list">
        {events.map((event) => (
          <article className="hub-event-row" key={event.id}>
            <div className="hub-event-row-image">{event.cover_image_url && <img src={event.cover_image_url} alt="" />}</div>
            <div className="hub-event-row-main">
              <div className="hub-event-row-top"><h3>{event.title}</h3><span className={`hub-event-status status-${event.moderation_status}`}>{pretty(event.moderation_status)}</span><span className={`hub-event-status status-${event.status}`}>{pretty(event.status)}</span></div>
              <p>{pretty(event.category)} · {dateLabel(event.starts_at)} · submitted by @{event.created_by_username}</p>
              {event.reviewed_at && <p className="hub-event-review-summary">Last reviewed {dateLabel(event.reviewed_at)}{event.reviewed_by_username ? ` by @${event.reviewed_by_username}` : ''}{event.review_notes ? ` · ${event.review_notes}` : ''}</p>}
              {event.moderation_history?.length > 0 && <details className="hub-event-history"><summary>Review history ({event.moderation_history.length})</summary>{event.moderation_history.map((review) => <p key={review.id}>{pretty(review.decision)} · {dateLabel(review.reviewed_at)}{review.reviewer_username ? ` by @${review.reviewer_username}` : ''}{review.review_notes ? ` — ${review.review_notes}` : ''}</p>)}</details>}
              <div className="hub-event-row-actions">
                {event.status === 'published' && <Link to={`/events/${encodeURIComponent(event.id)}`}>View public event</Link>}
                {event.status !== 'cancelled' && event.status !== 'completed' && <button type="button" onClick={() => startEdit(event)} disabled={Boolean(busyId)}>Edit details</button>}
                {event.status === 'published' && event.moderation_status === 'approved' && (cancelId === event.id ? <><span>Cancel this published event?</span><button type="button" className="danger" onClick={() => void cancelEvent(event.id)} disabled={Boolean(busyId)}>{busyId === event.id ? 'Cancelling…' : 'Confirm cancel'}</button><button type="button" onClick={() => setCancelId('')}>Keep event</button></> : <button type="button" className="danger" onClick={() => setCancelId(event.id)} disabled={Boolean(busyId)}>Cancel event</button>)}
              </div>
            </div>
          </article>
        ))}
      </div>
      {nextPage && !loading && <button className="hub-event-load-more" type="button" onClick={() => { setLoading(true); void loadEvents(nextPage) }}>Load more events</button>}
      {editing && <div className="hub-event-modal-backdrop" role="presentation"><section className="hub-event-edit-dialog" role="dialog" aria-modal="true" aria-labelledby="hub-event-edit-title"><button type="button" className="hub-event-modal-close" onClick={() => setEditing(null)} aria-label="Close">×</button><span>EVENT DETAILS</span><h3 id="hub-event-edit-title">Edit event</h3>{editing.moderation_status === 'approved' && <p className="hub-event-review-summary">Saving changes sends this event back to BYB moderation.</p>}<form onSubmit={(event) => void saveEdit(event)}><label htmlFor="hub-event-title">Title</label><input id="hub-event-title" value={title} maxLength={200} required onChange={(event) => setTitle(event.currentTarget.value)} /><label htmlFor="hub-event-category">Category</label><select id="hub-event-category" value={category} onChange={(event) => setCategory(event.currentTarget.value as EventCategory)}>{categories.map((value) => <option key={value} value={value}>{pretty(value)}</option>)}</select><label htmlFor="hub-event-description">Description</label><textarea id="hub-event-description" value={description} rows={5} onChange={(event) => setDescription(event.currentTarget.value)} /><div className="hub-event-row-actions"><button type="submit" disabled={Boolean(busyId)}>{busyId ? 'Saving…' : 'Save event details'}</button><button type="button" onClick={() => setEditing(null)} disabled={Boolean(busyId)}>Cancel</button></div></form></section></div>}
    </section>
  )
}
