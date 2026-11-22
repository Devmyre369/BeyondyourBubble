
import axios from 'axios'
import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import {
  eventsApi,
  type EventCategory,
  type EventFormat,
  type EventUpdateRequest,
  type ManagedEvent,
} from '../../../services/eventsApi'

import './hub-event-management.css'

type EditValues = {
  title: string
  description: string
  category: EventCategory
  format: EventFormat
  starts_at: string
  ends_at: string
  venue_name: string
  venue_address: string
  city: string
  online_join_url: string
  online_access_instructions: string
}

const categories: EventCategory[] = [
  'technical',
  'cultural',
  'academic',
  'sports',
  'business',
  'entertainment',
  'social',
  'political',
  'workshop',
  'other',
]

const formats: EventFormat[] = ['offline', 'online', 'hybrid']

const MAX_CANCELLATION_REASON_LENGTH = 1000

function pretty(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function dateLabel(value: string | null) {
  if (!value) return 'Date to be announced'

  const date = new Date(value)

  return Number.isNaN(date.getTime())
    ? 'Date to be announced'
    : new Intl.DateTimeFormat(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      }).format(date)
}

function toLocalInput(value: string | null) {
  if (!value) return ''

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return ''

  return new Date(
    date.getTime() - date.getTimezoneOffset() * 60000,
  ).toISOString().slice(0, 19)
}

function errorLabel(error: unknown) {
  if (
    axios.isAxiosError(error) &&
    error.response?.status === 403
  ) {
    return 'Your Hub management access has changed. Refresh the page to update your permissions.'
  }

  if (axios.isAxiosError(error) && error.response?.data) {
    const data = error.response.data as Record<string, unknown>

    const first = Object.values(data).find(
      (value) => typeof value === 'string' || Array.isArray(value),
    )

    if (typeof first === 'string') return first

    if (Array.isArray(first) && typeof first[0] === 'string') {
      return first[0]
    }
  }

  return 'The event request failed. Please try again.'
}

function valuesFromEvent(event: ManagedEvent): EditValues {
  return {
    title: event.title,
    description: event.description,
    category: event.category,
    format: event.format,
    starts_at: toLocalInput(event.starts_at),
    ends_at: toLocalInput(event.ends_at),
    venue_name: event.venue_name,
    venue_address: event.venue_address,
    city: event.city,
    online_join_url: event.online_join_url,
    online_access_instructions: event.online_access_instructions,
  }
}

function toRequest(values: EditValues): EventUpdateRequest {
  return {
    title: values.title.trim(),
    description: values.description.trim(),
    category: values.category,
    format: values.format,
    starts_at: new Date(values.starts_at).toISOString(),
    ends_at: new Date(values.ends_at).toISOString(),
    venue_name: values.venue_name.trim(),
    venue_address: values.venue_address.trim(),
    city: values.city.trim(),
    online_join_url: values.online_join_url.trim(),
    online_access_instructions: values.online_access_instructions.trim(),
  }
}

