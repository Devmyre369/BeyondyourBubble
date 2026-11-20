
import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from 'react'

import { useNavigate } from 'react-router-dom'

import { useAuth } from '../../../context/AuthContext'

import vibespaceApi, {
  type Comment,
  type LikeState,
  type Moment,
  type PostCounts,
  type Revibe,
  type SavedContent,
  type ProfilePost,
  type Vibe,
} from '../../../services/vibespaceApi'
import PostActionIcon from '../../vibespace/components/PostActionIcon'
import type { ProfileSection } from './profileSectionUtils'

interface VibeSpaceContentProps {
  username: string
  section?: Extract<ProfileSection, 'posts' | 'vibes' | 'moments'>
}

type ContentType = 'vibe' | 'moment'

type CommentState = Record<string, Comment[]>
type TextState = Record<string, string>
type LoadingState = Record<string, boolean>
type RevibeState = Record<string, Revibe | null>
type SavedState = Record<string, string>

export default function VibeSpaceContent({
  username,
  section = 'posts',
}: VibeSpaceContentProps) {
  const { user, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const currentUsername = user?.username || ''
  const isOwnProfile = currentUsername === username

  const [vibes, setVibes] = useState<Vibe[]>([])
  const [moments, setMoments] = useState<Moment[]>([])

  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [nextPage, setNextPage] = useState<number | null>(null)

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const lastScrolledHash = useRef('')

  useEffect(() => {
    const hash = window.location.hash
    if (loading || !hash || hash === lastScrolledHash.current) return
    const frame = window.requestAnimationFrame(() => {
      const target = document.getElementById(hash.slice(1))
      if (!target) return
      target.scrollIntoView({ behavior: 'smooth', block: 'center' })
      lastScrolledHash.current = hash
    })
    return () => window.cancelAnimationFrame(frame)
  }, [loading, vibes.length, moments.length])

  // Interaction state

  const [comments, setComments] = useState<CommentState>({})
  const [commentInputs, setCommentInputs] = useState<TextState>({})
  const [commentLoading, setCommentLoading] = useState<LoadingState>({})
  const [commentSubmitting, setCommentSubmitting] = useState<LoadingState>({})
  const [openComments, setOpenComments] = useState<Record<string, boolean>>({})

  const [revibes, setRevibes] = useState<RevibeState>({})
  const [savedItems, setSavedItems] = useState<SavedState>({})
  const [likes, setLikes] = useState<Record<string, LikeState>>({})
  const [counts, setCounts] = useState<Record<string, PostCounts>>({})

  const [quoteInputs, setQuoteInputs] = useState<TextState>({})
  const [quoteOpen, setQuoteOpen] = useState<Record<string, boolean>>({})
  const [revibeLoading, setRevibeLoading] = useState<LoadingState>({})
  const [saveLoading, setSaveLoading] = useState<LoadingState>({})
  const [likeLoading, setLikeLoading] = useState<LoadingState>({})

  const [editingComments, setEditingComments] = useState<TextState>({})
  const [commentEdits, setCommentEdits] = useState<TextState>({})
  const [commentActionLoading, setCommentActionLoading] = useState<LoadingState>({})

  const getKey = (type: ContentType, id: string) => `${type}:${id}`

  const goToDelete = (
    type: ContentType,
    id: string,
    post: {
      text?: string
      image_url?: string
      caption?: string
      event_title?: string | null
      created_at?: string
    },
  ) => {
    navigate(`/delete/${type}/${id}`, {
      state: {
        returnTo: window.location.pathname,
        post: { contentType: type, ...post },
      },
    })
  }

  const adjustCount = (
    type: ContentType,
    id: string,
    field: keyof PostCounts,
    delta: number,
  ) => {
    const key = getKey(type, id)
    const items = type === 'vibe' ? vibes : moments
    const item = items.find((post) => post.id === id)
    if (!item) return

    setCounts((previous) => ({
      ...previous,
      [key]: {
        ...(previous[key] || item),
        [field]: Math.max(
          0,
          (previous[key]?.[field] ?? item[field]) + delta,
        ),
      },
    }))
  }

  const setCount = (
    type: ContentType,
    id: string,
    field: keyof PostCounts,
    value: number,
  ) => {
    const key = getKey(type, id)
    const items = type === 'vibe' ? vibes : moments
    const item = items.find((post) => post.id === id)
    if (!item) return

    setCounts((previous) => ({
      ...previous,
      [key]: {
        ...(previous[key] || item),
        [field]: value,
      },
    }))
  }

  // Load VibeSpace content

  useEffect(() => {
    let active = true

    const loadContent = async () => {
      setLoading(true)
      setError('')
      setVibes([])
      setMoments([])
      setNextPage(null)

      try {
        let vibeData: Vibe[] = []
        let momentData: Moment[] = []
        let pageResponse:
          | Awaited<ReturnType<typeof vibespaceApi.getProfilePosts>>
          | Awaited<ReturnType<typeof vibespaceApi.getProfileVibes>>
          | Awaited<ReturnType<typeof vibespaceApi.getProfileMoments>>

        if (section === 'posts') {
          pageResponse = await vibespaceApi.getProfilePosts(username, 1)
          const posts = pageResponse.results as ProfilePost[]
          vibeData = posts
            .filter((post) => post.content_type === 'vibe')
            .map((post) => ({
              ...post,
              author_username: post.author_username,
              event: post.event_id,
              text: post.content_text,
              updated_at: post.created_at,
            }))
          momentData = posts
            .filter((post) => post.content_type === 'moment')
            .map((post) => ({
              ...post,
              author_username: post.author_username,
              event: post.event_id,
              image_url: post.image_url,
              caption: post.content_text,
              updated_at: post.created_at,
            }))
        } else if (section === 'vibes') {
          pageResponse = await vibespaceApi.getProfileVibes(username, 1)
          vibeData = pageResponse.results
        } else {
          pageResponse = await vibespaceApi.getProfileMoments(username, 1)
          momentData = pageResponse.results
        }

        if (!active) return
        setVibes(vibeData)
        setMoments(momentData)
        setNextPage(pageResponse.next)
        setCounts(
          Object.fromEntries([
            ...vibeData.map((item) => [getKey('vibe', item.id), item]),
            ...momentData.map((item) => [getKey('moment', item.id), item]),
          ]),
        )
      } catch {
        if (active) {
          setError('Unable to load VibeSpace content. Please try again.')
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    void loadContent()

    return () => {
      active = false
    }
  }, [section, username])

  const loadMore = async () => {
    if (nextPage === null) return
    setLoadingMore(true)
    setError('')

    try {
      if (section === 'posts') {
        const page = await vibespaceApi.getProfilePosts(username, nextPage)
        const newVibes: Vibe[] = page.results
          .filter((post) => post.content_type === 'vibe')
          .map((post) => ({
            ...post,
            event: post.event_id,
            text: post.content_text,
            updated_at: post.created_at,
          }))
        const newMoments: Moment[] = page.results
          .filter((post) => post.content_type === 'moment')
          .map((post) => ({
            ...post,
            event: post.event_id,
            caption: post.content_text,
            updated_at: post.created_at,
          }))
        setVibes((previous) => [...previous, ...newVibes])
        setMoments((previous) => [...previous, ...newMoments])
        setCounts((previous) => ({
          ...previous,
          ...Object.fromEntries([
            ...newVibes.map((item) => [getKey('vibe', item.id), item]),
            ...newMoments.map((item) => [getKey('moment', item.id), item]),
          ]),
        }))
        setNextPage(page.next)
      } else if (section === 'vibes') {
        const page = await vibespaceApi.getProfileVibes(username, nextPage)
        setVibes((previous) => [...previous, ...page.results])
        setCounts((previous) => ({
          ...previous,
          ...Object.fromEntries(
            page.results.map((item) => [getKey('vibe', item.id), item]),
          ),
        }))
        setNextPage(page.next)
      } else {
        const page = await vibespaceApi.getProfileMoments(username, nextPage)
        setMoments((previous) => [...previous, ...page.results])
        setCounts((previous) => ({
          ...previous,
          ...Object.fromEntries(
            page.results.map((item) => [getKey('moment', item.id), item]),
          ),
        }))
        setNextPage(page.next)
      }
    } catch {
      setError('Unable to load more posts. Please try again.')
    } finally {
      setLoadingMore(false)
    }
  }

  // Load the current user's saved content and Revibes

  useEffect(() => {
    if (!isAuthenticated) {
      return
    }

    let cancelled = false

    const loadInteractions = async () => {
      const allItems = [
        ...vibes.map((item) => ({
          type: 'vibe' as const,
          id: item.id,
        })),
        ...moments.map((item) => ({
          type: 'moment' as const,
          id: item.id,
        })),
      ]

      try {
        const savedData = await vibespaceApi.getSavedContent()

        if (cancelled) return

        const savedMap: SavedState = {}

        savedData.forEach((item: SavedContent) => {
          if (item.vibe) {
            savedMap[getKey('vibe', item.vibe)] = item.id
          }

          if (item.moment) {
            savedMap[getKey('moment', item.moment)] = item.id
          }
        })

        setSavedItems(savedMap)
      } catch {
        if (!cancelled) setSavedItems({})
      }

      const results = await Promise.all(
        allItems.map(async (item) => {
          const [revibeResult, likeResult] = await Promise.allSettled([
            item.type === 'vibe'
              ? vibespaceApi.getVibeRevibe(item.id)
              : vibespaceApi.getMomentRevibe(item.id),
            vibespaceApi.getLikeState(item.type, item.id),
          ])

          return {
            key: getKey(item.type, item.id),
            revibe:
              revibeResult.status === 'fulfilled'
                ? revibeResult.value
                : null,
            like:
              likeResult.status === 'fulfilled'
                ? likeResult.value
                : null,
            likeFailed: likeResult.status === 'rejected',
          }
        }),
      )

      if (cancelled) return

      const revibeMap: RevibeState = {}
      const likeMap: Record<string, LikeState> = {}

      results.forEach((result) => {
        revibeMap[result.key] = result.revibe
        if (result.like) {
          likeMap[result.key] = result.like
        }
      })
      if (results.some((result) => result.likeFailed)) {
        setError('Unable to load Like states. Please refresh the page.')
      }

      setRevibes(revibeMap)
      setLikes(likeMap)
    }

    void loadInteractions()

    return () => {
      cancelled = true
    }
  }, [isAuthenticated, vibes, moments])

  const handleLike = async (type: ContentType, id: string) => {
    const key = getKey(type, id)
    setLikeLoading((previous) => ({ ...previous, [key]: true }))

    try {
      const updated = likes[key]?.liked
        ? await vibespaceApi.unlikeContent(type, id)
        : await vibespaceApi.likeContent(type, id)
      setLikes((previous) => ({ ...previous, [key]: updated }))
      setCount(type, id, 'like_count', updated.like_count)
    } catch {
      setError('Unable to update your Like. Please try again.')
    } finally {
      setLikeLoading((previous) => ({ ...previous, [key]: false }))
    }
  }

  // Load comments when a comment panel is opened

  const toggleComments = async (
    type: ContentType,
    id: string,
  ) => {
    const key = getKey(type, id)
    const isOpening = !openComments[key]

    setOpenComments((previous) => ({
      ...previous,
      [key]: isOpening,
    }))

    if (!isOpening || comments[key]) return

    setCommentLoading((previous) => ({
      ...previous,
      [key]: true,
    }))

    try {
      const data =
        type === 'vibe'
          ? await vibespaceApi.getVibeComments(id)
          : await vibespaceApi.getMomentComments(id)

      setComments((previous) => ({
        ...previous,
        [key]: data,
      }))
    } catch {
      setError('Unable to load comments. Please try again.')
    } finally {
      setCommentLoading((previous) => ({
        ...previous,
        [key]: false,
      }))
    }
  }

  // Publish comment

  const handleCommentSubmit = async (
    event: FormEvent<HTMLFormElement>,
    type: ContentType,
    id: string,
  ) => {
    event.preventDefault()

    const key = getKey(type, id)
    const text = commentInputs[key]?.trim()

    if (!text || !isAuthenticated) return

    setCommentSubmitting((previous) => ({
      ...previous,
      [key]: true,
    }))

    try {
      const newComment =
        type === 'vibe'
          ? await vibespaceApi.createVibeComment(id, text)
          : await vibespaceApi.createMomentComment(id, text)

      setComments((previous) => ({
        ...previous,
        [key]: [...(previous[key] || []), newComment],
      }))
      adjustCount(type, id, 'comment_count', 1)

      setCommentInputs((previous) => ({
        ...previous,
        [key]: '',
      }))
    } catch {
      setError('Unable to publish your comment. Please try again.')
    } finally {
      setCommentSubmitting((previous) => ({
        ...previous,
        [key]: false,
      }))
    }
  }

  // Edit comment

  const handleCommentEdit = async (commentId: string, contentKey: string) => {
    const text = commentEdits[commentId]?.trim()

    if (!text) return

    setCommentActionLoading((previous) => ({
      ...previous,
      [commentId]: true,
    }))

    try {
      const updated = await vibespaceApi.updateComment(commentId, text)

      setComments((previous) => ({
        ...previous,
        [contentKey]: (previous[contentKey] || []).map((comment) =>
          comment.id === commentId ? updated : comment,
        ),
      }))

      setEditingComments((previous) => {
        const next = { ...previous }
        delete next[commentId]
        return next
      })
    } catch {
      setError('Unable to update this comment. Please try again.')
    } finally {
      setCommentActionLoading((previous) => ({
        ...previous,
        [commentId]: false,
      }))
    }
  }

  // Delete comment

  const handleCommentDelete = async (
    commentId: string,
    contentKey: string,
    type: ContentType,
    contentId: string,
  ) => {
    if (!window.confirm('Delete this comment?')) return

    setCommentActionLoading((previous) => ({
      ...previous,
      [commentId]: true,
    }))

    try {
      await vibespaceApi.deleteComment(commentId)

      setComments((previous) => ({
        ...previous,
        [contentKey]: (previous[contentKey] || []).filter(
          (comment) => comment.id !== commentId,
        ),
      }))
      adjustCount(type, contentId, 'comment_count', -1)
    } catch {
      setError('Unable to delete this comment. Please try again.')
    } finally {
      setCommentActionLoading((previous) => ({
        ...previous,
        [commentId]: false,
      }))
    }
  }

  // Direct or Quote Revibe

  const handleRevibe = async (
    type: ContentType,
    id: string,
    revibeType: 'direct' | 'quote',
  ) => {
    const key = getKey(type, id)
    const quoteText = quoteInputs[key]?.trim() || ''

    if (!isAuthenticated) return

    if (revibeType === 'quote' && !quoteText) {
      setError('Please write something to publish a Quote Revibe.')
      return
    }

    setRevibeLoading((previous) => ({
      ...previous,
      [key]: true,
    }))

    let countDelta = 0

    try {
      const existing = revibes[key]

      if (existing) {
        if (revibeType === 'direct') {
          await (type === 'vibe'
            ? vibespaceApi.removeVibeRevibe(id)
            : vibespaceApi.removeMomentRevibe(id))

          setRevibes((previous) => ({
            ...previous,
            [key]: null,
          }))
          countDelta = -1
          setSuccess('Revibe removed.')
        } else {
          const updated =
            type === 'vibe'
              ? await vibespaceApi.revibeVibe(id, {
                  revibe_type: 'quote',
                  quote_text: quoteText,
                })
              : await vibespaceApi.revibeMoment(id, {
                  revibe_type: 'quote',
                  quote_text: quoteText,
                })

          setRevibes((previous) => ({
            ...previous,
            [key]: updated,
          }))
          setSuccess('Quote Revibe updated.')
        }
      } else {
        const created =
          type === 'vibe'
            ? await vibespaceApi.revibeVibe(id, {
                revibe_type: revibeType,
                ...(revibeType === 'quote' ? { quote_text: quoteText } : {}),
              })
            : await vibespaceApi.revibeMoment(id, {
                revibe_type: revibeType,
                ...(revibeType === 'quote' ? { quote_text: quoteText } : {}),
              })

        setRevibes((previous) => ({
          ...previous,
          [key]: created,
        }))
        countDelta = 1
        setSuccess('Your Revibe has been published.')
      }

      if (countDelta !== 0) {
        adjustCount(type, id, 'revibe_count', countDelta)
      }

      setQuoteInputs((previous) => ({
        ...previous,
        [key]: '',
      }))

      setQuoteOpen((previous) => ({
        ...previous,
        [key]: false,
      }))
    } catch {
      setError('Unable to process your Revibe. Please try again.')
    } finally {
      setRevibeLoading((previous) => ({
        ...previous,
        [key]: false,
      }))
    }
  }

  // Save or unsave content

  const handleSave = async (
    type: ContentType,
    id: string,
  ) => {
    const key = getKey(type, id)
    const wasSaved = Boolean(savedItems[key])

    if (!isAuthenticated) return

    setSaveLoading((previous) => ({
      ...previous,
      [key]: true,
    }))

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
          type === 'vibe'
            ? await vibespaceApi.saveVibe(id)
            : await vibespaceApi.saveMoment(id)

        setSavedItems((previous) => ({
          ...previous,
          [key]: saved.id,
        }))
      }
      adjustCount(type, id, 'save_count', wasSaved ? -1 : 1)
    } catch {
      setError('Unable to update saved content. Please try again.')
    } finally {
      setSaveLoading((previous) => ({
        ...previous,
        [key]: false,
      }))
    }
  }

  // Share content

  const handleShare = async (
    type: ContentType,
    id: string,
  ) => {
    const url = `${window.location.origin}${window.location.pathname}#${type}-${id}`
    let shared = false

    try {
      if (navigator.share) {
        await navigator.share({
          title: type === 'vibe' ? 'BYB Vibe' : 'BYB Moment',
          url,
        })
        shared = true
      } else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url)
        shared = true
      } else {
        setError('Sharing is not supported by this browser.')
      }
      if (shared) {
        const result = await vibespaceApi.shareContent(type, id)
        setCount(type, id, 'share_count', result.share_count)
      }
    } catch (shareError) {
      if (shareError instanceof Error && shareError.name === 'AbortError') {
        return
      }

      setError('Unable to share this content.')
    }
  }

  const formatDate = (date: string) =>
    new Date(date).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })

  // Reusable interaction controls

  const renderActions = (
    type: ContentType,
    id: string,
    onDelete?: () => void,
  ) => {
    const key = getKey(type, id)
    const currentRevibe = revibes[key]
    const postCounts = counts[key]

    return (
      <>
        <div className="vibespace-interaction-actions">
          <button
            type="button"
            className={likes[key]?.liked ? 'active' : ''}
            disabled={likeLoading[key]}
            aria-label={
              `Like; ${postCounts?.like_count ?? 0} total likes`
            }
            title={`${postCounts?.like_count ?? 0} likes`}
            aria-pressed={Boolean(likes[key]?.liked)}
            onClick={() => void handleLike(type, id)}
          >
            <PostActionIcon name="like" active={likes[key]?.liked} />
            <span>{postCounts?.like_count ?? 0}</span>
          </button>
          <button
            type="button"
            className={openComments[key] ? 'active' : ''}
            aria-label={`Comments; ${postCounts?.comment_count ?? 0} total`}
            title={`${postCounts?.comment_count ?? 0} comments`}
            aria-expanded={Boolean(openComments[key])}
            onClick={() => void toggleComments(type, id)}
          >
            <PostActionIcon name="comment" />
            <span>{postCounts?.comment_count ?? 0}</span>
          </button>

          {isAuthenticated && (
            <>
              <button
                type="button"
                className={currentRevibe ? 'active' : ''}
                disabled={revibeLoading[key]}
                aria-label={`Revibe; ${postCounts?.revibe_count ?? 0} total`}
                title={`${postCounts?.revibe_count ?? 0} Revibes`}
                aria-pressed={Boolean(currentRevibe)}
                onClick={() => {
                  if (currentRevibe?.revibe_type === 'direct') {
                    void handleRevibe(type, id, 'direct')
                  } else {
                    setQuoteOpen((previous) => ({
                      ...previous,
                      [key]: !previous[key],
                    }))
                  }
                }}
              >
                <PostActionIcon name="revibe" />
                <span>{postCounts?.revibe_count ?? 0}</span>
              </button>

              <button
                type="button"
                disabled={saveLoading[key]}
                className={savedItems[key] ? 'active' : ''}
                aria-label={`Save; ${postCounts?.save_count ?? 0} total saves`}
                title={`${postCounts?.save_count ?? 0} saves`}
                aria-pressed={Boolean(savedItems[key])}
                onClick={() => void handleSave(type, id)}
              >
                <PostActionIcon name="save" />
                <span>{postCounts?.save_count ?? 0}</span>
              </button>
            </>
          )}

          <button
            type="button"
            aria-label={`Share; ${postCounts?.share_count ?? 0} total shares`}
            title={`${postCounts?.share_count ?? 0} shares`}
            onClick={() => void handleShare(type, id)}
          >
            <PostActionIcon name="share" />
            <span>{postCounts?.share_count ?? 0}</span>
          </button>

          {onDelete && (
            <button
              type="button"
              className="vibespace-delete-action"
              aria-label={`Delete this ${type}`}
              title={`Delete this ${type}`}
              onClick={onDelete}
            >
              <PostActionIcon name="delete" />
            </button>
          )}
        </div>

        {isAuthenticated && quoteOpen[key] && (
          <form
            className="vibespace-quote-form"
            onSubmit={(event) => {
              event.preventDefault()
              void handleRevibe(type, id, 'quote')
            }}
          >
            <textarea
              value={quoteInputs[key] || ''}
              onChange={(event) =>
                setQuoteInputs((previous) => ({
                  ...previous,
                  [key]: event.target.value,
                }))
              }
              maxLength={1000}
              rows={3}
              placeholder="Add your perspective to this Revibe..."
              required
            />

            <div className="vibespace-quote-footer">
              <span>{(quoteInputs[key] || '').length}/1000</span>
              <button
                type="button"
                onClick={() =>
                  setQuoteOpen((previous) => ({
                    ...previous,
                    [key]: false,
                  }))
                }
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={revibeLoading[key] || !quoteInputs[key]?.trim()}
              >
                Publish Quote
              </button>
            </div>
          </form>
        )}

        {currentRevibe?.revibe_type === 'quote' && (
          <div className="vibespace-existing-revibe">
            <span>Your Quote Revibe</span>
            <p>{currentRevibe.quote_text}</p>
            <button
              type="button"
              disabled={revibeLoading[key]}
              onClick={() => {
                setQuoteInputs((previous) => ({
                  ...previous,
                  [key]: currentRevibe.quote_text,
                }))
                setQuoteOpen((previous) => ({
                  ...previous,
                  [key]: true,
                }))
              }}
            >
              Edit quote
            </button>
            <button
              type="button"
              disabled={revibeLoading[key]}
              onClick={() => void handleRevibe(type, id, 'direct')}
            >
              Remove Revibe
            </button>
          </div>
        )}

        {openComments[key] && (
          <div className="vibespace-comments">
            <h4>Discussion</h4>

            {commentLoading[key] ? (
              <p className="vibespace-interaction-empty">
                Loading comments...
              </p>
            ) : (comments[key] || []).length === 0 ? (
              <p className="vibespace-interaction-empty">
                No comments yet. Start the conversation.
              </p>
            ) : (
              <div className="vibespace-comment-list">
                {(comments[key] || []).map((comment) => {
                  const isCommentAuthor =
                    isAuthenticated &&
                    comment.author_username === currentUsername

                  return (
                    <article className="vibespace-comment" key={comment.id}>
                      <div className="vibespace-comment-header">
                        <strong>@{comment.author_username}</strong>
                        <span>{formatDate(comment.created_at)}</span>
                      </div>

                      {editingComments[comment.id] ? (
                        <div className="vibespace-comment-edit">
                          <textarea
                            value={commentEdits[comment.id] || ''}
                            maxLength={1000}
                            onChange={(event) =>
                              setCommentEdits((previous) => ({
                                ...previous,
                                [comment.id]: event.target.value,
                              }))
                            }
                          />

                          <div>
                            <button
                              type="button"
                              onClick={() => {
                                setEditingComments((previous) => {
                                  const next = { ...previous }
                                  delete next[comment.id]
                                  return next
                                })
                              }}
                            >
                              Cancel
                            </button>

                            <button
                              type="button"
                              disabled={
                                commentActionLoading[comment.id] ||
                                !commentEdits[comment.id]?.trim()
                              }
                              onClick={() =>
                                void handleCommentEdit(comment.id, key)
                              }
                            >
                              Save changes
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p>{comment.text}</p>
                      )}

                      {isCommentAuthor && !editingComments[comment.id] && (
                        <div className="vibespace-comment-actions">
                          <button
                            type="button"
                            onClick={() => {
                              setCommentEdits((previous) => ({
                                ...previous,
                                [comment.id]: comment.text,
                              }))
                              setEditingComments((previous) => ({
                                ...previous,
                                [comment.id]: key,
                              }))
                            }}
                          >
                            Edit
                          </button>

                          <button
                            type="button"
                            disabled={commentActionLoading[comment.id]}
                            onClick={() =>
                              void handleCommentDelete(
                                comment.id,
                                key,
                                type,
                                id,
                              )
                            }
                          >
                            Delete
                          </button>
                        </div>
                      )}
                    </article>
                  )
                })}
              </div>
            )}

            {isAuthenticated ? (
              <form
                className="vibespace-comment-form"
                onSubmit={(event) =>
                  void handleCommentSubmit(event, type, id)
                }
              >
                <textarea
                  value={commentInputs[key] || ''}
                  onChange={(event) =>
                    setCommentInputs((previous) => ({
                      ...previous,
                      [key]: event.target.value,
                    }))
                  }
                  placeholder="Write a comment..."
                  maxLength={1000}
                  rows={2}
                  required
                />

                <button
                  type="submit"
                  disabled={
                    commentSubmitting[key] ||
                    !commentInputs[key]?.trim()
                  }
                >
                  {commentSubmitting[key] ? 'Posting...' : 'Post comment'}
                </button>
              </form>
            ) : (
              <p className="vibespace-interaction-empty">
                Log in to join the discussion.
              </p>
            )}
          </div>
        )}
      </>
    )
  }

  const posts = [
    ...vibes.map((item) => ({ type: 'vibe' as const, item })),
    ...moments.map((item) => ({ type: 'moment' as const, item })),
  ].sort(
    (left, right) => (
      new Date(right.item.created_at).getTime() -
        new Date(left.item.created_at).getTime() ||
      right.item.id.localeCompare(left.item.id) ||
      left.type.localeCompare(right.type)
    ),
  )

  return (
    <div className="vibespace-content">
      {error && (
        <div
          className="vibespace-message vibespace-message-error"
          role="alert"
        >
          {error}
        </div>
      )}

      {success && (
        <div
          className="vibespace-message vibespace-message-success"
          role="status"
        >
          {success}
        </div>
      )}

      {section === 'posts' && (
        <section className="vibespace-section vibespace-post-section">
          <div className="vibespace-section-heading">
            <div>
              <h2>Posts</h2>
              <p>Vibes and Moments, together in one timeline.</p>
            </div>
            <span className="vibespace-count">{posts.length}</span>
          </div>
          <div className="vibespace-post-list">
            {loading ? (
              <p className="vibespace-empty-state">Loading posts...</p>
            ) : posts.length === 0 ? (
              <div className="vibespace-empty-state">
                <h3>Your story starts here.</h3>
                <p>No posts have been published here yet.</p>
              </div>
            ) : posts.map(({ type, item }) => (
              <article
                className="vibespace-post"
                key={`${type}:${item.id}`}
              >
                <div className="vibespace-post-meta">
                  <span>{type === 'vibe' ? 'Vibe' : 'Moment'}</span>
                  <span>{formatDate(item.created_at)}</span>
                  {item.event_title && (
                    <span className="vibespace-event-tag">
                      {item.event_title}
                    </span>
                  )}
                </div>
                {type === 'vibe' ? (
                  <p className="vibespace-post-text">
                    {(item as Vibe).text}
                  </p>
                ) : (
                  <div className="vibespace-profile-moment">
                    <img
                      src={(item as Moment).image_url}
                      alt={(item as Moment).caption || 'VibeSpace Moment'}
                      loading="lazy"
                    />
                    {(item as Moment).caption && (
                      <p>{(item as Moment).caption}</p>
                    )}
                  </div>
                )}
                {renderActions(
                  type,
                  item.id,
                  isOwnProfile && item.author_username === currentUsername
                    ? () => {
                        if (type === 'vibe') {
                          goToDelete('vibe', item.id, {
                            text: (item as Vibe).text,
                            event_title: item.event_title,
                            created_at: item.created_at,
                          })
                        } else {
                          goToDelete('moment', item.id, {
                            image_url: (item as Moment).image_url,
                            caption: (item as Moment).caption,
                            event_title: item.event_title,
                            created_at: item.created_at,
                          })
                        }
                      }
                    : undefined,
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {section === 'vibes' && (
      <section className="vibespace-section vibespace-post-section">
        <div className="vibespace-section-heading">
          <div>
            <h2>Vibes</h2>
            <p>Share your thoughts and experiences.</p>
          </div>
          <span className="vibespace-count">{vibes.length}</span>
        </div>

        <div className="vibespace-post-list">
          {loading ? (
            <p className="vibespace-empty-state">Loading Vibes...</p>
          ) : vibes.length === 0 ? (
            <div className="vibespace-empty-state">
              <h3>Your story starts here.</h3>
              <p>
                No Vibes have been published here yet.
              </p>
            </div>
          ) : (
            vibes.map((vibe) => (
              <article className="vibespace-post" id={`vibe-${vibe.id}`} key={vibe.id}>
                <div className="vibespace-post-meta">
                  <span>{formatDate(vibe.created_at)}</span>

                  {vibe.event_title && (
                    <span className="vibespace-event-tag">
                      {vibe.event_title}
                    </span>
                  )}
                </div>

                <p className="vibespace-post-text">{vibe.text}</p>

                {renderActions(
                  'vibe',
                  vibe.id,
                  isOwnProfile && vibe.author_username === currentUsername
                    ? () => goToDelete('vibe', vibe.id, {
                        text: vibe.text,
                        event_title: vibe.event_title,
                        created_at: vibe.created_at,
                      })
                    : undefined,
                )}
              </article>
            ))
          )}
        </div>
      </section>
      )}

      {section === 'moments' && (
      <section className="vibespace-section vibespace-post-section">
        <div className="vibespace-section-heading">
          <div>
            <h2>Moments</h2>
            <p>Share photographs from experiences worth remembering.</p>
          </div>
          <span className="vibespace-count">{moments.length}</span>
        </div>

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
              <article className="vibespace-moment-card" id={`moment-${moment.id}`} key={moment.id}>
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

                  {renderActions(
                    'moment',
                    moment.id,
                    isOwnProfile &&
                      moment.author_username === currentUsername
                      ? () => goToDelete('moment', moment.id, {
                          image_url: moment.image_url,
                          caption: moment.caption,
                          event_title: moment.event_title,
                          created_at: moment.created_at,
                        })
                      : undefined,
                  )}
                </div>
              </article>
            ))
          )}
        </div>
      </section>
      )}

      {!loading && nextPage !== null && (
        <button
          className="profile-load-more"
          type="button"
          onClick={() => void loadMore()}
          disabled={loadingMore}
        >
          {loadingMore ? 'Loading...' : 'Load more'}
        </button>
      )}
    </div>
  )
}
