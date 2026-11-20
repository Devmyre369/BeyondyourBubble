import axios from 'axios'
import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext'
import { handshakesApi, type HandshakeStatusResponse } from '../../services/handshakesApi'
import './handshakes.css'

export default function HandshakeButton({ username }: { username: string }) {
  const { isAuthenticated, user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [loadedStatus, setLoadedStatus] = useState<{
    username: string
    value: HandshakeStatusResponse
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const state = loadedStatus?.username === username ? loadedStatus.value : null

  useEffect(() => {
    if (!isAuthenticated || user?.username.toLowerCase() === username.toLowerCase()) return
    let active = true
    handshakesApi.getStatus(username)
      .then((response) => { if (active) setLoadedStatus({ username, value: response }) })
      .catch(() => { if (active) setError('Handshake status could not be loaded.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [isAuthenticated, username, user?.username])

  if (user?.username.toLowerCase() === username.toLowerCase()) return null

  const doAction = async (action: 'send' | 'accept' | 'reject') => {
    if (!isAuthenticated) {
      const next = `${location.pathname}${location.search}${location.hash}`
      navigate(`/login?next=${encodeURIComponent(next)}`)
      return
    }
    if (action === 'reject' && !window.confirm(`Reject the Handshake request from @${username}?`)) return
    if (action === 'accept' && !state?.request_id) return

    setLoading(true)
    setError('')
    try {
      if (action === 'send') setLoadedStatus({ username, value: await handshakesApi.sendRequest(username) })
      else {
        await handshakesApi.respond(state!.request_id!, action)
        setLoadedStatus({ username, value: await handshakesApi.getStatus(username) })
      }
      window.dispatchEvent(new Event('byb:notifications-updated'))
    } catch (requestError: unknown) {
      const detail = axios.isAxiosError(requestError)
        ? requestError.response?.data?.detail
        : undefined
      setError(typeof detail === 'string' ? detail : 'Unable to update this Handshake. Please try again.')
      try { setLoadedStatus({ username, value: await handshakesApi.getStatus(username) }) } catch { /* retain current state */ }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="byb-handshake-control">
      {!isAuthenticated || state?.state === 'none' ? (
        <button type="button" className="byb-handshake-button" onClick={() => void doAction('send')} disabled={loading}>
          {loading ? 'Sending…' : 'Send Handshake'}
        </button>
      ) : state?.state === 'outgoing_pending' ? (
        <button type="button" className="byb-handshake-button is-pending" disabled>
          {loading ? 'Updating…' : 'Request pending'}
        </button>
      ) : state?.state === 'incoming_pending' ? (
        <div className="byb-handshake-actions">
          <button type="button" className="byb-handshake-button" onClick={() => void doAction('accept')} disabled={loading}>
            {loading ? 'Updating…' : 'Accept Handshake'}
          </button>
          <button type="button" className="byb-handshake-button is-secondary" onClick={() => void doAction('reject')} disabled={loading}>
            Reject
          </button>
        </div>
      ) : state?.state === 'connected' ? (
        <Link className="byb-handshake-button is-connected" to="/handshakes">Connected · Manage</Link>
      ) : state === null ? (
        <button type="button" className="byb-handshake-button is-pending" disabled>
          {error ? 'Handshake unavailable' : 'Loading status…'}
        </button>
      ) : (
        <button type="button" className="byb-handshake-button is-pending" disabled>
          {loading ? 'Loading…' : 'Handshake unavailable'}
        </button>
      )}
      {error && <span className="byb-handshake-error" role="alert">{error}</span>}
    </div>
  )
}
