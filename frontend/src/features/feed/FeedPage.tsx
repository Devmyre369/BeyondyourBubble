
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from 'react'
import { useAuth } from '../../context/AuthContext'
import { feedApi, type FeedEntry } from '../../services/feedApi'
import vibespaceApi, {
  type Comment,
  type EventChoice,
  type LikeState,
  type PostCounts,
  type Revibe,
} from '../../services/vibespaceApi'
import PostActionIcon from '../vibespace/components/PostActionIcon'
import './feed.css'

const getKey = (entry: FeedEntry) =>
  `${entry.content_type}:${entry.id}`

const createCountsMap = (items: FeedEntry[]): Record<string, PostCounts> =>
  Object.fromEntries(
    items.map((entry) => [
      getKey(entry),
      {
        like_count: entry.like_count,
        comment_count: entry.comment_count,
        revibe_count: entry.revibe_count,
        save_count: entry.save_count,
        share_count: entry.share_count,
      },
    ]),
  )

export default function FeedPage() {
  const { user, isAuthenticated } = useAuth()
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
  const [likes, setLikes] = useState<Record<string, LikeState>>({})
  const [likeLoading, setLikeLoading] = useState<Record<string, boolean>>({})
  const [revibes, setRevibes] = useState<Record<string, Revibe | null>>({})
  const [revibeLoading, setRevibeLoading] = useState<Record<string, boolean>>({})
  const [savedItems, setSavedItems] = useState<Record<string, string>>({})
  const [saveLoading, setSaveLoading] = useState<Record<string, boolean>>({})
  const [comments, setComments] = useState<Record<string, Comment[]>>({})
  const [commentInputs, setCommentInputs] = useState<Record<string, string>>({})
  const [commentLoading, setCommentLoading] = useState<Record<string, boolean>>({})
  const [commentSubmitting, setCommentSubmitting] = useState<Record<string, boolean>>({})
  const [openComments, setOpenComments] = useState<Record<string, boolean>>({})
  const [actionError, setActionError] = useState('')
  const [counts, setCounts] = useState<Record<string, PostCounts>>({})

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
      setCounts((previous) =>
        append
          ? { ...previous, ...createCountsMap(response.results) }
          : createCountsMap(response.results),
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

  useEffect(() => {
    if (!isAuthenticated || entries.length === 0) return

    let cancelled = false

    const loadInteractions = async () => {
      try {
        const savedData = await vibespaceApi.getSavedContent()
        if (cancelled) return

        const savedMap: Record<string, string> = {}
        savedData.forEach((item) => {
          if (item.vibe) savedMap[`vibe:${item.vibe}`] = item.id
          if (item.moment) savedMap[`moment:${item.moment}`] = item.id
        })
        setSavedItems(savedMap)
      } catch {
        if (!cancelled) {
          setActionError('Unable to load saved post states.')
        }
      }

      const results = await Promise.all(
        entries.map(async (entry) => {
          const [likeResult, revibeResult] = await Promise.allSettled([
            vibespaceApi.getLikeState(entry.content_type, entry.id),
            entry.content_type === 'vibe'
              ? vibespaceApi.getVibeRevibe(entry.id)
              : vibespaceApi.getMomentRevibe(entry.id),
          ])

          return {
            key: getKey(entry),
            like:
              likeResult.status === 'fulfilled'
                ? likeResult.value
                : null,
            revibe:
              revibeResult.status === 'fulfilled'
                ? revibeResult.value
                : null,
            likeFailed: likeResult.status === 'rejected',
          }
        }),
      )

      if (cancelled) return

      const likeMap: Record<string, LikeState> = {}
      const revibeMap: Record<string, Revibe | null> = {}
      results.forEach((result) => {
        if (result.like) likeMap[result.key] = result.like
        revibeMap[result.key] = result.revibe
      })
      if (results.some((result) => result.likeFailed)) {
        setActionError('Unable to load Like states. Try again later.')
      }
      setLikes(likeMap)
      setRevibes(revibeMap)
      setCounts((previous) => {
        const next = { ...previous }
        results.forEach((result) => {
          if (result.like && next[result.key]) {
            next[result.key] = {
              ...next[result.key],
              like_count: result.like.like_count,
            }
          }
        })
        return next
      })
    }

    void loadInteractions()

    return () => {
      cancelled = true
    }
  }, [entries, isAuthenticated])

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

  const handleLike = async (entry: FeedEntry) => {
    const key = getKey(entry)
    setLikeLoading((previous) => ({ ...previous, [key]: true }))

    try {
      const updated = likes[key]?.liked
        ? await vibespaceApi.unlikeContent(entry.content_type, entry.id)
        : await vibespaceApi.likeContent(entry.content_type, entry.id)
      setLikes((previous) => ({ ...previous, [key]: updated }))
      setCounts((previous) => ({
        ...previous,
        [key]: {
          ...(previous[key] || entry),
          like_count: updated.like_count,
        },
      }))
    } catch {
      setActionError('Unable to update your Like. Please try again.')
    } finally {
      setLikeLoading((previous) => ({ ...previous, [key]: false }))
    }
  }

  const handleRevibe = async (entry: FeedEntry) => {
    const key = getKey(entry)
    const hadRevibe = Boolean(revibes[key])
    setRevibeLoading((previous) => ({ ...previous, [key]: true }))

    try {
      if (revibes[key]) {
        await (entry.content_type === 'vibe'
          ? vibespaceApi.removeVibeRevibe(entry.id)
          : vibespaceApi.removeMomentRevibe(entry.id))
        setRevibes((previous) => ({ ...previous, [key]: null }))
      } else {
        const revibe =
          entry.content_type === 'vibe'
            ? await vibespaceApi.revibeVibe(entry.id, {
                revibe_type: 'direct',
              })
            : await vibespaceApi.revibeMoment(entry.id, {
                revibe_type: 'direct',
              })
        setRevibes((previous) => ({ ...previous, [key]: revibe }))
      }
      setCounts((previous) => ({
        ...previous,
        [key]: {
          ...(previous[key] || entry),
          revibe_count: Math.max(
            0,
            (previous[key]?.revibe_count ?? entry.revibe_count) +
              (hadRevibe ? -1 : 1),
          ),
        },
      }))
    } catch {
      setActionError('Unable to update your Revibe. Please try again.')
    } finally {
      setRevibeLoading((previous) => ({ ...previous, [key]: false }))
    }
  }

  const handleSave = async (entry: FeedEntry) => {
    const key = getKey(entry)
    const wasSaved = Boolean(savedItems[key])
    setSaveLoading((previous) => ({ ...previous, [key]: true }))

    try {
      const savedId = savedItems[key]
      if (savedId) {
        await vibespaceApi.removeSavedContent(savedId)
        setSavedItems((previous) => {
          const next = { ...previous }
          delete next[key]
          return next
        })
      } else {
        const saved =
          entry.content_type === 'vibe'
            ? await vibespaceApi.saveVibe(entry.id)
            : await vibespaceApi.saveMoment(entry.id)
        setSavedItems((previous) => ({ ...previous, [key]: saved.id }))
      }
      setCounts((previous) => ({
        ...previous,
        [key]: {
          ...(previous[key] || entry),
          save_count: Math.max(
            0,
            (previous[key]?.save_count ?? entry.save_count) +
              (wasSaved ? -1 : 1),
          ),
        },
      }))
    } catch {
      setActionError('Unable to update your saved posts. Please try again.')
    } finally {
      setSaveLoading((previous) => ({ ...previous, [key]: false }))
    }
  }

  const toggleComments = async (entry: FeedEntry) => {
    const key = getKey(entry)
    const opening = !openComments[key]
    setOpenComments((previous) => ({ ...previous, [key]: opening }))
    if (!opening || comments[key]) return

    setCommentLoading((previous) => ({ ...previous, [key]: true }))
    try {
      const data =
        entry.content_type === 'vibe'
          ? await vibespaceApi.getVibeComments(entry.id)
          : await vibespaceApi.getMomentComments(entry.id)
      setComments((previous) => ({ ...previous, [key]: data }))
    } catch {
      setActionError('Unable to load comments. Please try again.')
    } finally {
      setCommentLoading((previous) => ({ ...previous, [key]: false }))
    }
  }

  const handleCommentSubmit = async (
    event: FormEvent<HTMLFormElement>,
    entry: FeedEntry,
  ) => {
    event.preventDefault()
    const key = getKey(entry)
    const text = commentInputs[key]?.trim()
    if (!text) return

    setCommentSubmitting((previous) => ({ ...previous, [key]: true }))
    try {
      const comment =
        entry.content_type === 'vibe'
          ? await vibespaceApi.createVibeComment(entry.id, text)
          : await vibespaceApi.createMomentComment(entry.id, text)
      setComments((previous) => ({
        ...previous,
        [key]: [...(previous[key] || []), comment],
      }))
      setCommentInputs((previous) => ({ ...previous, [key]: '' }))
      setCounts((previous) => ({
        ...previous,
        [key]: {
          ...(previous[key] || entry),
          comment_count:
            (previous[key]?.comment_count ?? entry.comment_count) + 1,
        },
      }))
    } catch {
      setActionError('Unable to publish your comment. Please try again.')
    } finally {
      setCommentSubmitting((previous) => ({ ...previous, [key]: false }))
    }
  }

  const handleShare = async (entry: FeedEntry) => {
    const url = `${window.location.origin}${window.location.pathname}#${entry.content_type}-${entry.id}`
    let shared = false

    try {
      if (navigator.share) {
        await navigator.share({
          title: entry.content_type === 'vibe' ? 'BYB Vibe' : 'BYB Moment',
          url,
        })
        shared = true
      } else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url)
        shared = true
      } else {
        setActionError('Sharing is not supported by this browser.')
      }
      if (shared) {
        const result = await vibespaceApi.shareContent(
          entry.content_type,
          entry.id,
        )
        setCounts((previous) => ({
          ...previous,
          [getKey(entry)]: {
            ...(previous[getKey(entry)] || entry),
            share_count: result.share_count,
          },
        }))
      }
    } catch (shareError) {
      if (shareError instanceof Error && shareError.name === 'AbortError') {
        return
      }
      setActionError('Unable to share this post.')
    }
  }

  const handleDelete = async (entry: FeedEntry) => {
    if (!window.confirm(`Delete this ${entry.content_type}?`)) return

    try {
      if (entry.content_type === 'vibe') {
        await vibespaceApi.deleteVibe(entry.id)
      } else {
        await vibespaceApi.deleteMoment(entry.id)
      }
      setEntries((previous) =>
        previous.filter((item) => getKey(item) !== getKey(entry)),
      )
    } catch {
      setActionError(`Unable to delete this ${entry.content_type}.`)
    }
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

      {actionError && (
        <p className="feed-action-error" role="alert">
          {actionError}
        </p>
      )}

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
          {entries.map((entry) => {
            const key = getKey(entry)
            const postCounts = counts[key] || entry

            return (
            <article
              className="feed-card"
              key={key}
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

              <div className="feed-post-actions">
                <button
                  type="button"
                  className={likes[key]?.liked ? 'active' : ''}
                  disabled={likeLoading[key]}
                  aria-label={`Like; ${postCounts.like_count} total likes`}
                  title={`${postCounts.like_count} likes`}
                  aria-pressed={Boolean(likes[key]?.liked)}
                  onClick={() => void handleLike(entry)}
                >
                  <PostActionIcon
                    name="like"
                    active={likes[key]?.liked}
                  />
                  <span>{postCounts.like_count}</span>
                </button>
                <button
                  type="button"
                  className={openComments[key] ? 'active' : ''}
                  aria-label={`Comments; ${postCounts.comment_count} total`}
                  title={`${postCounts.comment_count} comments`}
                  aria-expanded={Boolean(openComments[key])}
                  onClick={() => void toggleComments(entry)}
                >
                  <PostActionIcon name="comment" />
                  <span>{postCounts.comment_count}</span>
                </button>
                {isAuthenticated && (
                  <>
                    <button
                      type="button"
                      className={revibes[key] ? 'active' : ''}
                      disabled={revibeLoading[key]}
                      aria-label={`Revibe; ${postCounts.revibe_count} total`}
                      title={`${postCounts.revibe_count} Revibes`}
                      aria-pressed={Boolean(revibes[key])}
                      onClick={() => void handleRevibe(entry)}
                    >
                      <PostActionIcon name="revibe" />
                      <span>{postCounts.revibe_count}</span>
                    </button>
                    <button
                      type="button"
                      className={savedItems[key] ? 'active' : ''}
                      disabled={saveLoading[key]}
                      aria-label={`Save; ${postCounts.save_count} total saves`}
                      title={`${postCounts.save_count} saves`}
                      aria-pressed={Boolean(savedItems[key])}
                      onClick={() => void handleSave(entry)}
                    >
                      <PostActionIcon name="save" />
                      <span>{postCounts.save_count}</span>
                    </button>
                  </>
                )}
                <button
                  type="button"
                  aria-label={`Share; ${postCounts.share_count} total shares`}
                  title={`${postCounts.share_count} shares`}
                  onClick={() => void handleShare(entry)}
                >
                  <PostActionIcon name="share" />
                  <span>{postCounts.share_count}</span>
                </button>
                {entry.author_username === user?.username && (
                  <button
                    type="button"
                    className="feed-delete-action"
                    aria-label={`Delete this ${entry.content_type}`}
                    onClick={() => void handleDelete(entry)}
                  >
                    <PostActionIcon name="delete" />
                  </button>
                )}
              </div>

              {openComments[getKey(entry)] && (
                <div className="feed-comments">
                  {commentLoading[getKey(entry)] ? (
                    <p className="feed-comments-empty">Loading comments...</p>
                  ) : comments[getKey(entry)]?.length ? (
                    comments[getKey(entry)].map((comment) => (
                      <div className="feed-comment" key={comment.id}>
                        <strong>@{comment.author_username}</strong>
                        <p>{comment.text}</p>
                      </div>
                    ))
                  ) : (
                    <p className="feed-comments-empty">No comments yet.</p>
                  )}

                  {isAuthenticated && (
                    <form
                      className="feed-comment-form"
                      onSubmit={(event) =>
                        void handleCommentSubmit(event, entry)
                      }
                    >
                      <input
                        value={commentInputs[getKey(entry)] || ''}
                        onChange={(event) =>
                          setCommentInputs((previous) => ({
                            ...previous,
                            [getKey(entry)]: event.target.value,
                          }))
                        }
                        maxLength={1000}
                        placeholder="Write a comment..."
                        aria-label="Write a comment"
                        required
                      />
                      <button
                        type="submit"
                        disabled={
                          commentSubmitting[getKey(entry)] ||
                          !commentInputs[getKey(entry)]?.trim()
                        }
                      >
                        {commentSubmitting[getKey(entry)]
                          ? 'Posting...'
                          : 'Post'}
                      </button>
                    </form>
                  )}
                </div>
              )}
            </article>
            )
          })}
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
