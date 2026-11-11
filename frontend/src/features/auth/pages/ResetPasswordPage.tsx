
import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import axios from 'axios'

import AuthLayout from '../components/AuthLayout'
import authApi from '../../../services/authApi'

interface LocationState {
  email?: string
}

export default function ResetPasswordPage() {
  const navigate = useNavigate()
  const location = useLocation()

  const state = location.state as LocationState | null
  const email = state?.email || ''

  const [otp, setOtp] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (!email) {
      setError('Reset session not found. Please request a new password reset.')
      return
    }

    if (!/^\d{6}$/.test(otp)) {
      setError('Please enter a valid six-digit OTP.')
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)

    try {
      const response = await authApi.confirmPasswordReset(
        email,
        otp,
        newPassword,
        confirmPassword,
      )

      setSuccess(response.message || 'Password reset successful.')

      window.setTimeout(() => {
        navigate('/login', { replace: true })
      }, 1500)
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data as {
          detail?: string
          message?: string
          otp?: string | string[]
          email?: string | string[]
          new_password?: string[]
          confirm_password?: string[]
        } | undefined

        const otpError = Array.isArray(data?.otp)
          ? data.otp[0]
          : data?.otp

        const emailError = Array.isArray(data?.email)
          ? data.email[0]
          : data?.email

        setError(
          data?.detail ||
          data?.message ||
          otpError ||
          emailError ||
          data?.new_password?.[0] ||
          data?.confirm_password?.[0] ||
          'Unable to reset your password. Please try again.'
        )
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  if (!email) {
    return (
      <AuthLayout
        eyebrow="ACCOUNT RECOVERY"
        title="Reset session not found."
        subtitle="Please request a new password reset."
      >
        <Link
          className="auth-submit-button auth-button-link"
          to="/forgot-password"
        >
          Request Password Reset
        </Link>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      eyebrow="SECURE YOUR ACCOUNT"
      title="Create a new password."
      subtitle={`Enter the verification code sent to ${email} and choose a new password.`}
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}

        {success && (
          <div className="auth-success" role="status">
            {success}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="otp">Verification code</label>
          <input
            id="otp"
            name="otp"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            placeholder="Enter 6-digit OTP"
            maxLength={6}
            pattern="[0-9]{6}"
            value={otp}
            onChange={(event) =>
              setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))
            }
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="new-password">New password</label>
          <input
            id="new-password"
            name="new_password"
            type="password"
            autoComplete="new-password"
            placeholder="Enter your new password"
            minLength={8}
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="confirm-password">Confirm new password</label>
          <input
            id="confirm-password"
            name="confirm_password"
            type="password"
            autoComplete="new-password"
            placeholder="Re-enter your new password"
            minLength={8}
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            required
          />
        </div>

        <button
          className="auth-submit-button"
          type="submit"
          disabled={loading || Boolean(success)}
        >
          {loading ? 'Resetting password...' : 'Reset Password'}
        </button>

        <p className="auth-switch-text">
          Remember your password? <Link to="/login">Back to login</Link>
        </p>
      </form>
    </AuthLayout>
  )
}
