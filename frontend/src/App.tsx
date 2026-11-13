
import { Navigate, Route, Routes } from 'react-router-dom'

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
import AppLayout from './components/layout/AppLayout'

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
        <Route
          path="/complete-profile"
          element={<ProfileSetupPage />}
        />

        <Route element={<ProfileRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/home" element={<FeedPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/edit-profile" element={<ProfileEditPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
