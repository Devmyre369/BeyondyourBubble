import {
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import {
  eventsApi,
  type EventCategory,
  type EventFormat,
  type EventSubmissionRequest,
} from '../../services/eventsApi'
import {
  hubsApi,
  type HubDetail,
} from '../../services/hubsApi'
import './event-create.css'

const CATEGORIES = [
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

type Values = {
  title: string
  description: string
  category: EventCategory | ''
  format: EventFormat
  startDate: string
  startTime: string
  endDate: string
  endTime: string
  venue_name: string
  venue_address: string
  city: string
  online_join_url: string
  online_access_instructions: string
}

const INITIAL_VALUES: Values = {
  title: '',
  description: '',
  category: '',
  format: 'offline',
  startDate: '',
  startTime: '',
  endDate: '',
  endTime: '',
  venue_name: '',
  venue_address: '',
  city: '',
  online_join_url: '',
  online_access_instructions: '',
}

const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_IMAGE_SIZE = 10 * 1024 * 1024

export default function EventCreatePage() {
  const { hubId } = useParams<{ hubId: string }>()
  const navigate = useNavigate()

  const [hub, setHub] = useState<HubDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [permissionError, setPermissionError] = useState('')
  const [values, setValues] = useState<Values>(INITIAL_VALUES)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [generalError, setGeneralError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [createdTitle, setCreatedTitle] = useState('')
  const [createdEventId, setCreatedEventId] = useState('')
  const [submissionWarning, setSubmissionWarning] = useState('')
  const [isRetryingCoverUpload, setIsRetryingCoverUpload] = useState(false)
  const [step, setStep] = useState<'edit' | 'review'>('edit')

  const [coverFile, setCoverFile] = useState<File | null>(null)
  const [coverPreview, setCoverPreview] = useState('')
  const [coverError, setCoverError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let active = true

    async function load() {
      if (!hubId) {
        setPermissionError('Hub not found.')
        setLoading(false)
        return
      }

      try {
        const [hubDetail, membershipState] = await Promise.all([
          hubsApi.getHub(hubId),
          hubsApi.getMembership(hubId),
        ])

        if (!active) return

        const role = membershipState.membership?.role
        const status = membershipState.membership?.status
        const canHost =
          status === 'approved' &&
          (role === 'owner' ||
            role === 'admin' ||
            role === 'editor')

        if (!canHost) {
          setPermissionError(
            'You do not have permission to host events for this Hub.',
          )
        }

        setHub(hubDetail)
      } catch {
        if (active) {
          setPermissionError('Unable to load this Hub.')
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    void load()

    return () => {
      active = false
    }
  }, [hubId])

  useEffect(() => {
    return () => {
      if (coverPreview) URL.revokeObjectURL(coverPreview)
    }
  }, [coverPreview])

  function updateField<K extends keyof Values>(
    field: K,
    value: Values[K],
  ) {
    setValues((previous) => ({ ...previous, [field]: value }))
    setFieldErrors((previous) => {
      const next = { ...previous }
      delete next[field]
      return next
    })
  }

  function handleCoverChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    setCoverError('')

    if (!file) {
      setCoverFile(null)
      if (coverPreview) URL.revokeObjectURL(coverPreview)
      setCoverPreview('')
      return
    }

    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      setCoverError('Only JPG, JPEG, PNG, and WEBP images are allowed.')
      return
    }

    if (file.size > MAX_IMAGE_SIZE) {
      setCoverError('Image size must not exceed 10 MB.')
      return
    }

    if (coverPreview) URL.revokeObjectURL(coverPreview)
    setCoverFile(file)
    setCoverPreview(URL.createObjectURL(file))
  }
  function validate(): boolean {
    const errors: Record<string, string> = {}

    if (!values.title.trim()) {
      errors.title = 'Event title is required.'
    }

    if (!values.category) {
      errors.category = 'Event category is required.'
    }

    if (!values.startDate) {
      errors.startDate = 'Start date is required.'
    }

    if (!values.startTime) {
      errors.startTime = 'Start time is required.'
    }

    if (!values.endDate) {
      errors.endDate = 'End date is required.'
    }

    if (!values.endTime) {
      errors.endTime = 'End time is required.'
    }

    let startsAt: Date | null = null
    let endsAt: Date | null = null

    if (values.startDate && values.startTime) {
      startsAt = new Date(`${values.startDate}T${values.startTime}`)
      if (Number.isNaN(startsAt.getTime())) {
        errors.startTime = 'Invalid start date or time.'
      }
    }

    if (values.endDate && values.endTime) {
      endsAt = new Date(`${values.endDate}T${values.endTime}`)
      if (Number.isNaN(endsAt.getTime())) {
        errors.endTime = 'Invalid end date or time.'
      }
    }

    if (
      startsAt &&
      endsAt &&
      !Number.isNaN(startsAt.getTime()) &&
      !Number.isNaN(endsAt.getTime()) &&
      endsAt <= startsAt
    ) {
      errors.endTime = 'Event end must be after its start.'
    }

    const format = values.format

    if (format === 'offline' || format === 'hybrid') {
      if (!values.venue_name.trim()) {
        errors.venue_name = 'Venue name is required for offline and hybrid events.'
      }
      if (!values.venue_address.trim()) {
        errors.venue_address = 'Venue address is required for offline and hybrid events.'
      }
      if (!values.city.trim()) {
        errors.city = 'City is required for offline and hybrid events.'
      }
    }

    if (format === 'online' || format === 'hybrid') {
      if (!values.online_join_url.trim()) {
        errors.online_join_url = 'An online joining URL is required for online and hybrid events.'
      }
    }

    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  function handleReview(event: FormEvent) {
    event.preventDefault()
    if (validate()) {
      setStep('review')
    }
  }

  async function handleSubmit() {
    if (!hubId || !hub) return
    if (isSubmitting) return
    if (!validate()) return

    setIsSubmitting(true)
    setGeneralError('')

    const startsAt = new Date(`${values.startDate}T${values.startTime}`).toISOString()
    const endsAt = new Date(`${values.endDate}T${values.endTime}`).toISOString()

    const payload: EventSubmissionRequest = {
      hub_id: hubId,
      title: values.title.trim(),
      description: values.description.trim(),
      category: values.category as EventCategory,
      starts_at: startsAt,
      ends_at: endsAt,
      format: values.format,
    }

    if (values.venue_name.trim()) payload.venue_name = values.venue_name.trim()
    if (values.venue_address.trim()) payload.venue_address = values.venue_address.trim()
    if (values.city.trim()) payload.city = values.city.trim()
    if (values.online_join_url.trim()) payload.online_join_url = values.online_join_url.trim()
    if (values.online_access_instructions.trim()) {
      payload.online_access_instructions = values.online_access_instructions.trim()
    }

    try {
      const created = await eventsApi.submitEvent(payload)
      setCreatedTitle(created.title)
      setCreatedEventId(created.id)
      setSubmissionWarning('')
      if (coverFile) {
        try {
          await eventsApi.uploadEventCoverImage(created.id, coverFile)
        } catch {
          setSubmissionWarning(
            'The event was submitted, but its cover image could not be uploaded. You can retry the upload below.',
          )
        }
      }
      setSubmitted(true)
    } catch {
      setGeneralError('We could not submit this event. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function retryCoverUpload() {
    if (!createdEventId || !coverFile || isRetryingCoverUpload) return

    setIsRetryingCoverUpload(true)
    try {
      await eventsApi.uploadEventCoverImage(createdEventId, coverFile)
      setSubmissionWarning('')
      setCoverFile(null)
    } catch {
      setSubmissionWarning(
        'The event was submitted, but its cover image could not be uploaded. Please try again.',
      )
    } finally {
      setIsRetryingCoverUpload(false)
    }
  }

  if (loading) {
    return (
      <section className="event-create-page">
        <div className="event-create-state" role="status">
          <span className="event-create-loader" aria-hidden="true" />
          <h1>Loading Hub</h1>
          <p>Loading Hub details...</p>
        </div>
      </section>
    )
  }

  if (permissionError) {
    return (
      <section className="event-create-page">
        <div className="event-create-state" role="alert">
          <h1>Unable to host an event</h1>
          <p>{permissionError}</p>
          <Link to={hubId ? `/hubs/${hubId}` : '/hubs'}>Back to Hub</Link>
        </div>
      </section>
    )
  }

  if (submitted) {
    return (
      <section className="event-create-page">
        <div className="event-create-success">
          <h1>Event submitted</h1>
          <p>
            <strong>{createdTitle}</strong> has been submitted and is awaiting
            BYB moderation. It will appear publicly only after it is approved.
          </p>
          {submissionWarning && (
            <div role="status">
              <p className="event-create-error">{submissionWarning}</p>
              {coverFile && (
                <button
                  type="button"
                  onClick={() => void retryCoverUpload()}
                  disabled={isRetryingCoverUpload}
                >
                  {isRetryingCoverUpload ? 'Uploading...' : 'Retry cover upload'}
                </button>
              )}
            </div>
          )}
          <div className="event-create-success-actions">
            <button
              type="button"
              onClick={() => navigate(hubId ? `/hubs/${hubId}` : '/hubs')}
            >
              Back to Hub
            </button>
            <button
              type="button"
              onClick={() => {
                setSubmitted(false)
                setSubmissionWarning('')
                setCreatedEventId('')
                setValues(INITIAL_VALUES)
                setStep('edit')
                setCoverFile(null)
                if (coverPreview) URL.revokeObjectURL(coverPreview)
                setCoverPreview('')
              }}
            >
              Host another event
            </button>
          </div>
        </div>
      </section>
    )
  }
  return (
    <section className="event-create-page">
      <div className="event-create-toolbar">
        <Link className="event-create-back" to={hubId ? `/hubs/${hubId}` : '/hubs'}>
          Back to Hub
        </Link>
      </div>

      <div className="event-create-layout">
        <header className="event-create-header">
          <span className="event-create-eyebrow">HOST AN EVENT</span>
          <h1>{hub?.name}</h1>
          <p>
            Create an event for this Hub. It will be reviewed by BYB before it
            appears publicly.
          </p>
          {hub?.logo && (
            <img
              className="event-create-hub-logo"
              src={hub.logo}
              alt=""
            />
          )}
        </header>

        {step === 'edit' ? (
          <form className="event-create-form" onSubmit={handleReview}>
            <div className="event-create-grid">
              <div className="event-create-field event-create-field-full">
                <label htmlFor="event-title">Event title</label>
                <input
                  id="event-title"
                  value={values.title}
                  onChange={(e) => updateField('title', e.target.value)}
                  maxLength={200}
                  aria-invalid={Boolean(fieldErrors.title)}
                />
                {fieldErrors.title && (
                  <span className="event-create-error">{fieldErrors.title}</span>
                )}
              </div>

              <div className="event-create-field event-create-field-full">
                <label htmlFor="event-description">Description</label>
                <textarea
                  id="event-description"
                  value={values.description}
                  onChange={(e) => updateField('description', e.target.value)}
                  rows={4}
                />
              </div>

              <div className="event-create-field">
                <label htmlFor="event-category">Category</label>
                <select
                  id="event-category"
                  value={values.category}
                  onChange={(e) =>
                    updateField('category', e.target.value as EventCategory | '')
                  }
                  aria-invalid={Boolean(fieldErrors.category)}
                >
                  <option value="">Select a category</option>
                  {CATEGORIES.map((category) => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
                {fieldErrors.category && (
                  <span className="event-create-error">{fieldErrors.category}</span>
                )}
              </div>

              <div className="event-create-field">
                <label>Format</label>
                <div className="event-create-radio-group">
                  {(['offline', 'online', 'hybrid'] as EventFormat[]).map((format) => (
                    <label key={format} className="event-create-radio">
                      <input
                        type="radio"
                        name="format"
                        value={format}
                        checked={values.format === format}
                        onChange={() => updateField('format', format)}
                      />
                      <span>{format.charAt(0).toUpperCase() + format.slice(1)}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="event-create-field">
                <label htmlFor="event-start-date">Start date</label>
                <input
                  id="event-start-date"
                  type="date"
                  value={values.startDate}
                  onChange={(e) => updateField('startDate', e.target.value)}
                  aria-invalid={Boolean(fieldErrors.startDate)}
                />
                {fieldErrors.startDate && (
                  <span className="event-create-error">{fieldErrors.startDate}</span>
                )}
              </div>

              <div className="event-create-field">
                <label htmlFor="event-start-time">Start time</label>
                <input
                  id="event-start-time"
                  type="time"
                  value={values.startTime}
                  onChange={(e) => updateField('startTime', e.target.value)}
                  aria-invalid={Boolean(fieldErrors.startTime)}
                />
                {fieldErrors.startTime && (
                  <span className="event-create-error">{fieldErrors.startTime}</span>
                )}
              </div>

              <div className="event-create-field">
                <label htmlFor="event-end-date">End date</label>
                <input
                  id="event-end-date"
                  type="date"
                  value={values.endDate}
                  onChange={(e) => updateField('endDate', e.target.value)}
                  aria-invalid={Boolean(fieldErrors.endDate)}
                />
                {fieldErrors.endDate && (
                  <span className="event-create-error">{fieldErrors.endDate}</span>
                )}
              </div>

              <div className="event-create-field">
                <label htmlFor="event-end-time">End time</label>
                <input
                  id="event-end-time"
                  type="time"
                  value={values.endTime}
                  onChange={(e) => updateField('endTime', e.target.value)}
                  aria-invalid={Boolean(fieldErrors.endTime)}
                />
                {fieldErrors.endTime && (
                  <span className="event-create-error">{fieldErrors.endTime}</span>
                )}
              </div>
              {(values.format === 'offline' || values.format === 'hybrid') && (
                <>
                  <div className="event-create-field">
                    <label htmlFor="event-venue">Venue name</label>
                    <input
                      id="event-venue"
                      value={values.venue_name}
                      onChange={(e) => updateField('venue_name', e.target.value)}
                      aria-invalid={Boolean(fieldErrors.venue_name)}
                    />
                    {fieldErrors.venue_name && (
                      <span className="event-create-error">{fieldErrors.venue_name}</span>
                    )}
                  </div>

                  <div className="event-create-field event-create-field-full">
                    <label htmlFor="event-address">Full address</label>
                    <textarea
                      id="event-address"
                      value={values.venue_address}
                      onChange={(e) => updateField('venue_address', e.target.value)}
                      rows={3}
                      aria-invalid={Boolean(fieldErrors.venue_address)}
                    />
                    {fieldErrors.venue_address && (
                      <span className="event-create-error">{fieldErrors.venue_address}</span>
                    )}
                  </div>

                  <div className="event-create-field">
                    <label htmlFor="event-city">City</label>
                    <input
                      id="event-city"
                      value={values.city}
                      onChange={(e) => updateField('city', e.target.value)}
                      aria-invalid={Boolean(fieldErrors.city)}
                    />
                    {fieldErrors.city && (
                      <span className="event-create-error">{fieldErrors.city}</span>
                    )}
                  </div>
                </>
              )}

              {(values.format === 'online' || values.format === 'hybrid') && (
                <>
                  <div className="event-create-field event-create-field-full">
                    <label htmlFor="event-join-url">Joining URL</label>
                    <input
                      id="event-join-url"
                      type="url"
                      value={values.online_join_url}
                      onChange={(e) => updateField('online_join_url', e.target.value)}
                      aria-invalid={Boolean(fieldErrors.online_join_url)}
                    />
                    {fieldErrors.online_join_url && (
                      <span className="event-create-error">{fieldErrors.online_join_url}</span>
                    )}
                  </div>

                  <div className="event-create-field event-create-field-full">
                    <label htmlFor="event-join-instructions">Joining instructions</label>
                    <textarea
                      id="event-join-instructions"
                      value={values.online_access_instructions}
                      onChange={(e) =>
                        updateField('online_access_instructions', e.target.value)
                      }
                      rows={3}
                    />
                  </div>
                </>
              )}
              <div className="event-create-field event-create-field-full">
                <label htmlFor="event-cover">Cover image</label>
                <input
                  id="event-cover"
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleCoverChange}
                />
                <p className="event-create-help">
                  JPG, JPEG, PNG, or WEBP. Maximum 10 MB.
                </p>
                {coverError && (
                  <span className="event-create-error">{coverError}</span>
                )}
                {coverPreview && (
                  <div className="event-create-cover-preview">
                    <img src={coverPreview} alt="Cover preview" />
                    <button
                      type="button"
                      onClick={() => {
                        setCoverFile(null)
                        if (coverPreview) URL.revokeObjectURL(coverPreview)
                        setCoverPreview('')
                        if (fileInputRef.current) fileInputRef.current.value = ''
                      }}
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            </div>

            {generalError && (
              <p className="event-create-error event-create-general-error">
                {generalError}
              </p>
            )}

            <div className="event-create-actions">
              <button type="submit" disabled={isSubmitting}>
                Review event
              </button>
            </div>
          </form>
        ) : (
          <div className="event-create-review">
            <h2>Review your event</h2>
            <dl>
              <div>
                <dt>Title</dt>
                <dd>{values.title}</dd>
              </div>
              <div>
                <dt>Category</dt>
                <dd>{values.category}</dd>
              </div>
              <div>
                <dt>Format</dt>
                <dd>{values.format}</dd>
              </div>
              <div>
                <dt>Starts</dt>
                <dd>{values.startDate} {values.startTime}</dd>
              </div>
              <div>
                <dt>Ends</dt>
                <dd>{values.endDate} {values.endTime}</dd>
              </div>
              {values.venue_name && (
                <div>
                  <dt>Venue</dt>
                  <dd>{values.venue_name}, {values.city}</dd>
                </div>
              )}
              {values.online_join_url && (
                <div>
                  <dt>Joining URL</dt>
                  <dd>{values.online_join_url}</dd>
                </div>
              )}
              {coverPreview && (
                <div>
                  <dt>Cover image</dt>
                  <dd>Selected: {coverFile?.name}</dd>
                </div>
              )}
            </dl>

            {generalError && (
              <p className="event-create-error event-create-general-error">
                {generalError}
              </p>
            )}

            <div className="event-create-actions">
              <button
                type="button"
                onClick={() => setStep('edit')}
                disabled={isSubmitting}
              >
                Edit details
              </button>
              <button
                type="button"
                onClick={() => void handleSubmit()}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Submit for moderation'}
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
