
import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
} from 'react'

import { useAuth } from '../../../context/AuthContext'

import vibespaceApi, {
  type Comment,
  type Moment,
  type Revibe,
  type SavedContent,
  type Vibe,
} from '../../../services/vibespaceApi'

interface VibeSpaceContentProps {
  username: string
}

type ContentType = 'vibe' | 'moment'

type CommentState = Record<string, Comment[]>
type TextState = Record<string, string>
type LoadingState = Record<string, boolean>
type RevibeState = Record<string, Revibe | null>
type SavedState = Record<string, string>

export default function VibeSpaceContent({
  username,
}: VibeSpaceContentProps) {
  const { user, isAuthenticated } = useAuth()

  const currentUsername = user?.username || ''
  const isOwnProfile = currentUsername === username

  const [vibes, setVibes] = useState<Vibe[]>([])
  const [moments, setMoments] = useState<Moment[]>([])

  const [loading, setLoading] = useState(true)

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Interaction state

  const [comments, setComments] = useState<CommentState>({})
  const [commentInputs, setCommentInputs] = useState<TextState>({})
  const [commentLoading, setCommentLoading] = useState<LoadingState>({})
  const [commentSubmitting, setCommentSubmitting] = useState<LoadingState>({})
  const [openComments, setOpenComments] = useState<Record<string, boolean>>({})

  const [revibes, setRevibes] = useState<RevibeState>({})
  const [savedItems, setSavedItems] = useState<SavedState>({})

  const [quoteInputs, setQuoteInputs] = useState<TextState>({})
  const [quoteOpen, setQuoteOpen] = useState<Record<string, boolean>>({})
  const [revibeLoading, setRevibeLoading] = useState<LoadingState>({})
  const [saveLoading, setSaveLoading] = useState<LoadingState>({})

  const [editingComments, setEditingComments] = useState<TextState>({})
  const [commentEdits, setCommentEdits] = useState<TextState>({})
  const [commentActionLoading, setCommentActionLoading] = useState<LoadingState>({})

  const getKey = (type: ContentType, id: string) => `${type}:${id}`

  // Load VibeSpace content

  const loadContent = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const [vibeData, momentData] = await Promise.all([
        vibespaceApi.getVibes(username),
        vibespaceApi.getMoments(username),
      ])

      setVibes(vibeData)
      setMoments(momentData)
    } catch {
      setError('Unable to load VibeSpace content. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [username])

  useEffect(() => {
    void loadContent()
  }, [loadContent])

  // Load the current user's saved content and Revibes

  useEffect(() => {
    if (!isAuthenticated) {
      setSavedItems({})
      setRevibes({})
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

      const results = await Promise.allSettled(
        allItems.map(async (item) => {
          const revibe =
            item.type === 'vibe'
              ? await vibespaceApi.getVibeRevibe(item.id)
              : await vibespaceApi.getMomentRevibe(item.id)

          return {
            key: getKey(item.type, item.id),
            revibe,
          }
        }),
      )

      if (cancelled) return

      const revibeMap: RevibeState = {}

      results.forEach((result) => {
        if (result.status === 'fulfilled') {
          revibeMap[result.value.key] = result.value.revibe
        }
      })

      setRevibes(revibeMap)
    }

    void loadInteractions()

    return () => {
      cancelled = true
    }
  }, [isAuthenticated, vibes, moments])

  // Delete Vibe

  const handleDeleteVibe = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this Vibe?')) {
      return
    }

    setError('')
    setSuccess('')

    try {
      await vibespaceApi.deleteVibe(id)
      setVibes((previous) => previous.filter((item) => item.id !== id))
      setSuccess('Vibe deleted successfully.')
    } catch {
      setError('Unable to delete this Vibe. Please try again.')
    }
  }

  // Delete Moment

  const handleDeleteMoment = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this Moment?')) {
      return
    }

    setError('')
    setSuccess('')

    try {
      await vibespaceApi.deleteMoment(id)
      setMoments((previous) => previous.filter((item) => item.id !== id))
      setSuccess('Moment deleted successfully.')
    } catch {
      setError('Unable to delete this Moment. Please try again.')
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
        setSuccess('Your Revibe has been published.')
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

    try {
      if (navigator.share) {
        await navigator.share({
          title: type === 'vibe' ? 'BYB Vibe' : 'BYB Moment',
          url,
        })
      } else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url)
        setSuccess('Content link copied to clipboard.')
      } else {
        setError('Sharing is not supported by this browser.')
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

  const renderActions = (type: ContentType, id: string) => {
    const key = getKey(type, id)
    const currentRevibe = revibes[key]

    return (
      <>
        <div className="vibespace-interaction-actions">
          <button
            type="button"
            className={openComments[key] ? 'active' : ''}
            onClick={() => void toggleComments(type, id)}
          >
            Comments
          </button>

          {isAuthenticated && (
            <>
              <button
                type="button"
                className={currentRevibe ? 'active' : ''}
                disabled={revibeLoading[key]}
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
                {revibeLoading[key]
                  ? 'Please wait...'
                  : currentRevibe?.revibe_type === 'direct'
                    ? 'Revibed'
                    : 'Revibe'}
              </button>

              <button
                type="button"
                disabled={saveLoading[key]}
                className={savedItems[key] ? 'active' : ''}
                onClick={() => void handleSave(type, id)}
              >
                {saveLoading[key]
                  ? 'Please wait...'
                  : savedItems[key]
                    ? 'Saved'
                    : 'Save'}
              </button>
            </>
          )}

          <button
            type="button"
            onClick={() => void handleShare(type, id)}
          >
            Share
          </button>
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
                              void handleCommentDelete(comment.id, key)
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

      {/* VIBES */}

      <section className="vibespace-card vibespace-post-section">
        <div className="vibespace-section-heading">
          <div>
            <h2>Your Vibes</h2>
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

                {renderActions('vibe', vibe.id)}

                {isOwnProfile && vibe.author_username === currentUsername && (
                  <div className="vibespace-post-actions">
                    <button
                      type="button"
                      onClick={() => void handleDeleteVibe(vibe.id)}
                    >
                      Delete
                    </button>
                  </div>
                )}
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

                  {renderActions('moment', moment.id)}

                  {isOwnProfile &&
                    moment.author_username === currentUsername && (
                      <button
                        type="button"
                        onClick={() => void handleDeleteMoment(moment.id)}
                      >
                        Delete
                      </button>
                    )}
                </div>
              </article>
            ))
          )}
        </div>
      </section>
    </div>
  )
}
