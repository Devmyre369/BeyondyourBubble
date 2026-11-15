import type { EventChoice } from '../../../services/vibespaceApi'
import './event-card.css'

export interface EventCardProps {
  event: EventChoice
  onSelect?: (event: EventChoice) => void
}

function getEventDateTime(startsAt: string | null) {
  if (!startsAt) {
    return { date: 'Date to be announced', time: '' }
  }

  const date = new Date(startsAt)

  if (Number.isNaN(date.getTime())) {
    return { date: 'Date to be announced', time: '' }
  }

  return {
    date: new Intl.DateTimeFormat(undefined, {
      weekday: 'short',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    }).format(date),
    time: new Intl.DateTimeFormat(undefined, {
      hour: 'numeric',
      minute: '2-digit',
    }).format(date),
  }
}

export default function EventCard({ event, onSelect }: EventCardProps) {
  const { date, time } = getEventDateTime(event.starts_at)
  const location = [event.venue_name.trim(), event.city.trim()]
    .filter(Boolean)
    .join(', ')

  return (
    <article
      className="event-card"
      aria-labelledby={`event-card-title-${event.id}`}
    >
      <div className="event-card-cover" aria-hidden="true">
        <span className="event-card-cover-orb event-card-cover-orb-one" />
        <span className="event-card-cover-orb event-card-cover-orb-two" />
        <span className="event-card-cover-label">BEYOND YOUR BUBBLE</span>
        <span className="event-card-cover-mark">BYB</span>
      </div>

      <div className="event-card-content">
        <div className="event-card-meta">
          <span
            className="event-card-status"
            data-status={event.status}
            aria-label={`Event status: ${event.status}`}
          >
            {event.status === 'completed' ? 'Completed' : 'Published'}
          </span>
        </div>

        <h3 className="event-card-title" id={`event-card-title-${event.id}`}>
          {event.title}
        </h3>

        <dl className="event-card-details">
          <div className="event-card-detail">
            <dt>Date</dt>
            <dd>{date}</dd>
          </div>
          {time && (
            <div className="event-card-detail">
              <dt>Time</dt>
              <dd>{time}</dd>
            </div>
          )}
        </dl>

        <p className="event-card-location">
          <svg
            viewBox="0 0 20 20"
            fill="none"
            aria-hidden="true"
            focusable="false"
          >
            <path
              d="M16 8.3c0 4.1-6 9.2-6 9.2S4 12.4 4 8.3a6 6 0 1 1 12 0Z"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <circle cx="10" cy="8" r="2" stroke="currentColor" strokeWidth="1.5" />
          </svg>
          <span>{location || 'Location to be announced'}</span>
        </p>

        {onSelect && (
          <button
            className="event-card-action"
            type="button"
            onClick={() => onSelect(event)}
            aria-label={`Select ${event.title}`}
          >
            Select event
            <span aria-hidden="true">→</span>
          </button>
        )}
      </div>
    </article>
  )
}
