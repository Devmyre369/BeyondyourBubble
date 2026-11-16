import axios from 'axios'
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../../../context/AuthContext'
import { useFollowState } from '../../../context/useFollowState'
import { profileApi } from '../../../services/profileApi'

interface FollowButtonProps {
  username: string
  initialFollowing: boolean
  initialFollowersCount?: number
  className?: string
}

export default function FollowButton({
  username,
  initialFollowing,
  initialFollowersCount,
  className = '',
}: FollowButtonProps) {
  const { user, isAuthenticated } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const { state, applyMutation } = useFollowState(
    username,
    initialFollowing,
    initialFollowersCount,
  )
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (user?.username.toLowerCase() === username.toLowerCase()) return null

  const isFollowing = state?.isFollowing ?? initialFollowing
  const followersCount = state?.followersCount ?? initialFollowersCount

  const toggleFollow = async () => {
    if (!isAuthenticated) {
      const returnPath = `${location.pathname}${location.search}${location.hash}`
      navigate(`/login?next=${encodeURIComponent(returnPath)}`)
      return
    }

    setSubmitting(true)
    setError('')
    try {
      const response = isFollowing
        ? await profileApi.unfollowUser(username)
        : await profileApi.followUser(username)
      applyMutation(response)
    } catch (requestError: unknown) {
      const status = axios.isAxiosError(requestError)
        ? requestError.response?.status
        : undefined
      setError(
        status === 404
          ? 'This profile is no longer available.'
          : 'Unable to update your follow. Please try again.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={`follow-control ${className}`.trim()}>
      <button
        type="button"
        className={`follow-button${isFollowing ? ' is-following' : ''}`}
        onClick={() => void toggleFollow()}
        disabled={submitting}
        aria-pressed={isFollowing}
      >
        {submitting ? 'Saving...' : isFollowing ? 'Following' : 'Follow'}
      </button>
      {typeof followersCount === 'number' && (
        <span className="follow-count" aria-label={`${followersCount} followers`}>
          {followersCount}
        </span>
      )}
      {error && <span className="follow-error" role="alert">{error}</span>}
    </div>
  )
}
