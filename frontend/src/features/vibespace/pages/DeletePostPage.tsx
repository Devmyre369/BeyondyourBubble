
import { useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'

import vibespaceApi from '../../../services/vibespaceApi'
import './delete-post.css'

interface DeletePostPreview {
  contentType?: 'vibe' | 'moment'
  text?: string
  image_url?: string
  caption?: string
  event_title?: string | null
  created_at?: string
}

interface DeletePostLocationState {
  post?: DeletePostPreview
  returnTo?: string
}

function formatDate(value?: string) {
  if (!value) return ''
  return new Date(value).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export default function DeletePostPage() {
  const { contentType = '', id = '' } = useParams()
  const location = useLocation()
  const navigate = useNavigate()

  const state = (location.state || {}) as DeletePostLocationState
  const preview = state.post
  const returnTo = state.returnTo || '/home'

  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')

  const isValidType = contentType === 'vibe' || contentType === 'moment'
  const label = contentType === 'moment' ? 'Moment' : 'Vibe'

  const handleCancel = () => {
    navigate(returnTo, { replace: true })
  }

  const handleConfirm = async () => {
    if (!isValidType || !id) return

    setDeleting(true)
    setError('')

    try {
      if (contentType === 'vibe') {
        await vibespaceApi.deleteVibe(id)
      } else {
        await vibespaceApi.deleteMoment(id)
      }
      navigate(returnTo, { replace: true })
    } catch {
      setError(`Unable to delete this ${label}. Please try again.`)
      setDeleting(false)
    }
  }

  if (!isValidType || !id) {
    return (
      <main className="delete-post-page">
        <div className="delete-post-card">
          <span className="delete-post-eyebrow">DELETE POST</span>
          <h1>Post not found</h1>
          <p className="delete-post-message">
            This post could not be found. It may already have been deleted.
          </p>
          <div className="delete-post-actions">
            <Link className="delete-post-cancel" to="/home">
              Back to feed
            </Link>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="delete-post-page">
      <div className="delete-post-card">
        <span className="delete-post-eyebrow">
          DELETE {label.toUpperCase()}
        </span>
        <h1>Delete this {label}?</h1>
        <p className="delete-post-message">
          This action is permanent and cannot be undone. This {label} will be
          removed from your VibeSpace and the BYB feed.
        </p>

        {(preview?.text || preview?.caption || preview?.image_url) && (
          <div className="delete-post-preview">
            {preview?.image_url && (
              <img src={preview.image_url} alt="" loading="lazy" />
            )}
            {preview?.text && (
              <p className="delete-post-preview-text">{preview.text}</p>
            )}
            {preview?.caption && (
              <p className="delete-post-preview-text">{preview.caption}</p>
            )}
            {(preview?.event_title || preview?.created_at) && (
              <div className="delete-post-preview-meta">
                {preview?.event_title && <span>{preview.event_title}</span>}
                {preview?.created_at && (
                  <span>{formatDate(preview.created_at)}</span>
                )}
              </div>
            )}
          </div>
        )}

        {error && (
          <p className="delete-post-error" role="alert">
            {error}
          </p>
        )}

        <div className="delete-post-actions">
          <button
            type="button"
            className="delete-post-cancel"
            onClick={handleCancel}
            disabled={deleting}
          >
            Cancel
          </button>
          <button
            type="button"
            className="delete-post-confirm"
            onClick={() => void handleConfirm()}
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : `Delete ${label}`}
          </button>
        </div>
      </div>
    </main>
  )
}
