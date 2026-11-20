import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { handshakesApi, type HandshakeItem, type HandshakePage } from '../../services/handshakesApi'
import './handshakes.css'

type Section = 'incoming' | 'outgoing' | 'connections'

const sectionLabels: Record<Section, string> = {
  incoming: 'Incoming',
  outgoing: 'Outgoing',
  connections: 'Connections',
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export default function HandshakesPage() {
  const [section, setSection] = useState<Section>('incoming')
  const [page, setPage] = useState<HandshakePage | null>(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [loading, setLoading] = useState(true)
  const [actionId, setActionId] = useState('')
  const [error, setError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  const fetchPage = useCallback((nextPage: number, activeSection: Section) => {
    return activeSection === 'incoming'
      ? handshakesApi.getIncoming(nextPage)
      : activeSection === 'outgoing'
        ? handshakesApi.getOutgoing(nextPage)
        : handshakesApi.getConnections(nextPage)
  }, [])

  const load = useCallback(async (nextPage: number, activeSection: Section) => {
    setLoading(true)
    setError('')
    try {
      const result = await fetchPage(nextPage, activeSection)
      setPage(result)
      setPageNumber(nextPage)
    } catch {
      setError('Handshake information could not be loaded. Please retry.')
    } finally {
      setLoading(false)
    }
  }, [fetchPage])

  useEffect(() => {
    let active = true
    const loadSection = async () => {
      try {
        const result = await fetchPage(1, section)
        if (!active) return
        setPage(result)
        setPageNumber(1)
      } catch {
        if (active) setError('Handshake information could not be loaded. Please retry.')
      } finally {
        if (active) setLoading(false)
      }
    }
    void loadSection()
    return () => { active = false }
  }, [fetchPage, section, refreshKey])

  const runAction = async (item: HandshakeItem, action: 'accept' | 'reject' | 'cancel' | 'remove') => {
    const person = `@${item.person.username}`
    if (action === 'reject' && !window.confirm(`Reject the Handshake request from ${person}?`)) return
    if (action === 'cancel' && !window.confirm(`Cancel your Handshake request to ${person}?`)) return
    if (action === 'remove' && !window.confirm(`Remove ${person} from your Handshake connections?`)) return

    setActionId(item.id)
    setLoading(true)
    setError('')
    try {
      if (action === 'remove') await handshakesApi.removeConnection(item.id)
      else await handshakesApi.respond(item.id, action)
      window.dispatchEvent(new Event('byb:notifications-updated'))
      setRefreshKey((value) => value + 1)
    } catch {
      setError('That Handshake action could not be completed. Refresh and try again.')
      setLoading(false)
    } finally {
      setActionId('')
    }
  }

  return (
    <main className="byb-handshakes-page">
      <header className="byb-handshakes-header">
        <div>
          <span className="byb-handshakes-eyebrow">YOUR NETWORK</span>
          <h1>Handshakes</h1>
          <p>Build mutual connections. Following and Handshakes stay separate.</p>
        </div>
        <button type="button" className="byb-handshakes-refresh" onClick={() => { setLoading(true); setError(''); setRefreshKey((value) => value + 1) }} disabled={loading}>
          Refresh
        </button>
      </header>

      <nav className="byb-handshakes-tabs" aria-label="Handshake lists">
        {(Object.keys(sectionLabels) as Section[]).map((value) => (
          <button
            key={value}
            type="button"
            className={section === value ? 'active' : ''}
            aria-current={section === value ? 'page' : undefined}
            onClick={() => { setLoading(true); setError(''); setSection(value) }}
          >
            {sectionLabels[value]}
            {section === value && page && <span>{page.count}</span>}
          </button>
        ))}
      </nav>

      {error && <div className="byb-handshakes-error" role="alert">{error}</div>}
      {loading ? (
        <div className="byb-handshakes-state" role="status">Loading Handshakes…</div>
      ) : page?.results.length ? (
        <section className="byb-handshake-list" aria-label={`${sectionLabels[section]} Handshakes`}>
          {page.results.map((item) => {
            const displayName = `${item.person.first_name} ${item.person.last_name}`.trim() || item.person.username
            return (
              <article className="byb-handshake-card" key={item.id}>
                <Link className="byb-handshake-person" to={`/users/${encodeURIComponent(item.person.username)}`}>
                  {item.person.profile_picture ? (
                    <img src={item.person.profile_picture} alt="" />
                  ) : (
                    <span className="byb-handshake-avatar-fallback" aria-hidden="true">{displayName.charAt(0).toUpperCase()}</span>
                  )}
                  <span>
                    <strong>{displayName}</strong>
                    <small>@{item.person.username}{item.person.byb_signature ? ` · ${item.person.byb_signature}` : ''}</small>
                  </span>
                </Link>
                <div className="byb-handshake-card-meta">
                  <span className={`byb-handshake-status status-${item.status}`}>{item.status}</span>
                  <time dateTime={item.created_at}>{formatDate(item.created_at)}</time>
                </div>
                <div className="byb-handshake-card-actions">
                  {section === 'incoming' && item.status === 'pending' && (
                    <>
                      <button type="button" onClick={() => void runAction(item, 'accept')} disabled={actionId === item.id}>
                        {actionId === item.id ? 'Saving…' : 'Accept'}
                      </button>
                      <button type="button" className="secondary" onClick={() => void runAction(item, 'reject')} disabled={actionId === item.id}>Reject</button>
                    </>
                  )}
                  {section === 'outgoing' && item.status === 'pending' && (
                    <button type="button" className="secondary" onClick={() => void runAction(item, 'cancel')} disabled={actionId === item.id}>Cancel request</button>
                  )}
                  {section === 'connections' && item.status === 'accepted' && (
                    <button type="button" className="danger" onClick={() => void runAction(item, 'remove')} disabled={actionId === item.id}>Remove</button>
                  )}
                </div>
              </article>
            )
          })}
        </section>
      ) : (
        <div className="byb-handshakes-state byb-handshakes-empty">
          <h2>{section === 'incoming' ? 'No incoming requests' : section === 'outgoing' ? 'No outgoing requests' : 'No connections yet'}</h2>
          <p>{section === 'connections' ? 'Send a Handshake request from someone’s profile to start building your network.' : 'New Handshake activity will appear here.'}</p>
          <Link to="/search">Discover people</Link>
        </div>
      )}

      {!loading && page && (page.previous !== null || page.next !== null) && (
        <div className="byb-handshakes-pagination">
          <button type="button" disabled={page.previous === null} onClick={() => void load(pageNumber - 1, section)}>Previous</button>
          <span>Page {pageNumber}</span>
          <button type="button" disabled={page.next === null} onClick={() => void load(pageNumber + 1, section)}>Next</button>
        </div>
      )}
    </main>
  )
}
