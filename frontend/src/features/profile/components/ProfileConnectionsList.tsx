import axios from 'axios'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import {
  profileApi,
  type PaginatedResponse,
  type PublicConnectionUser,
} from '../../../services/profileApi'
import FollowButton from './FollowButton'

interface ProfileConnectionsListProps {
  username: string
  relationship: 'followers' | 'following'
}

export default function ProfileConnectionsList({
  username,
  relationship,
}: ProfileConnectionsListProps) {
  const [response, setResponse] =
    useState<PaginatedResponse<PublicConnectionUser> | null>(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    void profileApi.getProfileConnections(username, relationship, 1)
      .then((result) => {
        if (!active) return
        setResponse(result)
        setPage(1)
      })
      .catch((requestError: unknown) => {
        if (!active) return
        if (!axios.isAxiosError(requestError)) {
          console.error('Unable to load profile connections:', requestError)
        }
        setError(
          axios.isAxiosError(requestError) && requestError.response?.status === 404
            ? 'This profile is no longer available.'
            : 'Unable to load this list. Please try again.',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [relationship, username])

  const loadMore = async () => {
    if (!response?.next) return
    const nextPage = response.next
    setLoadingMore(true)
    setError('')
    try {
      const next = await profileApi.getProfileConnections(
        username,
        relationship,
        nextPage,
      )
      setResponse((previous) => previous
        ? { ...next, results: [...previous.results, ...next.results] }
        : next)
      setPage(nextPage)
    } catch (requestError: unknown) {
      if (!axios.isAxiosError(requestError)) {
        console.error('Unable to load more profile connections:', requestError)
      }
      setError('Unable to load more profiles. Please try again.')
    } finally {
      setLoadingMore(false)
    }
  }

  if (loading) {
    return <p className="profile-list-state" role="status">Loading {relationship}...</p>
  }

  if (error && !response) {
    return <p className="profile-list-state profile-list-error" role="alert">{error}</p>
  }

  if (!response?.results.length) {
    return (
      <div className="profile-list-state">
        <h3>No {relationship} yet</h3>
        <p>When people appear here, you can discover more of the BYB community.</p>
      </div>
    )
  }

  return (
    <section className="profile-connections" aria-label={relationship}>
      <div className="profile-connection-list">
        {response.results.map((person) => {
          const fullName = `${person.first_name} ${person.last_name}`.trim()
          return (
            <article className="profile-connection-card" key={person.username}>
              <Link
                className="profile-connection-identity"
                to={`/users/${encodeURIComponent(person.username)}`}
              >
                {person.profile_picture ? (
                  <img src={person.profile_picture} alt="" loading="lazy" />
                ) : (
                  <span className="profile-connection-avatar" aria-hidden="true">
                    {(fullName || person.username).charAt(0).toUpperCase()}
                  </span>
                )}
                <span>
                  <strong>{fullName || person.username}</strong>
                  <small>@{person.username}</small>
                  {person.byb_signature && <small>{person.byb_signature}</small>}
                </span>
              </Link>
              <FollowButton
                username={person.username}
                initialFollowing={person.is_following}
              />
            </article>
          )
        })}
      </div>
      {error && <p className="profile-list-error" role="alert">{error}</p>}
      {response.next && (
        <button
          className="profile-load-more"
          type="button"
          onClick={() => void loadMore()}
          disabled={loadingMore}
        >
          {loadingMore ? 'Loading...' : `Load more (${page + 1})`}
        </button>
      )}
    </section>
  )
}
