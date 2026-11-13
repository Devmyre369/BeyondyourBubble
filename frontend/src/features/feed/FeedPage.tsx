
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from 'react'
import { feedApi, type FeedEntry } from '../../services/feedApi'
import vibespaceApi, { type EventChoice } from '../../services/vibespaceApi'
import './feed.css'

export default function FeedPage() {
  const [entries, setEntries] = useState<FeedEntry[]>([])
  const [events, setEvents] = useState<EventChoice[]>([])
  const [nextPage, setNextPage] = useState<number | null>(1)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [composerError, setComposerError] = useState('')
  const [composerSuccess, setComposerSuccess] = useState('')
  const [activeComposer, setActiveComposer] = useState<
    'vibe' | 'moment' | null
  >(null)
  const [vibeText, setVibeText] = useState('')
  const [vibeEvent, setVibeEvent] = useState('')
  const [momentImage, setMomentImage] = useState<File | null>(null)
  const [momentCaption, setMomentCaption] = useState('')
  const [momentEvent, setMomentEvent] = useState('')
  const [publishing, setPublishing] = useState(false)
  const momentFileInput = useRef<HTMLInputElement>(null)

  const loadFeed = useCallback(async (page: number, append = false) => {
    try {
      if (append) {
        setLoadingMore(true)
      } else {
        setLoading(true)
      }

      setError('')

      const response = await feedApi.getFeed(page)

      setEntries((previous) =>
        append ? [...previous, ...response.results] : response.results
      )

      setNextPage(response.next)
    } catch (err) {
      console.error('Feed loading failed:', err)
      setError('Unable to load your feed. Please try again.')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [])

  useEffect(() => {
    loadFeed(1)
  }, [loadFeed])

  useEffect(() => {
    let cancelled = false

    const loadEvents = async () => {
      try {
        const eventChoices = await vibespaceApi.getEventChoices()
        if (!cancelled) setEvents(eventChoices)
      } catch {
        if (!cancelled) {
          setComposerError(
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

  const handleVibeSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!vibeText.trim()) {
      setComposerError('Please write something before publishing.')
      return
    }

    setPublishing(true)
    setComposerError('')
    setComposerSuccess('')

    try {
      await vibespaceApi.createVibe({
        text: vibeText.trim(),
        event: vibeEvent || null,
      })
      setVibeText('')
      setVibeEvent('')
      setActiveComposer(null)
      setComposerSuccess('Your Vibe has been published.')
      await loadFeed(1)
    } catch {
      setComposerError('Unable to publish your Vibe. Please try again.')
    } finally {
      setPublishing(false)
    }
  }

  const handleMomentSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!momentImage) {
      setComposerError('Please select an image for your Moment.')
      return
    }

    if (momentImage.size > 10 * 1024 * 1024) {
      setComposerError('Image size must not exceed 10 MB.')
      return
    }

    setPublishing(true)
    setComposerError('')
    setComposerSuccess('')

    try {
      await vibespaceApi.createMoment({
        image: momentImage,
        caption: momentCaption.trim(),
        event: momentEvent || null,
      })
      setMomentImage(null)
      setMomentCaption('')
      setMomentEvent('')
      if (momentFileInput.current) momentFileInput.current.value = ''
      setActiveComposer(null)
      setComposerSuccess('Your Moment has been published.')
      await loadFeed(1)
    } catch {
      setComposerError('Unable to publish your Moment. Please try again.')
    } finally {
      setPublishing(false)
    }
  }

  const toggleComposer = (composer: 'vibe' | 'moment') => {
    setActiveComposer((current) =>
      current === composer ? null : composer,
    )
    setComposerError('')
    setComposerSuccess('')
  }

  const formatDate = (date: string) => {
    return new Date(date).toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  }

  return (
    <div className="feed-page">
      <header className="feed-header">
        <div>
          <h1>BYB Feed</h1>
          <p>Experience what is happening beyond your bubble.</p>
        </div>
      </header>

      <section className="feed-publish" aria-label="Publish to your feed">
        <div className="feed-publish-heading">
          <div>
            <h2>Share your experience</h2>
            <p>Publish a thought or capture a moment.</p>
          </div>
          <div className="feed-publish-actions">
            <button
              type="button"
              aria-expanded={activeComposer === 'vibe'}
              aria-controls="feed-vibe-composer"
              onClick={() => toggleComposer('vibe')}
            >
              Upload a vibe
            </button>
            <button
              type="button"
              aria-expanded={activeComposer === 'moment'}
              aria-controls="feed-moment-composer"
              onClick={() => toggleComposer('moment')}
            >
              Upload a moment
            </button>
          </div>
        </div>

        {composerError && (
          <p className="feed-publish-message feed-publish-error" role="alert">
            {composerError}
          </p>
        )}
        {composerSuccess && (
          <p
            className="feed-publish-message feed-publish-success"
            role="status"
          >
            {composerSuccess}
          </p>
        )}

        {activeComposer === 'vibe' && (
          <form
            id="feed-vibe-composer"
            className="feed-composer"
            onSubmit={(event) => void handleVibeSubmit(event)}
          >
            <textarea
              value={vibeText}
              onChange={(event) => setVibeText(event.target.value)}
              placeholder="What's happening in your world?"
              maxLength={2000}
              rows={4}
              required
            />
            <div className="feed-composer-footer">
              <span>{vibeText.length}/2000</span>
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
              <button type="submit" disabled={publishing || !vibeText.trim()}>
                {publishing ? 'Publishing...' : 'Publish Vibe'}
              </button>
            </div>
          </form>
        )}

        {activeComposer === 'moment' && (
          <form
            id="feed-moment-composer"
            className="feed-composer"
            onSubmit={(event) => void handleMomentSubmit(event)}
          >
            <label htmlFor="feed-moment-image">Select an image</label>
            <input
              ref={momentFileInput}
              id="feed-moment-image"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(event) =>
                setMomentImage(event.target.files?.[0] || null)
              }
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
              rows={2}
            />
            <div className="feed-composer-footer">
              <span>{momentCaption.length}/500</span>
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
              <button type="submit" disabled={publishing || !momentImage}>
                {publishing ? 'Uploading...' : 'Publish Moment'}
              </button>
            </div>
          </form>
        )}
      </section>

      {loading && (
        <div className="feed-status">
          Loading your feed...
        </div>
      )}

      {!loading && error && (
        <div className="feed-error" role="alert">
          <p>{error}</p>
          <button type="button" onClick={() => loadFeed(1)}>
            Try again
          </button>
        </div>
      )}

      {!loading && !error && entries.length === 0 && (
        <div className="feed-empty">
          <h2>Your feed starts here.</h2>
          <p>
            Vibes and Moments shared by the BYB community will appear here.
          </p>
        </div>
      )}

      {!loading && entries.length > 0 && (
        <section className="feed-list" aria-label="Your BYB feed">
          {entries.map((entry) => (
            <article
              className="feed-card"
              key={`${entry.content_type}-${entry.id}`}
            >
              <div className="feed-card-header">
                {entry.author_profile_picture ? (
                  <img
                    className="feed-avatar"
                    src={entry.author_profile_picture}
                    alt={`${entry.author_username}'s profile`}
                  />
                ) : (
                  <div
                    className="feed-avatar feed-avatar-placeholder"
                    aria-hidden="true"
                  >
                    {entry.author_username.charAt(0).toUpperCase()}
                  </div>
                )}

                <div className="feed-author-info">
                  <strong>{entry.author_username}</strong>
                  <span>{formatDate(entry.created_at)}</span>
                </div>

                <span className="feed-content-type">
                  {entry.content_type === 'vibe' ? 'VIBE' : 'MOMENT'}
                </span>
              </div>

              {entry.event_title && (
                <div className="feed-event">
                  <span>EVENT</span>
                  <strong>{entry.event_title}</strong>
                </div>
              )}

              {entry.content_type === 'vibe' && entry.content_text && (
                <div className="feed-vibe-content">
                  {entry.content_text}
                </div>
              )}

              {entry.content_type === 'moment' && (
                <div className="feed-moment-content">
                  {entry.image_url && (
                    <img
                      className="feed-moment-image"
                      src={entry.image_url}
                      alt={entry.content_text || 'BYB Moment'}
                      loading="lazy"
                    />
                  )}

                  {entry.content_text && (
                    <p>{entry.content_text}</p>
                  )}
                </div>
              )}
            </article>
          ))}
        </section>
      )}

      {!loading && !error && nextPage !== null && (
        <div className="feed-load-more">
          <button
            type="button"
            onClick={() => loadFeed(nextPage, true)}
            disabled={loadingMore}
          >
            {loadingMore ? 'Loading...' : 'Load more'}
          </button>
        </div>
      )}
    </div>
  )
}