export default function HubEventManagement({
  hubId,
}: {
  hubId: string
}) {
  const [events, setEvents] = useState<ManagedEvent[]>([])
  const [nextPage, setNextPage] = useState<number | null>(1)
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState('')
  const [error, setError] = useState('')

  const [editing, setEditing] = useState<ManagedEvent | null>(null)
  const [values, setValues] = useState<EditValues | null>(null)

  const [coverFile, setCoverFile] = useState<File | null>(null)
  const [coverPreview, setCoverPreview] = useState('')

  const [cancelId, setCancelId] = useState('')
  const [cancelReason, setCancelReason] = useState('')

  const loadEvents = useCallback(async (page = 1) => {
    try {
      const response = await eventsApi.getHubEvents(hubId, page)

      setEvents((previous) =>
        page === 1
          ? response.results
          : [...previous, ...response.results],
      )

      setNextPage(
        response.next
          ? Number(
              new URL(
                response.next,
                window.location.origin,
              ).searchParams.get('page'),
            )
          : null,
      )
    } catch (loadError) {
      setError(errorLabel(loadError))
    } finally {
      setLoading(false)
    }
  }, [hubId])

  useEffect(() => {
    let active = true

    eventsApi.getHubEvents(hubId)
      .then((response) => {
        if (!active) return

        setEvents(response.results)

        setNextPage(
          response.next
            ? Number(
                new URL(
                  response.next,
                  window.location.origin,
                ).searchParams.get('page'),
              )
            : null,
        )
      })
      .catch((loadError: unknown) => {
        if (active) setError(errorLabel(loadError))
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [hubId])

  useEffect(
    () => () => {
      if (coverPreview) URL.revokeObjectURL(coverPreview)
    },
    [coverPreview],
  )

  function startEdit(event: ManagedEvent) {
    setEditing(event)
    setValues(valuesFromEvent(event))
    setCoverFile(null)
    setCoverPreview('')
    setError('')
    setCancelId('')
    setCancelReason('')
  }

  function closeEdit() {
    if (busyId) return

    setEditing(null)
    setValues(null)
    setCoverFile(null)
    setCoverPreview('')
  }

  async function saveEdit(formEvent: FormEvent<HTMLFormElement>) {
    formEvent.preventDefault()

    if (!editing || !values || busyId) return

    const starts = new Date(values.starts_at)
    const ends = new Date(values.ends_at)

    if (
      Number.isNaN(starts.getTime()) ||
      Number.isNaN(ends.getTime()) ||
      ends <= starts
    ) {
      setError('The event end must be after its start.')
      return
    }

    if (
      (values.format === 'offline' || values.format === 'hybrid') &&
      (
        !values.venue_name.trim() ||
        !values.venue_address.trim() ||
        !values.city.trim()
      )
    ) {
      setError(
        'Venue name, full address, and city are required for offline and hybrid events.',
      )
      return
    }

    if (
      (values.format === 'online' || values.format === 'hybrid') &&
      !values.online_join_url.trim()
    ) {
      setError(
        'An online meeting URL is required for online and hybrid events.',
      )
      return
    }

    setBusyId(editing.id)
    setError('')

    try {
      let updated = await eventsApi.updateEvent(
        editing.id,
        toRequest(values),
      )

      setEvents((previous) =>
        previous.map((item) =>
          item.id === updated.id ? updated : item,
        ),
      )

      if (coverFile) {
        try {
          await eventsApi.uploadEventCoverImage(
            editing.id,
            coverFile,
          )

          updated = await eventsApi.getManagedEvent(editing.id)

          setEvents((previous) =>
            previous.map((item) =>
              item.id === updated.id ? updated : item,
            ),
          )
        } catch (uploadError) {
          setEditing(updated)
          setValues(valuesFromEvent(updated))

          setError(
            `Event details were saved, but its cover image was not replaced: ${errorLabel(uploadError)}`,
          )

          return
        }
      }

      setEditing(null)
      setValues(null)
      setCoverFile(null)
      setCoverPreview('')
    } catch (saveError) {
      setError(errorLabel(saveError))
    } finally {
      setBusyId('')
    }
  }

  function startCancellation(eventId: string) {
    setCancelId(eventId)
    setCancelReason('')
    setError('')
  }

  function closeCancellation() {
    if (busyId) return

    setCancelId('')
    setCancelReason('')
    setError('')
  }

  async function cancelEvent(eventId: string) {
    if (busyId) return

    const reason = cancelReason.trim()

    if (!reason) {
      setError('Please provide a reason for cancelling this event.')
      return
    }

    if (reason.length > MAX_CANCELLATION_REASON_LENGTH) {
      setError(
        `The cancellation reason cannot exceed ${MAX_CANCELLATION_REASON_LENGTH} characters.`,
      )
      return
    }

    setBusyId(eventId)
    setError('')

    try {
      await eventsApi.cancelEvent(eventId, reason)

      setEvents((previous) =>
        previous.map((item) =>
          item.id === eventId
            ? { ...item, status: 'cancelled' }
            : item,
        ),
      )

      setCancelId('')
      setCancelReason('')
    } catch (cancelError) {
      setError(errorLabel(cancelError))
    } finally {
      setBusyId('')
    }
  }

  function update<K extends keyof EditValues>(
    field: K,
    value: EditValues[K],
  ) {
    setValues((previous) =>
      previous
        ? { ...previous, [field]: value }
        : previous,
    )

    setError('')
  }

  return (
    <section
      className="hub-event-management"
      aria-labelledby="hub-events-title"
      aria-busy={loading}
    >
      <header className="hub-event-management-header">
        <div>
          <span>HUB MANAGEMENT</span>
          <h2 id="hub-events-title">Events</h2>
          <p>All event changes go through central BYB moderation.</p>
        </div>

        <Link to={`/hubs/${encodeURIComponent(hubId)}/events/create`}>
          + Host an event
        </Link>
      </header>

      {error && (
        <p className="hub-event-error" role="alert">
          {error}
        </p>
      )}

      {loading && events.length === 0 && (
        <p className="hub-event-state" role="status">
          Loading Hub events…
        </p>
      )}

      {!loading && events.length === 0 && !error && (
        <p className="hub-event-state">
          No events have been submitted for this Hub yet.
        </p>
      )}

      <div className="hub-event-list">
        {events.map((event) => (
          <article className="hub-event-row" key={event.id}>
            <div className="hub-event-row-image">
              {event.cover_image_url && (
                <img
                  src={event.cover_image_url}
                  alt={`${event.title} cover`}
                />
              )}
            </div>

            <div className="hub-event-row-main">
              <div className="hub-event-row-top">
                <h3>{event.title}</h3>

                <span
                  className={`hub-event-status status-${event.moderation_status}`}
                >
                  {pretty(event.moderation_status)}
                </span>

                <span
                  className={`hub-event-status status-${event.status}`}
                >
                  {pretty(event.status)}
                </span>
              </div>

              <p>
                {pretty(event.category)} · {pretty(event.format)} ·{' '}
                {dateLabel(event.starts_at)}–{dateLabel(event.ends_at)} ·
                submitted by @{event.created_by_username}
              </p>

              {event.reviewed_at && (
                <p className="hub-event-review-summary">
                  Latest review
                  {event.review_category
                    ? ` · ${pretty(event.review_category)}`
                    : ''}
                  {event.reviewed_by_username
                    ? ` by @${event.reviewed_by_username}`
                    : ''}
                  {event.review_notes
                    ? ` · ${event.review_notes}`
                    : ''}
                </p>
              )}

              {event.moderation_history?.length > 0 && (
                <details className="hub-event-history">
                  <summary>
                    Review history ({event.moderation_history.length})
                  </summary>

                  {event.moderation_history.map((review) => (
                    <p key={review.id}>
                      {pretty(review.decision)}
                      {review.review_category
                        ? ` · ${pretty(review.review_category)}`
                        : ''}
                      {' · '}
                      {dateLabel(review.reviewed_at)}
                      {review.reviewer_username
                        ? ` by @${review.reviewer_username}`
                        : ''}
                      {review.review_notes
                        ? ` — ${review.review_notes}`
                        : ''}
                    </p>
                  ))}
                </details>
              )}

              <div className="hub-event-row-actions">
                {event.status === 'published' && (
                  <Link to={`/events/${encodeURIComponent(event.id)}`}>
                    View public event
                  </Link>
                )}

                {event.status !== 'cancelled' &&
                  event.status !== 'completed' && (
                    <button
                      type="button"
                      onClick={() => startEdit(event)}
                      disabled={Boolean(busyId)}
                    >
                      Edit details
                    </button>
                  )}

                {event.status === 'published' &&
                  event.moderation_status === 'approved' && (
                    cancelId === event.id ? (
                      <div className="hub-event-cancellation">
                        <span>
                          Cancel this event? This action cannot be undone.
                        </span>

                        <label htmlFor={`cancel-reason-${event.id}`}>
                          Reason for cancellation
                        </label>

                        <textarea
                          id={`cancel-reason-${event.id}`}
                          value={cancelReason}
                          onChange={(event) => {
                            setCancelReason(
                              event.currentTarget.value.slice(
                                0,
                                MAX_CANCELLATION_REASON_LENGTH,
                              ),
                            )
                            setError('')
                          }}
                          placeholder="Explain why this event is being cancelled..."
                          rows={3}
                          maxLength={MAX_CANCELLATION_REASON_LENGTH}
                          required
                          disabled={Boolean(busyId)}
                        />

                        <span className="hub-event-cancellation-count">
                          {cancelReason.length}/
                          {MAX_CANCELLATION_REASON_LENGTH} characters
                        </span>

                        <button
                          type="button"
                          className="danger"
                          onClick={() => void cancelEvent(event.id)}
                          disabled={
                            Boolean(busyId) ||
                            !cancelReason.trim()
                          }
                        >
                          {busyId === event.id
                            ? 'Cancelling…'
                            : 'Confirm cancellation'}
                        </button>

                        <button
                          type="button"
                          onClick={closeCancellation}
                          disabled={Boolean(busyId)}
                        >
                          Keep event
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        className="danger"
                        onClick={() => startCancellation(event.id)}
                        disabled={Boolean(busyId)}
                      >
                        Cancel event
                      </button>
                    )
                  )}
              </div>
            </div>
          </article>
        ))}
      </div>

      {nextPage && !loading && (
        <button
          className="hub-event-load-more"
          type="button"
          disabled={Boolean(busyId)}
          onClick={() => {
            setLoading(true)
            void loadEvents(nextPage)
          }}
        >
          Load more events
        </button>
      )}

      {editing && values && (
        <div className="hub-event-modal-backdrop" role="presentation">
          <section
            className="hub-event-edit-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="hub-event-edit-title"
          >
            <button
              type="button"
              className="hub-event-modal-close"
              onClick={closeEdit}
              disabled={Boolean(busyId)}
              aria-label="Close"
            >
              ×
            </button>

            <span>EVENT DETAILS</span>
            <h3 id="hub-event-edit-title">Edit event</h3>

            <p className="hub-event-edit-note">
              {editing.moderation_status === 'approved'
                ? 'Saving changes returns this event to BYB moderation.'
                : editing.moderation_status === 'rejected'
                  ? 'Saving changes resubmits this event for BYB moderation.'
                  : 'This event remains pending while you edit it.'}
            </p>

            <form onSubmit={(event) => void saveEdit(event)}>
              <label htmlFor="hub-event-title">Title</label>
              <input
                id="hub-event-title"
                value={values.title}
                maxLength={200}
                required
                onChange={(event) =>
                  update('title', event.currentTarget.value)
                }
              />

              <label htmlFor="hub-event-description">Description</label>
              <textarea
                id="hub-event-description"
                value={values.description}
                rows={5}
                onChange={(event) =>
                  update('description', event.currentTarget.value)
                }
              />

              <div className="hub-event-edit-grid">
                <div>
                  <label htmlFor="hub-event-category">Category</label>
                  <select
                    id="hub-event-category"
                    value={values.category}
                    onChange={(event) =>
                      update(
                        'category',
                        event.currentTarget.value as EventCategory,
                      )
                    }
                  >
                    {categories.map((value) => (
                      <option key={value} value={value}>
                        {pretty(value)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="hub-event-format">Format</label>
                  <select
                    id="hub-event-format"
                    value={values.format}
                    onChange={(event) =>
                      update(
                        'format',
                        event.currentTarget.value as EventFormat,
                      )
                    }
                  >
                    {formats.map((value) => (
                      <option key={value} value={value}>
                        {pretty(value)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="hub-event-edit-grid">
                <div>
                  <label htmlFor="hub-event-start">
                    Start date and time
                  </label>
                  <input
                    id="hub-event-start"
                    type="datetime-local"
                    step={1}
                    value={values.starts_at}
                    required
                    onChange={(event) =>
                      update('starts_at', event.currentTarget.value)
                    }
                  />
                </div>

                <div>
                  <label htmlFor="hub-event-end">
                    End date and time
                  </label>
                  <input
                    id="hub-event-end"
                    type="datetime-local"
                    step={1}
                    value={values.ends_at}
                    required
                    onChange={(event) =>
                      update('ends_at', event.currentTarget.value)
                    }
                  />
                </div>
              </div>

              {(values.format === 'offline' ||
                values.format === 'hybrid') && (
                <>
                  <label htmlFor="hub-event-venue">Venue name</label>
                  <input
                    id="hub-event-venue"
                    value={values.venue_name}
                    required
                    onChange={(event) =>
                      update('venue_name', event.currentTarget.value)
                    }
                  />

                  <label htmlFor="hub-event-address">Full address</label>
                  <textarea
                    id="hub-event-address"
                    value={values.venue_address}
                    rows={2}
                    required
                    onChange={(event) =>
                      update('venue_address', event.currentTarget.value)
                    }
                  />

                  <label htmlFor="hub-event-city">City</label>
                  <input
                    id="hub-event-city"
                    value={values.city}
                    required
                    onChange={(event) =>
                      update('city', event.currentTarget.value)
                    }
                  />
                </>
              )}

              {(values.format === 'online' ||
                values.format === 'hybrid') && (
                <>
                  <label htmlFor="hub-event-url">
                    Online meeting URL
                  </label>
                  <input
                    id="hub-event-url"
                    type="url"
                    value={values.online_join_url}
                    required
                    onChange={(event) =>
                      update('online_join_url', event.currentTarget.value)
                    }
                  />

                  <label htmlFor="hub-event-instructions">
                    Online access instructions
                  </label>
                  <textarea
                    id="hub-event-instructions"
                    value={values.online_access_instructions}
                    rows={3}
                    onChange={(event) =>
                      update(
                        'online_access_instructions',
                        event.currentTarget.value,
                      )
                    }
                  />
                </>
              )}

              <label htmlFor="hub-event-cover">
                Replace cover image
              </label>
              <input
                id="hub-event-cover"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(event) => {
                  const file = event.currentTarget.files?.[0] || null

                  setCoverFile(file)
                  setCoverPreview(
                    file ? URL.createObjectURL(file) : '',
                  )
                }}
              />

              {coverPreview && (
                <img
                  className="hub-event-cover-preview"
                  src={coverPreview}
                  alt="New event cover preview"
                />
              )}

              <div className="hub-event-row-actions">
                <button
                  type="submit"
                  disabled={
                    Boolean(busyId) || !values.title.trim()
                  }
                >
                  {busyId ? 'Saving…' : 'Save event changes'}
                </button>

                <button
                  type="button"
                  onClick={closeEdit}
                  disabled={Boolean(busyId)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </section>
  )
}
