import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import vibespaceApi, { type EventChoice } from '../../services/vibespaceApi'
import './feed.css'

type CreatePostPageProps = {
  type: 'vibe' | 'moment'
}

export default function CreatePostPage({ type }: CreatePostPageProps) {
  const isVibe = type === 'vibe'
  const [events, setEvents] = useState<EventChoice[]>([])
  const [selectedEvent, setSelectedEvent] = useState('')
  const [vibeText, setVibeText] = useState('')
  const [momentImage, setMomentImage] = useState<File | null>(null)
  const [momentCaption, setMomentCaption] = useState('')
  const [error, setError] = useState('')
  const [eventError, setEventError] = useState('')
  const [success, setSuccess] = useState('')
  const [publishing, setPublishing] = useState(false)
  const momentFileInput = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let cancelled = false

    const loadEvents = async () => {
      try {
        const choices = await vibespaceApi.getEventChoices()
        if (!cancelled) setEvents(choices)
      } catch {
        if (!cancelled) {
          setEventError(
            'Unable to load event options. You can still publish without one.',
          )
        }
      }
    }

    void loadEvents()

    return () => {
      cancelled = true
    }
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (isVibe && !vibeText.trim()) {
      setError('Please write something before publishing.')
      return
    }

    if (!isVibe && !momentImage) {
      setError('Please select an image for your Moment.')
      return
    }

    if (!isVibe && momentImage && momentImage.size > 10 * 1024 * 1024) {
      setError('Image size must not exceed 10 MB.')
      return
    }

    setPublishing(true)

    try {
      if (isVibe) {
        await vibespaceApi.createVibe({
          text: vibeText.trim(),
          event: selectedEvent || null,
        })
        setVibeText('')
        setSelectedEvent('')
        setSuccess('Your Vibe has been published.')
      } else if (momentImage) {
        await vibespaceApi.createMoment({
          image: momentImage,
          caption: momentCaption.trim(),
          event: selectedEvent || null,
        })
        setMomentImage(null)
        setMomentCaption('')
        setSelectedEvent('')
        if (momentFileInput.current) momentFileInput.current.value = ''
        setSuccess('Your Moment has been published.')
      }
    } catch {
      setError(
        `Unable to publish your ${isVibe ? 'Vibe' : 'Moment'}. Please try again.`,
      )
    } finally {
      setPublishing(false)
    }
  }

  return (
    <div className="feed-page create-post-page">
      <header className="feed-header">
        <div>
          <h1>Upload a {isVibe ? 'Vibe' : 'Moment'}</h1>
          <p>
            {isVibe
              ? 'Share what is happening in your world.'
              : 'Capture and share a moment with the community.'}
          </p>
        </div>
        <Link className="create-post-back" to="/home">
          Back to feed
        </Link>
      </header>

      <section
        className="feed-publish"
        aria-label={`Upload a ${isVibe ? 'Vibe' : 'Moment'}`}
      >
        {eventError && (
          <p className="feed-publish-message" role="status">
            {eventError}
          </p>
        )}
        {error && (
          <p className="feed-publish-message feed-publish-error" role="alert">
            {error}
          </p>
        )}
        {success && (
          <p
            className="feed-publish-message feed-publish-success"
            role="status"
          >
            {success}
          </p>
        )}

        <form
          className="feed-composer"
          onSubmit={(event) => void handleSubmit(event)}
        >
          {isVibe ? (
            <textarea
              value={vibeText}
              onChange={(event) => setVibeText(event.target.value)}
              placeholder="What's happening in your world?"
              maxLength={2000}
              rows={5}
              required
            />
          ) : (
            <>
              <label htmlFor="create-moment-image">Select an image</label>
              <input
                ref={momentFileInput}
                id="create-moment-image"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(event) =>
                  setMomentImage(event.target.files?.[0] || null)
                }
                required
              />
              {momentImage && (
                <p className="feed-selected-file">
                  Selected: {momentImage.name}
                </p>
              )}
              <textarea
                value={momentCaption}
                onChange={(event) => setMomentCaption(event.target.value)}
                placeholder="Add a caption to this Moment (optional)"
                maxLength={500}
                rows={3}
              />
            </>
          )}

          <div className="feed-composer-footer">
            <span>
              {isVibe
                ? `${vibeText.length}/2000`
                : `${momentCaption.length}/500`}
            </span>
            <select
              value={selectedEvent}
              onChange={(event) => setSelectedEvent(event.target.value)}
              aria-label={`Associate ${isVibe ? 'Vibe' : 'Moment'} with an event`}
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
              disabled={
                publishing || (isVibe ? !vibeText.trim() : !momentImage)
              }
            >
              {publishing
                ? isVibe
                  ? 'Publishing...'
                  : 'Uploading...'
                : `Publish ${isVibe ? 'Vibe' : 'Moment'}`}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}
