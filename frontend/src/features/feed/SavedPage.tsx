
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { feedApi, type FeedEntry } from '../../services/feedApi'
import vibespaceApi from '../../services/vibespaceApi'
import PostActionIcon from '../vibespace/components/PostActionIcon'
import '../feed/feed.css'
import './saved.css'

const getKey = (entry: FeedEntry) =>
  `${entry.content_type}:${entry.id}`

const formatDate = (date: string) =>
  new Date(date).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })

export default function SavedPage() {
  const { user } = useAuth()
  const [entries, setEntries] = useState<FeedEntry[]>([])
  const [savedIds, setSavedIds] = useState<Record<string, string>>({})
  const [nextPage, setNextPage] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [unsaveLoading, setUnsaveLoading] = useState<Record<string, boolean>>({})

  useEffect(() => {
    let active = true

    const loadSaved = async () => {
      try {
        const [feed, savedRows] = await Promise.all([
          feedApi.getSavedFeed(1),
          vibespaceApi.getSavedContent(),
        ])
        if (!active) return

        const savedMap: Record<string, string> = {}
        savedRows.forEach((item) => {
          if (item.vibe) savedMap[`vibe:${item.vibe}`] = item.id
          if (item.moment) savedMap[`moment:${item.moment}`] = item.id
        })

        setEntries(feed.results)
        setNextPage(feed.next)
        setSavedIds(savedMap)
      } catch (err) {
        if (!active) return
        console.error('Saved posts loading failed:', err)
        setError('Unable to load your saved posts. Please try again.')
      } finally {
        if (active) setLoading(false)
      }
    }

    void loadSaved()

    return () => {
      active = false
    }
  }, [])

  const loadMore = async () => {
    if (nextPage === null) return
    setLoadingMore(true)
    setActionError('')

    try {
      const feed = await feedApi.getSavedFeed(nextPage)
      setEntries((previous) => [...previous, ...feed.results])
      setNextPage(feed.next)
    } catch {
      setActionError('Unable to load more saved posts. Please try again.')
    } finally {
      setLoadingMore(false)
    }
  }

  const handleUnsave = async (entry: FeedEntry) => {
    const key = getKey(entry)
    setUnsaveLoading((previous) => ({ ...previous, [key]: true }))
    setActionError('')

    try {
      const savedId = savedIds[key]
      if (savedId) {
        await vibespaceApi.removeSavedContent(savedId)
      }
      setEntries((previous) =>
        previous.filter((item) => getKey(item) !== key),
      )
      setSavedIds((previous) => {
        const next = { ...previous }
        delete next[key]
        return next
      })
    } catch {
      setActionError('Unable to remove this saved post. Please try again.')
    } finally {
      setUnsaveLoading((previous) => ({ ...previous, [key]: false }))
    }
  }

  return (
    <div className="saved-page">
      <header className="feed-header">
        <div className="feed-search-intro">
          <span className="feed-search-eyebrow">SAVED</span>
          <h1>Your saved posts.</h1>
          <p>Every Vibe and Moment you save lands here.</p>
        </div>
      </header>

      {actionError && (
        <p className="feed-action-error" role="alert">
          {actionError}
        </p>
      )}

      {loading && (
        <div className="feed-status">
          Loading your saved posts...
        </div>
      )}

      {!loading && error && (
        <div className="feed-error" role="alert">
          <p>{error}</p>
          <button type="button" onClick={() => window.location.reload()}>
            Try again
          </button>
        </div>
      )}

      {!loading && !error && entries.length === 0 && (
        <div className="feed-empty">
          <h2>You have not saved anything yet.</h2>
          <p>
            Tap the save icon on any Vibe or Moment to keep it here.
          </p>
        </div>
      )}

      {!loading && entries.length > 0 && (
        <section className="feed-list" aria-label="Your saved posts">
          {entries.map((entry) => {
            const key = getKey(entry)

            return (
              <article className="feed-card" key={key}>
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
                    <Link
                      to={
                        entry.author_username === user?.username
                          ? '/profile'
                          : `/users/${encodeURIComponent(entry.author_username)}`
                      }
                    >
                      {`${entry.author_first_name} ${entry.author_last_name}`.trim() ||
                        entry.author_username}
                    </Link>
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

                    {entry.content_text && <p>{entry.content_text}</p>}
                  </div>
                )}

                <div className="feed-post-actions">
                  <span className="saved-stat">
                    <PostActionIcon name="like" />
                    <span>{entry.like_count}</span>
                  </span>
                  <span className="saved-stat">
                    <PostActionIcon name="comment" />
                    <span>{entry.comment_count}</span>
                  </span>
                  <span className="saved-stat">
                    <PostActionIcon name="save" active />
                    <span>{entry.save_count}</span>
                  </span>
                  <button
                    type="button"
                    className="saved-unsave-button"
                    disabled={unsaveLoading[key]}
                    onClick={() => void handleUnsave(entry)}
                  >
                    <PostActionIcon name="save" active />
                    <span>
                      {unsaveLoading[key] ? 'Removing...' : 'Unsave'}
                    </span>
                  </button>
                </div>
              </article>
            )
          })}
        </section>
      )}

      {!loading && !error && nextPage !== null && entries.length > 0 && (
        <div className="feed-load-more">
          <button
            type="button"
            onClick={() => void loadMore()}
            disabled={loadingMore}
          >
            {loadingMore ? 'Loading...' : 'Load more'}
          </button>
        </div>
      )}
    </div>
  )
}
