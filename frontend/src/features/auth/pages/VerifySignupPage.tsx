
import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import axios from 'axios'

import AuthLayout from '../components/AuthLayout'
import { useAuth } from '../../../context/AuthContext'
import authApi from '../../../services/authApi'

interface LocationState {
  email?: string
}

export default function VerifySignupPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { completeAuthentication } = useAuth()

  const state = location.state as LocationState | null
  const email = state?.email || ''

  const [otp, setOtp] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    if (!email) {
      setError('Signup email is missing. Please sign up again.')
      return
    }

    if (!/^\d{6}$/.test(otp)) {
      setError('Please enter a valid six-digit OTP.')
      return
    }

    setLoading(true)

    try {
      const response = await authApi.verifySignup(email, otp)

      completeAuthentication(response)
      navigate('/home', { replace: true })
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data as {
          detail?: string
          message?: string
          otp?: string
          email?: string
        } | undefined

        setError(
          data?.detail ||
          data?.message ||
          data?.otp ||
          data?.email ||
          'OTP verification failed. Please try again.'
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
        eyebrow="EMAIL VERIFICATION"
        title="Signup session not found."
        subtitle="Please return to signup and start again."
      >
        <Link className="auth-submit-button auth-button-link" to="/signup">
          Back to Signup
        </Link>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      eyebrow="ONE LAST STEP"
      title="Verify your email."
      subtitle={`Enter the six-digit verification code sent to ${email}.`}
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && (
          <div className="auth-error" role="alert">
            {error}
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

        <button
          className="auth-submit-button"
          type="submit"
          disabled={loading || otp.length !== 6}
        >
          {loading ? 'Verifying...' : 'Verify Email'}
        </button>

        <p className="auth-switch-text">
          Wrong email address? <Link to="/signup">Go back to signup</Link>
        </p>
      </form>
    </AuthLayout>
  )
}
