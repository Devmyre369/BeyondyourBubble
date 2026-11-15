import './events.css'

type EventsContentState = 'loading' | 'empty' | 'error'

function renderEventsContentState(state: EventsContentState) {
  switch (state) {
    case 'loading':
      return (
        <div className="events-state events-loading-state" role="status">
          <span className="events-loading-indicator" aria-hidden="true" />
          <p>Loading events...</p>
        </div>
      )
    case 'error':
      return (
        <div className="events-state events-error-state" role="alert">
          <h3>Events are temporarily unavailable</h3>
          <p>Please try again later.</p>
        </div>
      )
    case 'empty':
      return (
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
          <h3>Event discovery is coming soon</h3>
          <p>When events are ready to explore, you will find them here.</p>
        </div>
      )
  }
}

export default function EventsPage() {
  return (
    <div className="events-page">
      <header className="events-page-header">
        <span className="events-eyebrow">YOUR COMMUNITY, IN PERSON</span>
        <h1>Discover Events</h1>
        <p>
          Find new ways to connect and share experiences beyond your bubble.
        </p>
      </header>

      <div className="events-discovery-tools">
        <section className="events-tool-panel" aria-labelledby="events-search-title">
          <h2 id="events-search-title">Search events</h2>
          <input
            className="events-search-input"
            type="search"
            aria-label="Event search coming soon"
            placeholder="Search events (coming soon)"
            disabled
          />
        </section>

        <section className="events-tool-panel" aria-labelledby="events-filters-title">
          <h2 id="events-filters-title">Filters</h2>
          <p className="events-tool-placeholder">
            Event filters will be available here.
          </p>
        </section>
      </div>

      <section className="events-results" aria-labelledby="events-results-title">
        <div className="events-results-heading">
          <div>
            <span className="events-eyebrow">FIND YOUR NEXT EXPERIENCE</span>
            <h2 id="events-results-title">Events to explore</h2>
          </div>
        </div>
        <div className="events-results-content">
          {renderEventsContentState('empty')}
        </div>
      </section>
    </div>
  )
}
