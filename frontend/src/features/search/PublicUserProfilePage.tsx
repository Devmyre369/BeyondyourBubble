import axios from 'axios'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext'
import { profileApi, type UserProfile } from '../../services/profileApi'
import VibeSpaceContent from '../profile/components/VibeSpaceContent'
import './search-page.css'

type ProfileLoadState =
  | { username: string; status: 'loaded'; profile: UserProfile }
  | { username: string; status: 'not-found' | 'private' | 'error' }

export default function PublicUserProfilePage() {
  const { username = '' } = useParams()
  const { user } = useAuth()
  const [state, setState] = useState<ProfileLoadState | null>(null)

  useEffect(() => {
    let active = true
    void profileApi
      .getPublicProfile(username)
      .then((profile) => {
        if (active) setState({ username, status: 'loaded', profile })
      })
      .catch((error: unknown) => {
        if (!active) return
        const status = axios.isAxiosError(error)
          ? error.response?.status
          : undefined
        if (status !== 403 && status !== 404) {
          console.error('Unable to load public profile:', error)
        }
        setState({
          username,
          status:
            status === 404
              ? 'not-found'
              : status === 403
                ? 'private'
                : 'error',
        })
      })

    return () => {
      active = false
    }
  }, [username])

  const currentState =
    state?.username === username ? state : null

  if (!currentState) {
    return (
      <main className="public-profile-page">
        <div className="search-page-state" role="status">
          Loading profile...
        </div>
      </main>
    )
  }

  if (currentState.status !== 'loaded') {
    const message =
      currentState.status === 'not-found'
        ? 'This profile could not be found.'
        : currentState.status === 'private'
          ? 'This profile is private.'
          : 'We could not load this profile. Please try again later.'

    return (
      <main className="public-profile-page">
        <Link className="public-profile-back" to="/home">
          ← Back to BYB
        </Link>
        <div
          className={`search-page-state${currentState.status === 'error' ? ' search-page-error' : ''}`}
          role={currentState.status === 'error' ? 'alert' : 'status'}
        >
          {message}
        </div>
      </main>
    )
  }

  const { profile } = currentState
  const isOwnProfile = user?.username === profile.username
  if (profile.visibility === 'private' && !isOwnProfile) {
    return (
      <main className="public-profile-page">
        <Link className="public-profile-back" to="/home">
          ← Back to BYB
        </Link>
        <div className="search-page-state" role="status">
          This profile is private.
        </div>
      </main>
    )
  }

  const fullName = `${profile.first_name} ${profile.last_name}`.trim()
  const initials = `${profile.first_name.charAt(0)}${profile.last_name.charAt(0)}`
    .trim()
    .toUpperCase()

  return (
    <main className="public-profile-page">
      <Link className="public-profile-back" to="/home">
        ← Back to BYB
      </Link>
      <article className="public-profile-card">
        <div
          className="public-profile-cover"
          style={
            profile.cover_image
              ? { backgroundImage: `url("${profile.cover_image}")` }
              : undefined
          }
          aria-hidden="true"
        />
        <div className="public-profile-identity">
          {profile.profile_picture ? (
            <img
              className="public-profile-avatar"
              src={profile.profile_picture}
              alt=""
            />
          ) : (
            <span className="public-profile-avatar-placeholder" aria-hidden="true">
              {initials || profile.username.charAt(0).toUpperCase()}
            </span>
          )}
          <div className="public-profile-identity-copy">
            <h1>{fullName || profile.username}</h1>
            <p>
              @{profile.username}
              {profile.profile_type && ` · ${profile.profile_type}`}
            </p>
          </div>
        </div>
        <div className="public-profile-body">
          {profile.byb_signature && (
            <p className="public-profile-city">{profile.byb_signature}</p>
          )}
          {profile.bio && <p className="public-profile-bio">{profile.bio}</p>}
          {profile.city && (
            <p className="public-profile-city">⌖ {profile.city}</p>
          )}
        </div>
      </article>
      <div className="public-profile-content">
        <VibeSpaceContent username={profile.username} />
      </div>
    </main>
  )
}
