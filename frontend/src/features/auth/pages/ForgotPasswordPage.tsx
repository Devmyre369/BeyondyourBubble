
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import axios from 'axios'

import AuthLayout from '../components/AuthLayout'
import authApi from '../../../services/authApi'

export default function ForgotPasswordPage() {
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setLoading(true)

    const normalizedEmail = email.trim().toLowerCase()

    try {
      const response = await authApi.requestPasswordReset(normalizedEmail)

      navigate('/reset-password', {
        state: { email: normalizedEmail },
      })

      // The backend intentionally uses a generic response
      // to avoid revealing whether an email is registered.
      void response
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data as {
          detail?: string
          message?: string
          email?: string[]
        } | undefined

        setError(
          data?.detail ||
          data?.message ||
          data?.email?.[0] ||
          'Unable to process your request. Please try again.'
        )
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      eyebrow="ACCOUNT RECOVERY"
      title="Forgot your password?"
      subtitle="Enter your registered email address to receive a password reset verification code."
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            name="email"
            type="email"
            placeholder="Enter your registered email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>

        <button
          className="auth-submit-button"
          type="submit"
          disabled={loading}
        >
          {loading ? 'Sending request...' : 'Continue'}
        </button>

        <p className="auth-switch-text">
          Remember your password? <Link to="/login">Back to login</Link>
        </p>
      </form>
    </AuthLayout>
  )
}
