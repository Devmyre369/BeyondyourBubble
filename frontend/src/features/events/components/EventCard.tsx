
import type { Event } from '../../../services/eventsApi'
import { Link } from 'react-router-dom'
import './event-card.css'

export interface EventCardProps {
  event: Event
  onSelect?: (event: Event) => void
  showRegistration?: boolean
  isAuthenticated?: boolean
  registrationLoading?: boolean
  onToggleRegistration?: (event: Event) => void
}

function getEventDateTime(startsAt: string | null, endsAt: string | null) {
  if (!startsAt) {
    return { date: 'Date to be announced', time: '' }
  }

  const date = new Date(startsAt)

  if (Number.isNaN(date.getTime())) {
    return { date: 'Date to be announced', time: '' }
  }

  const timeFormat = new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  })
  const startTime = timeFormat.format(date)
  const endDate = endsAt ? new Date(endsAt) : null
  const time = endDate && !Number.isNaN(endDate.getTime())
    ? `${startTime} – ${timeFormat.format(endDate)}`
    : startTime
  return {
    date: new Intl.DateTimeFormat(undefined, {
      weekday: 'short',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    }).format(date),
    time,
  }
}

function formatLabel(value: string) {
  return value
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export default function EventCard({ event, onSelect, showRegistration = false, isAuthenticated = false, registrationLoading = false, onToggleRegistration }: EventCardProps) {
  const { date, time } = getEventDateTime(event.starts_at, event.ends_at)

  const location =
    event.format === 'online'
      ? 'Online event'
      : [event.venue_name.trim(), event.city.trim()]
          .filter(Boolean)
          .join(', ') || 'Location to be announced'

  return (
    <article
      className="event-card"
      aria-labelledby={`event-card-title-${event.id}`}
    >
      <div
        className="event-card-cover"
        aria-hidden="true"
        style={{
          backgroundImage: event.cover_image_url
            ? `linear-gradient(125deg, rgba(20, 18, 25, 0.55), rgba(20, 18, 25, 0.25)), url("${event.cover_image_url}")`
            : undefined,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
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
          >
            {formatLabel(event.status)}
          </span>

          <span
            className="event-card-status"
            data-status="category"
          >
            {formatLabel(event.category)}
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

          <div className="event-card-detail">
            <dt>Format</dt>
            <dd>{formatLabel(event.format)}</dd>
          </div>
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
            <circle
              cx="10"
              cy="8"
              r="2"
              stroke="currentColor"
              strokeWidth="1.5"
            />
          </svg>
          <span>{location}</span>
        </p>

        <p className="event-card-organiser">
          Organised by {event.organising_hub_name}
        </p>

        {!onSelect && (
          <Link className="event-card-action" to={`/events/${encodeURIComponent(event.id)}`} aria-label={`View ${event.title}`}>
            View event <span aria-hidden="true">→</span>
          </Link>
        )}

        {showRegistration && (isAuthenticated ? (
          <button
            className="event-registration-action"
            type="button"
            disabled={registrationLoading}
            onClick={() => onToggleRegistration?.(event)}
          >
            {registrationLoading ? 'Updating…' : event.is_registered ? 'Cancel registration' : 'Join event'}
          </button>
        ) : (
          <Link className="event-registration-action" to="/login">Sign in to join</Link>
        ))}

        {onSelect && (
          <button
            className="event-card-action"
            type="button"
            onClick={() => onSelect(event)}
            aria-label={`View ${event.title}`}
          >
            View event
            <span aria-hidden="true">→</span>
          </button>
        )}
      </div>
    </article>
  )
}
