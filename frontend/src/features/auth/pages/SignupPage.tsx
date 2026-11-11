
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import axios from 'axios'

import AuthLayout from '../components/AuthLayout'
import authApi from '../../../services/authApi'

export default function SignupPage() {
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)

    try {
      const response = await authApi.signup({
        username: username.trim(),
        email: email.trim().toLowerCase(),
        password,
        confirm_password: confirmPassword,
      })

      navigate('/verify-signup', {
        state: { email: response.email || email.trim().toLowerCase() },
      })
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data as {
          detail?: string
          message?: string
          username?: string[]
          email?: string[]
          password?: string[]
          confirm_password?: string[]
        } | undefined

        setError(
          data?.detail ||
          data?.message ||
          data?.username?.[0] ||
          data?.email?.[0] ||
          data?.password?.[0] ||
          data?.confirm_password?.[0] ||
          'Unable to create your account. Please try again.'
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
      eyebrow="JOIN THE COMMUNITY"
      title="Step outside your bubble."
      subtitle="Create your BYB account and start discovering what is happening around you."
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            name="username"
            type="text"
            placeholder="Choose a username"
            autoComplete="username"
            minLength={3}
            maxLength={150}
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            name="email"
            type="email"
            placeholder="Enter your email address"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            placeholder="Create a password"
            autoComplete="new-password"
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="confirm-password">Confirm password</label>
          <input
            id="confirm-password"
            name="confirm_password"
            type="password"
            placeholder="Re-enter your password"
            autoComplete="new-password"
            minLength={8}
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            required
          />
        </div>

        <button
          className="auth-submit-button"
          type="submit"
          disabled={loading}
        >
          {loading ? 'Creating account...' : 'Create Account'}
        </button>

        <p className="auth-switch-text">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </AuthLayout>
  )
}
