
import { useEffect, useRef, useState } from 'react'
import {
  Navigate,
  Outlet,
  Route,
  Routes,
} from 'react-router-dom'

import WelcomePage from './features/auth/pages/WelcomePage'
import LoginPage from './features/auth/pages/LoginPage'
import SignupPage from './features/auth/pages/SignupPage'
import VerifySignupPage from './features/auth/pages/VerifySignupPage'
import ForgotPasswordPage from './features/auth/pages/ForgotPasswordPage'
import ResetPasswordPage from './features/auth/pages/ResetPasswordPage'

import ProtectedRoute from './features/auth/components/ProtectedRoute'
import ProfileRoute from './features/profile/components/ProfileRoute'

import ProfileSetupPage from './features/profile/pages/ProfileSetupPage'
import ProfilePage from './features/profile/pages/ProfilePage'
import ProfileEditPage from './features/profile/pages/ProfileEditPage'

import FeedPage from './features/feed/FeedPage'
import SavedPage from './features/feed/SavedPage'
import CreatePostPage from './features/feed/CreatePostPage'
import DeletePostPage from './features/vibespace/pages/DeletePostPage'
import EventsPage from './features/events/EventsPage'
import EventCreatePage from './features/events/EventCreatePage'
import HubDiscoverPage from './features/hubs/HubDiscoverPage'
import HubDetailPage from './features/hubs/HubDetailPage'
import SearchPage from './features/search/SearchPage'
import PublicUserProfilePage from './features/search/PublicUserProfilePage'
import NotificationsPage from './features/notifications/NotificationsPage'

import AppLayout from './components/layout/AppLayout'
import SplashScreen from './components/SplashScreen'

import { useAuth } from './context/AuthContext'
import { FollowProvider } from './context/FollowProvider'

import './features/profile/components/profile-experience.css'

function PublicProfileLayout() {
  const { isAuthenticated } = useAuth()

  return isAuthenticated ? <AppLayout /> : <Outlet />
}

export default function App() {
  const { isAuthenticated } = useAuth()

  const [showSplash, setShowSplash] = useState(true)

  const splashTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const previousAuthState = useRef(isAuthenticated)

  // Initial app launch: show splash for 1.6 seconds.
  useEffect(() => {
    splashTimer.current = setTimeout(() => {
      setShowSplash(false)
      splashTimer.current = null
    }, 1600)

    return () => {
      if (splashTimer.current) {
        clearTimeout(splashTimer.current)
        splashTimer.current = null
      }
    }
  }, [])

  // Successful login/signup: show splash for 3 seconds.
  useEffect(() => {
    const wasAuthenticated = previousAuthState.current

    previousAuthState.current = isAuthenticated

    if (!wasAuthenticated && isAuthenticated) {
      if (splashTimer.current) {
        clearTimeout(splashTimer.current)
      }

      setShowSplash(true)

      splashTimer.current = setTimeout(() => {
        setShowSplash(false)
        splashTimer.current = null
      }, 3000)
    }
  }, [isAuthenticated])

  return (
    <>
      <FollowProvider>
        <Routes>
          <Route path="/" element={<WelcomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          <Route
            path="/verify-signup"
            element={<VerifySignupPage />}
          />

          <Route
            path="/forgot-password"
            element={<ForgotPasswordPage />}
          />

          <Route
            path="/reset-password"
            element={<ResetPasswordPage />}
          />

          <Route element={<PublicProfileLayout />}>
            <Route
              path="/users/:username/:section?"
              element={<PublicUserProfilePage />}
            />
          </Route>

          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route
                path="/complete-profile"
                element={<ProfileSetupPage />}
              />

              <Route element={<ProfileRoute />}>
                <Route path="/home" element={<FeedPage />} />

                <Route path="/saved" element={<SavedPage />} />

                <Route
                  path="/discover"
                  element={<Navigate to="/home" replace />}
                />

                <Route
                  path="/create/vibe"
                  element={<CreatePostPage type="vibe" />}
                />

                <Route
                  path="/create/moment"
                  element={<CreatePostPage type="moment" />}
                />

                <Route
                  path="/delete/:contentType/:id"
                  element={<DeletePostPage />}
                />

                <Route path="/events" element={<EventsPage />} />

                <Route
                  path="/hubs/:hubId/events/create"
                  element={<EventCreatePage />}
                />

                <Route
                  path="/notifications"
                  element={<NotificationsPage />}
                />

                <Route path="/search" element={<SearchPage />} />

                <Route path="/hubs" element={<HubDiscoverPage />} />

                <Route
                  path="/hubs/:hubId"
                  element={<HubDetailPage />}
                />

                <Route
                  path="/profile/:section?"
                  element={<ProfilePage />}
                />

                <Route
                  path="/edit-profile"
                  element={<ProfileEditPage />}
                />
              </Route>
            </Route>
          </Route>

          <Route
            path="*"
            element={<Navigate to="/" replace />}
          />
        </Routes>
      </FollowProvider>

      {showSplash && <SplashScreen />}
    </>
  )
}
