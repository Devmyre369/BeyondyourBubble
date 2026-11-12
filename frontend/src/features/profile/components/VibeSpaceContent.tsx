
import { useCallback, useEffect, useState, type FormEvent } from 'react'
import vibespaceApi, {
  type EventChoice,
  type Moment,
  type Vibe,
} from '../../../services/vibespaceApi'

interface VibeSpaceContentProps {
  username: string
}

export default function VibeSpaceContent({
  username,
}: VibeSpaceContentProps) {
  const [vibes, setVibes] = useState<Vibe[]>([])
  const [moments, setMoments] = useState<Moment[]>([])
  const [events, setEvents] = useState<EventChoice[]>([])

  const [vibeText, setVibeText] = useState('')
  const [vibeEvent, setVibeEvent] = useState('')

  const [momentImage, setMomentImage] = useState<File | null>(null)
  const [momentCaption, setMomentCaption] = useState('')
  const [momentEvent, setMomentEvent] = useState('')

  const [loading, setLoading] = useState(true)
  const [publishingVibe, setPublishingVibe] = useState(false)
  const [publishingMoment, setPublishingMoment] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadContent = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const [vibeData, momentData, eventData] = await Promise.all([
        vibespaceApi.getVibes(username),
        vibespaceApi.getMoments(username),
        vibespaceApi.getEventChoices(),
      ])

      setVibes(vibeData)
      setMoments(momentData)
      setEvents(eventData)
    } catch {
      setError('Unable to load VibeSpace content. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [username])

  useEffect(() => {
    void loadContent()
  }, [loadContent])

  const handleVibeSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!vibeText.trim()) {
      setError('Please write something before publishing.')
      return
    }

    setPublishingVibe(true)
    setError('')
    setSuccess('')

    try {
      const newVibe = await vibespaceApi.createVibe({
        text: vibeText.trim(),
        event: vibeEvent || null,
      })

      setVibes((previous) => [newVibe, ...previous])
      setVibeText('')
      setVibeEvent('')
      setSuccess('Your Vibe has been published.')
    } catch {
      setError('Unable to publish your Vibe. Please try again.')
    } finally {
      setPublishingVibe(false)
    }
  }

  const handleMomentSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!momentImage) {
      setError('Please select an image for your Moment.')
      return
    }

    if (momentImage.size > 10 * 1024 * 1024) {
      setError('Image size must not exceed 10 MB.')
      return
    }

    setPublishingMoment(true)
    setError('')
    setSuccess('')

    try {
      const newMoment = await vibespaceApi.createMoment({
        image: momentImage,
        caption: momentCaption.trim(),
        event: momentEvent || null,
      })

      setMoments((previous) => [newMoment, ...previous])
      setMomentImage(null)
      setMomentCaption('')
      setMomentEvent('')

      const fileInput = document.getElementById(
        'vibespace-moment-image',
      ) as HTMLInputElement | null

      if (fileInput) fileInput.value = ''

      setSuccess('Your Moment has been published.')
    } catch {
      setError('Unable to publish your Moment. Please try again.')
    } finally {
      setPublishingMoment(false)
    }
  }

  const handleDeleteVibe = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this Vibe?')) {
      return
    }

    setError('')
    setSuccess('')

    try {
      await vibespaceApi.deleteVibe(id)
      setVibes((previous) => previous.filter((vibe) => vibe.id !== id))
      setSuccess('Vibe deleted successfully.')
    } catch {
      setError('Unable to delete this Vibe. Please try again.')
    }
  }

  const handleDeleteMoment = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this Moment?')) {
      return
    }

    setError('')
    setSuccess('')

    try {
      await vibespaceApi.deleteMoment(id)
      setMoments((previous) =>
        previous.filter((moment) => moment.id !== id),
      )
      setSuccess('Moment deleted successfully.')
    } catch {
      setError('Unable to delete this Moment. Please try again.')
    }
  }

  const formatDate = (date: string) =>
    new Date(date).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })

  return (
    <div className="vibespace-content">

      {error && (
        <div className="vibespace-message vibespace-message-error" role="alert">
          {error}
        </div>
      )}

      {success && (
        <div className="vibespace-message vibespace-message-success" role="status">
          {success}
        </div>
      )}

      {/* VIBES */}

      <section className="vibespace-card vibespace-post-section">
        <div className="vibespace-section-heading">
          <div>
            <h2>Your Vibes</h2>
            <p>Share your thoughts and experiences.</p>
          </div>
          <span className="vibespace-count">{vibes.length}</span>
        </div>

        <form onSubmit={handleVibeSubmit} className="vibespace-composer">
          <textarea
            value={vibeText}
            onChange={(event) => setVibeText(event.target.value)}
            placeholder="What's happening in your world?"
            maxLength={2000}
            rows={4}
            required
          />

          <div className="vibespace-composer-footer">
            <span className="vibespace-character-count">
              {vibeText.length}/2000
            </span>

            <select
              value={vibeEvent}
              onChange={(event) => setVibeEvent(event.target.value)}
              aria-label="Associate Vibe with an event"
            >
              <option value="">Publish independently</option>
              {events.map((item) => (
                <option key={item.id} value={item.id}>
                  Associate with: {item.title}
                </option>
              ))}
            </select>

            <button type="submit" disabled={publishingVibe || !vibeText.trim()}>
              {publishingVibe ? 'Publishing...' : 'Publish Vibe'}
            </button>
          </div>
        </form>

        <div className="vibespace-post-list">
          {loading ? (
            <p className="vibespace-empty-state">Loading Vibes...</p>
          ) : vibes.length === 0 ? (
            <div className="vibespace-empty-state">
              <h3>Your story starts here.</h3>
              <p>Publish your first Vibe to share an experience or thought.</p>
            </div>
          ) : (
            vibes.map((vibe) => (
              <article className="vibespace-post" key={vibe.id}>
                <div className="vibespace-post-meta">
                  <span>{formatDate(vibe.created_at)}</span>
                  {vibe.event_title && (
                    <span className="vibespace-event-tag">
                      {vibe.event_title}
                    </span>
                  )}
                </div>

                <p className="vibespace-post-text">{vibe.text}</p>

                <div className="vibespace-post-actions">
                  <button
                    type="button"
                    onClick={() => void handleDeleteVibe(vibe.id)}
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))
          )}
        </div>
      </section>

      {/* MOMENTS */}

      <section className="vibespace-card vibespace-post-section">
        <div className="vibespace-section-heading">
          <div>
            <h2>Captured Moments</h2>
            <p>Share photographs from experiences worth remembering.</p>
          </div>
          <span className="vibespace-count">{moments.length}</span>
        </div>

        <form onSubmit={handleMomentSubmit} className="vibespace-composer">
          <label htmlFor="vibespace-moment-image">
            Select an image
          </label>

          <input
            id="vibespace-moment-image"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) =>
              setMomentImage(event.target.files?.[0] || null)
            }
          />

          {momentImage && (
            <p className="vibespace-selected-file">
              Selected: {momentImage.name}
            </p>
          )}

          <textarea
            value={momentCaption}
            onChange={(event) => setMomentCaption(event.target.value)}
            placeholder="Add a caption to this Moment (optional)"
            maxLength={500}
            rows={2}
          />

          <div className="vibespace-composer-footer">
            <span className="vibespace-character-count">
              {momentCaption.length}/500
            </span>

            <select
              value={momentEvent}
              onChange={(event) => setMomentEvent(event.target.value)}
              aria-label="Associate Moment with an event"
            >
              <option value="">Publish independently</option>
              {events.map((item) => (
                <option key={item.id} value={item.id}>
                  Associate with: {item.title}
                </option>
              ))}
            </select>

            <button
              type="submit"
              disabled={publishingMoment || !momentImage}
            >
              {publishingMoment ? 'Uploading...' : 'Publish Moment'}
            </button>
          </div>
        </form>

        <div className="vibespace-moment-grid">
          {loading ? (
            <p className="vibespace-empty-state">Loading Moments...</p>
          ) : moments.length === 0 ? (
            <div className="vibespace-empty-state">
              <h3>No Moments yet.</h3>
              <p>Your photographs will appear here.</p>
            </div>
          ) : (
            moments.map((moment) => (
              <article className="vibespace-moment-card" key={moment.id}>
                <img
                  src={moment.image_url}
                  alt={moment.caption || 'VibeSpace Moment'}
                  loading="lazy"
                />

                <div className="vibespace-moment-info">
                  <span>{formatDate(moment.created_at)}</span>

                  {moment.event_title && (
                    <span className="vibespace-event-tag">
                      {moment.event_title}
                    </span>
                  )}

                  {moment.caption && <p>{moment.caption}</p>}

                  <button
                    type="button"
                    onClick={() => void handleDeleteMoment(moment.id)}
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))
          )}
        </div>
      </section>
    </div>
  )
}
