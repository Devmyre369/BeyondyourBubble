
import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import axios from 'axios'

import { useAuth } from '../../../context/AuthContext'
import profileApi from '../../../services/profileApi'

export default function ProfileRoute() {
  const {
    profile,
    profileLoaded,
    setProfile,
  } = useAuth()

  const [checkComplete, setCheckComplete] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (profileLoaded) return

    let active = true

    const loadProfile = async () => {
      try {
        const data = await profileApi.getMyProfile()

        if (active) {
          setProfile(data)
        }
      } catch (err) {
        if (!active) return

        if (axios.isAxiosError(err) && err.response?.status === 404) {
          setProfile(null)
        } else {
          setError('Unable to load your profile. Please try again.')
        }
      } finally {
        if (active) {
          setCheckComplete(true)
        }
      }
    }

    loadProfile()

    return () => {
      active = false
    }
  }, [profileLoaded, setProfile])

  const checking = !profileLoaded && !checkComplete

  if (checking) {
    return <div className="profile-loading">Loading your BYB profile...</div>
  }

  if (error) {
    return (
      <div className="profile-loading">
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>
          Try Again
        </button>
      </div>
    )
  }

  if (!profile) {
    return <Navigate to="/complete-profile" replace />
  }

  return <Outlet />
}
