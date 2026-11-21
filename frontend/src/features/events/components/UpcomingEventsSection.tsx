import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'
import { useAuth } from '../../../context/AuthContext'
import { eventsApi, type Event } from '../../../services/eventsApi'
import EventCard from './EventCard'
import './upcoming-events.css'

interface Props {
  hubId?: string
  title?: string
  description?: string
}

export default function UpcomingEventsSection({
  hubId,
  title = 'Upcoming Events',
  description = 'Find something happening in your community.',
}: Props) {
  const { isAuthenticated } = useAuth()
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [nextPage, setNextPage] = useState<number | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [busyIds, setBusyIds] = useState<Record<string, boolean>>({})
  const [retry, setRetry] = useState(0)

  const load = useCallback(async (page = 1, append = false) => {
    if (append) setLoadingMore(true)
    else setLoading(true)
    setError('')
    try {
      const response = await eventsApi.getEvents({ upcoming: true, hub_id: hubId, page })
      setEvents((previous) => append ? [...previous, ...response.results] : response.results)
      setNextPage(response.next
        ? Number(new URL(response.next, window.location.origin).searchParams.get('page')) || page + 1
        : null)
    } catch (loadError) {
      setError(axios.isAxiosError(loadError) && loadError.response?.status === 401
        ? 'Sign in to view upcoming events.'
        : 'Upcoming events could not be loaded. Please try again.')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [hubId])

  useEffect(() => {
    const timer = setTimeout(() => { void load(1) }, 0)
    return () => clearTimeout(timer)
  }, [load, retry])

  async function toggleRegistration(event: Event) {
    if (busyIds[event.id]) return
    setBusyIds((previous) => ({ ...previous, [event.id]: true }))
    setError('')
    try {
      const result = event.is_registered
        ? await eventsApi.cancelRegistration(event.id)
        : await eventsApi.registerForEvent(event.id)
      setEvents((previous) => previous.map((item) => item.id === event.id
        ? { ...item, is_registered: result.is_registered }
        : item))
    } catch (requestError) {
      setError(axios.isAxiosError(requestError) && requestError.response?.status === 401
        ? 'Please sign in again to manage your event registration.'
        : 'Your registration could not be updated. Please try again.')
    } finally {
      setBusyIds((previous) => ({ ...previous, [event.id]: false }))
    }
  }

  return (
    <section className="upcoming-events-section" aria-labelledby={`upcoming-events-${hubId || 'home'}`} aria-busy={loading}>
      <header className="upcoming-events-heading">
        <div><span>WHAT’S HAPPENING</span><h2 id={`upcoming-events-${hubId || 'home'}`}>{title}</h2><p>{description}</p></div>
      </header>
      {error && <div className="upcoming-events-error" role="alert">{error}<button type="button" onClick={() => setRetry((value) => value + 1)}>Try again</button></div>}
      {loading ? <p className="upcoming-events-state" role="status">Loading upcoming events…</p>
        : events.length === 0 ? <p className="upcoming-events-state">No upcoming events right now.</p>
          : <div className="upcoming-events-grid">{events.map((event) => <EventCard key={event.id} event={event} showRegistration isAuthenticated={isAuthenticated} registrationLoading={Boolean(busyIds[event.id])} onToggleRegistration={(selected) => void toggleRegistration(selected)} />)}</div>}
      {nextPage && !loading && <button className="upcoming-events-more" type="button" disabled={loadingMore} onClick={() => void load(nextPage, true)}>{loadingMore ? 'Loading…' : 'More upcoming events'}</button>}
    </section>
  )
}
