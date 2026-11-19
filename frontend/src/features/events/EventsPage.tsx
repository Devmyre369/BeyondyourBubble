
import { useEffect, useRef, useState } from 'react'
import { eventsApi } from '../../services/eventsApi'
import type {
  Event,
  EventCategory,
  EventFormat,
} from '../../services/eventsApi'
import EventCard from './components/EventCard'
import './events.css'

const categories: { value: EventCategory; label: string }[] = [
  { value: 'technical', label: 'Technical' },
  { value: 'cultural', label: 'Cultural' },
  { value: 'academic', label: 'Academic' },
  { value: 'sports', label: 'Sports' },
  { value: 'business', label: 'Business & Entrepreneurship' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'social', label: 'Social & Community' },
  { value: 'political', label: 'Political & Public Affairs' },
  { value: 'workshop', label: 'Workshop & Seminar' },
  { value: 'other', label: 'Other' },
]

export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([])
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [category, setCategory] = useState('')
  const [city, setCity] = useState('')
  const [format, setFormat] = useState('')
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [count, setCount] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [nextPage, setNextPage] = useState(2)
  const [retry, setRetry] = useState(0)

  const requestVersion = useRef(0)

  // Debounce search input to avoid sending a request for every keystroke.
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search.trim())
    }, 350)

    return () => window.clearTimeout(timer)
  }, [search])

  // Fetch events whenever a discovery filter changes.
  useEffect(() => {
    let active = true
    const requestId = ++requestVersion.current

    async function fetchEvents() {
      setLoading(true)
      setError('')
      setLoadingMore(false)

      try {
        const response = await eventsApi.getEvents({
          search: debouncedSearch || undefined,
          category: (category || undefined) as EventCategory | undefined,
          city: city.trim() || undefined,
          format: (format || undefined) as EventFormat | undefined,
          page: 1,
        })

        if (!active || requestId !== requestVersion.current) return

        const results = Array.isArray(response?.results)
          ? response.results
          : []

        setEvents(results)
        setCount(Number(response?.count) || results.length)
        setHasMore(Boolean(response?.next))
        setNextPage(2)
      } catch {
        if (!active || requestId !== requestVersion.current) return

        setEvents([])
        setCount(0)
        setHasMore(false)
        setError('We could not load events. Please check your connection and try again.')
      } finally {
        if (active && requestId === requestVersion.current) {
          setLoading(false)
        }
      }
    }

    fetchEvents()

    return () => {
      active = false
    }
  }, [debouncedSearch, category, city, format, retry])

  async function loadMoreEvents() {
    const requestId = requestVersion.current

    setLoadingMore(true)
    setError('')

    try {
      const response = await eventsApi.getEvents({
        search: debouncedSearch || undefined,
        category: (category || undefined) as EventCategory | undefined,
        city: city.trim() || undefined,
        format: (format || undefined) as EventFormat | undefined,
        page: nextPage,
      })

      if (requestId !== requestVersion.current) return

      const results = Array.isArray(response?.results)
        ? response.results
        : []

      setEvents((previous) => [
        ...(Array.isArray(previous) ? previous : []),
        ...results,
      ])
      setHasMore(Boolean(response?.next))
      setNextPage((previous) => previous + 1)
    } catch {
      if (requestId === requestVersion.current) {
        setError('Could not load more events. Please try again.')
      }
    } finally {
      if (requestId === requestVersion.current) {
        setLoadingMore(false)
      }
    }
  }

  function clearFilters() {
    setSearch('')
    setDebouncedSearch('')
    setCategory('')
    setCity('')
    setFormat('')
  }

  const hasActiveFilters = Boolean(
    search || category || city || format,
  )

  return (
    <div className="events-page">
      <header className="events-page-header">
        <span className="events-eyebrow">YOUR COMMUNITY, IN PERSON</span>
        <h1>Discover Events</h1>
        <p>
          Find new ways to connect, discover experiences, and explore
          what is happening beyond your bubble.
        </p>
      </header>

      <div className="events-discovery-tools">
        <section
          className="events-tool-panel"
          aria-labelledby="events-search-title"
        >
          <h2 id="events-search-title">Search events</h2>
          <input
            className="events-search-input"
            type="search"
            id="events-search"
            name="search"
            aria-label="Search events"
            placeholder="Search by event name or description..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </section>

        <section
          className="events-tool-panel"
          aria-labelledby="events-filters-title"
        >
          <h2 id="events-filters-title">Filter events</h2>

          <div className="events-filter-controls">
            <select
              className="events-filter-select"
              id="events-category"
              name="category"
              aria-label="Filter by category"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              <option value="">All categories</option>
              {categories.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>

            <select
              className="events-filter-select"
              id="events-format"
              name="format"
              aria-label="Filter by event format"
              value={format}
              onChange={(event) => setFormat(event.target.value)}
            >
              <option value="">All formats</option>
              <option value="offline">Offline</option>
              <option value="online">Online</option>
              <option value="hybrid">Hybrid</option>
            </select>

            <input
              className="events-filter-input"
              type="text"
              id="events-city"
              name="city"
              aria-label="Filter by city"
              placeholder="Enter city"
              value={city}
              onChange={(event) => setCity(event.target.value)}
            />
          </div>

          {hasActiveFilters && (
            <button
              className="events-clear-filters"
              type="button"
              onClick={clearFilters}
            >
              Clear filters
            </button>
          )}
        </section>
      </div>

      <section
        className="events-results"
        aria-labelledby="events-results-title"
      >
        <div className="events-results-heading">
          <div>
            <span className="events-eyebrow">
              FIND YOUR NEXT EXPERIENCE
            </span>
            <h2 id="events-results-title">Events to explore</h2>
            {!loading && (
              <p className="events-results-count">
                {count} {count === 1 ? 'event' : 'events'} found
              </p>
            )}
          </div>
        </div>

        <div className="events-results-content">
          {loading ? (
            <div className="events-state events-loading-state" role="status">
              <span
                className="events-loading-indicator"
                aria-hidden="true"
              />
              <p>Discovering events...</p>
            </div>
          ) : error && events.length === 0 ? (
            <div className="events-state events-error-state" role="alert">
              <h3>Events are temporarily unavailable</h3>
              <p>{error}</p>
              <button
                className="events-retry-button"
                type="button"
                onClick={() => setRetry((previous) => previous + 1)}
              >
                Try again
              </button>
            </div>
          ) : events.length === 0 ? (
            <div className="events-state events-empty-state" role="status">
              <svg
                className="events-empty-icon"
                viewBox="0 0 48 48"
                fill="none"
                aria-hidden="true"
              >
                <rect
                  x="7"
                  y="11"
                  width="34"
                  height="30"
                  rx="6"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
                <path
                  d="M16 7v8M32 7v8M7 20h34"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
                <path
                  d="M17 28h.01M24 28h.01M31 28h.01M17 34h.01M24 34h.01"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              </svg>
              <h3>
                {hasActiveFilters
                  ? 'No events match your filters'
                  : 'No events to explore yet'}
              </h3>
              <p>
                {hasActiveFilters
                  ? 'Try changing your search or removing some filters.'
                  : 'Approved and published events will appear here.'}
              </p>
            </div>
          ) : (
            <>
              <div className="events-grid">
                {events.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </div>

              {error && (
                <p className="events-inline-error" role="alert">
                  {error}
                </p>
              )}

              {hasMore && (
                <div className="events-load-more">
                  <button
                    className="events-load-more-button"
                    type="button"
                    onClick={loadMoreEvents}
                    disabled={loadingMore}
                  >
                    {loadingMore ? 'Loading...' : 'Load more events'}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </div>
  )
}
