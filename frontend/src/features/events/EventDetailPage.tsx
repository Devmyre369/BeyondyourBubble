import axios from 'axios'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { eventsApi, type Event } from '../../services/eventsApi'
import './event-detail.css'

function formatDateTime(value: string | null, options: Intl.DateTimeFormatOptions) {
  if (!value) return 'To be announced'
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? 'To be announced'
    : new Intl.DateTimeFormat(undefined, options).format(date)
}

function label(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (character) => character.toUpperCase())
}

export default function EventDetailPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const [event, setEvent] = useState<Event | null>(null)
  const [loadedEventId, setLoadedEventId] = useState('')
  const [state, setState] = useState<'ready' | 'not-found' | 'error'>('ready')

  useEffect(() => {
    let active = true
    if (!eventId) return
    void eventsApi.getEvent(eventId).then((result) => {
      if (!active) return
      setEvent(result)
      setLoadedEventId(eventId)
      setState('ready')
    }).catch((error: unknown) => {
      if (!active) return
      setLoadedEventId(eventId)
      setState(axios.isAxiosError(error) && error.response?.status === 404 ? 'not-found' : 'error')
    })
    return () => { active = false }
  }, [eventId])

  const isLoading = loadedEventId !== eventId
  if (isLoading || state !== 'ready' || !event) {
    return (
      <section className="event-detail-page" aria-busy={isLoading}>
        <Link className="event-detail-back" to="/events">← Back to events</Link>
        <div className="event-detail-state" role={state === 'error' ? 'alert' : 'status'}>
          {isLoading ? 'Loading event…' : state === 'not-found' ? 'This event is unavailable or has not been approved for public viewing.' : 'We could not load this event. Please try again.'}
        </div>
      </section>
    )
  }

  const dateOptions: Intl.DateTimeFormatOptions = { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }
  const timeOptions: Intl.DateTimeFormatOptions = { hour: 'numeric', minute: '2-digit' }

  return (
    <main className="event-detail-page">
      <Link className="event-detail-back" to="/events">← Back to events</Link>
      <article className="event-detail-card">
        <div className="event-detail-cover">
          {event.cover_image_url && <img src={event.cover_image_url} alt={`${event.title} cover`} />}
          <span className="event-detail-cover-mark">BYB EVENTS</span>
        </div>
        <div className="event-detail-body">
          <div className="event-detail-meta">
            <span>{label(event.category)}</span><span>{label(event.format)}</span><span>{label(event.status)}</span>
          </div>
          <h1>{event.title}</h1>
          <p className="event-detail-organiser">
            Organised by <Link to={`/hubs/${encodeURIComponent(event.organising_hub)}`}>{event.organising_hub_name}</Link>
            {event.created_by_username && <> · hosted by <Link to={`/users/${encodeURIComponent(event.created_by_username)}`}>@{event.created_by_username}</Link></>}
          </p>
          <dl className="event-detail-facts">
            <div><dt>Starts</dt><dd>{formatDateTime(event.starts_at, dateOptions)}{event.starts_at && ` · ${formatDateTime(event.starts_at, timeOptions)}`}</dd></div>
            <div><dt>Ends</dt><dd>{formatDateTime(event.ends_at, dateOptions)}{event.ends_at && ` · ${formatDateTime(event.ends_at, timeOptions)}`}</dd></div>
            <div><dt>Location</dt><dd>{event.format === 'online' ? 'Online' : [event.venue_name, event.city].filter(Boolean).join(', ') || 'To be announced'}</dd></div>
            {event.venue_address && <div><dt>Address</dt><dd>{event.venue_address}</dd></div>}
          </dl>
          <section className="event-detail-description">
            <h2>About this event</h2>
            <p>{event.description || 'The organiser has not added a description yet.'}</p>
          </section>
          {(event.online_join_url || event.online_access_instructions) && (
            <section className="event-detail-online">
              <h2>Joining information</h2>
              {event.online_access_instructions && <p>{event.online_access_instructions}</p>}
              {event.online_join_url && <a href={event.online_join_url} target="_blank" rel="noopener noreferrer">Open event link</a>}
            </section>
          )}
        </div>
      </article>
    </main>
  )
}
