
import { useCallback, useEffect, useState } from 'react'
import { feedApi, type FeedEntry } from '../../services/feedApi'
import './feed.css'
export default function FeedPage() {
  const [entries, setEntries] = useState<FeedEntry[]>([])
  const [nextPage, setNextPage] = useState<number | null>(1)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')

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
    <main className="feed-page">
      <header className="feed-header">
        <div>
          <h1>BYB Feed</h1>
          <p>Experience what is happening beyond your bubble.</p>
        </div>
      </header>

      {loading && (
        <div className="feed-status">
          Loading your feed...
        </div>
      )}

      {!loading && error && (
        <div className="feed-error">
          <p>{error}</p>
          <button onClick={() => loadFeed(1)}>
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
        <section className="feed-list">
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
                  <div className="feed-avatar feed-avatar-placeholder">
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
            onClick={() => loadFeed(nextPage, true)}
            disabled={loadingMore}
          >
            {loadingMore ? 'Loading...' : 'Load more'}
          </button>
        </div>
      )}
    </main>
  )
}
