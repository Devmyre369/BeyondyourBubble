
import { Navigate, Route, Routes } from 'react-router-dom'

import WelcomePage from './features/auth/pages/WelcomePage'
import LoginPage from './features/auth/pages/LoginPage'
import SignupPage from './features/auth/pages/SignupPage'
import VerifySignupPage from './features/auth/pages/VerifySignupPage'
import ForgotPasswordPage from './features/auth/pages/ForgotPasswordPage'
import ResetPasswordPage from './features/auth/pages/ResetPasswordPage'

import ProtectedRoute from './features/auth/components/ProtectedRoute'
import ProfileRoute from './features/profile/components/ProfileRoute'

import { useAuth } from './context/AuthContext'

function HomePage() {
  const { user, logout } = useAuth()

  return (
    <main className="home-placeholder">
      <div className="home-placeholder-content">
        <span className="auth-eyebrow">BEYOND YOUR BUBBLE</span>

        <h1>Welcome to BYB, {user?.username}.</h1>

        <p>Your journey beyond your bubble starts here.</p>

        <button
          type="button"
          className="auth-submit-button"
          onClick={logout}
        >
          Log Out
        </button>
      </div>
    </main>
  )
}

function CompleteProfilePage() {
  return (
    <main className="home-placeholder">
      <div className="home-placeholder-content">
        <span className="auth-eyebrow">BEYOND YOUR BUBBLE</span>

        <h1>Let's build your VibeSpace.</h1>

        <p>Complete your individual profile to continue.</p>
      </div>
    </main>
  )
}

export default function App() {
  return (
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

      <Route element={<ProtectedRoute />}>
        <Route path="/complete-profile" element={<CompleteProfilePage />} />

        <Route element={<ProfileRoute />}>
          <Route path="/home" element={<HomePage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
