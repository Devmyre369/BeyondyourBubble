import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import HubCreateModal from './HubCreateModal'
import {
  hubsApi,
  type HubDiscoveryResponse,
  type HubType,
  type HubListItem,
} from '../../services/hubsApi'
import './hub-discover.css'

const HUB_CATEGORIES: { value: HubType; label: string }[] = [
  { value: 'company', label: 'Company' },
  { value: 'organisation', label: 'Organisation' },
  { value: 'college', label: 'College' },
  { value: 'college_club', label: 'College Club' },
  { value: 'college_department', label: 'College Department' },
  { value: 'community', label: 'Community' },
]

const CATEGORY_LABELS: Record<HubType, string> = {
  company: 'Company',
  organisation: 'Organisation',
  college: 'College',
  college_club: 'College Club',
  college_department: 'College Department',
  community: 'Community',
}

interface DiscoveryQuery {
  search: string
  hub_type: HubType | ''
  page: number
}

function isHubType(value: string): value is HubType {
  return HUB_CATEGORIES.some((category) => category.value === value)
}

function HubCard({ hub }: { hub: HubListItem }) {
  const titleId = `hub-title-${hub.id}`

  return (
    <Link className="hub-card-link" to={`/hubs/${hub.id}`}>
      <article className="hub-card" aria-labelledby={titleId}>
        <div className="hub-card-cover">
          {hub.cover_image && (
            <img
              className="hub-card-cover-image"
              src={hub.cover_image}
              alt=""
              loading="lazy"
              onError={(event) => {
                event.currentTarget.style.visibility = 'hidden'
              }}
            />
          )}
          <div className="hub-card-cover-shade" />
          <span className="hub-card-category">
            {CATEGORY_LABELS[hub.hub_type]}
          </span>
          <span className="hub-card-cover-mark" aria-hidden="true">
            BYB
          </span>
        </div>

        <div className="hub-card-content">
          <div className="hub-card-heading">
            <div className="hub-card-logo" aria-hidden="true">
              {hub.logo && (
                <img
                  src={hub.logo}
                  alt=""
                  loading="lazy"
                  onError={(event) => {
                    event.currentTarget.style.visibility = 'hidden'
                  }}
                />
              )}
              <span>{hub.name.trim().charAt(0).toUpperCase() || 'H'}</span>
            </div>

            <div className="hub-card-title-group">
              <div className="hub-card-title-line">
                <h3 id={titleId}>{hub.name}</h3>
                {hub.is_verified && (
                  <span
                    className="hub-card-verified"
                    role="img"
                    aria-label="Verified Hub"
                    title="Verified Hub"
                  >
                    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                      <path
                        d="m5 10 3.2 3.2L15.5 6"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                )}
              </div>

              <p className="hub-card-location">
                <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path
                    d="M16 8.3c0 4.1-6 9.2-6 9.2S4 12.4 4 8.3a6 6 0 1 1 12 0Z"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  />
                  <circle
                    cx="10"
                    cy="8"
                    r="2"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  />
                </svg>
                <span>{hub.city || 'Location not listed'}</span>
              </p>
            </div>
          </div>

          <p className="hub-card-description">
            {hub.short_description || 'No description available yet.'}
          </p>
        </div>
      </article>
    </Link>
  )
}

export default function HubDiscoverPage() {
  const navigate = useNavigate()
  const pendingRequests = useRef(
    new Map<string, Promise<HubDiscoveryResponse>>(),
  )
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [searchInput, setSearchInput] = useState('')
  const [query, setQuery] = useState<DiscoveryQuery>({
    search: '',
    hub_type: '',
    page: 1,
  })
  const [discovery, setDiscovery] = useState<HubDiscoveryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      const search = searchInput.trim()
      setQuery((previous) =>
        previous.search === search
          ? previous
          : { ...previous, search, page: 1 },
      )
    }, 300)

    return () => window.clearTimeout(timeoutId)
  }, [searchInput])

  useEffect(() => {
    let isCurrentRequest = true
    const requestKey = JSON.stringify([
      query.search,
      query.hub_type,
      query.page,
      retryCount,
    ])

    const loadHubs = async () => {
      setLoading(true)
      setError('')

      let request = pendingRequests.current.get(requestKey)
      if (!request) {
        request = hubsApi.getHubs({
          search: query.search || undefined,
          hub_type: query.hub_type || undefined,
          page: query.page,
        })
        pendingRequests.current.set(requestKey, request)
      }

      try {
        const response = await request

        if (isCurrentRequest) {
          setDiscovery(response)
        }
      } catch (requestError) {
        if (isCurrentRequest) {
          console.error('Hub discovery failed:', requestError)
          setError('Unable to load Hubs right now. Please try again.')
        }
      } finally {
        if (pendingRequests.current.get(requestKey) === request) {
          pendingRequests.current.delete(requestKey)
        }

        if (isCurrentRequest) {
          setLoading(false)
        }
      }
    }

    void loadHubs()

    return () => {
      isCurrentRequest = false
    }
  }, [query, retryCount])

  const handleCategoryChange = (value: string) => {
    if (value !== '' && !isHubType(value)) return

    const hubType = value === '' ? '' : value
    setQuery((previous) =>
      previous.hub_type === hubType
        ? previous
        : { ...previous, hub_type: hubType, page: 1 },
    )
  }

  const clearFilters = () => {
    setSearchInput('')
    setQuery({ search: '', hub_type: '', page: 1 })
  }

  const retry = () => setRetryCount((previous) => previous + 1)

  return (
    <section
      className="hub-discover-page"
      aria-labelledby="hub-discover-page-title"
    >
      <header className="hub-discover-header">
        <div className="hub-discover-header-copy">
          <span className="hub-discover-eyebrow">
            COMMUNITY, WITHOUT BORDERS
          </span>
          <h1 id="hub-discover-page-title">Find your people.</h1>
          <p>
            Discover the colleges, clubs, organisations, and communities
            shaping what comes next.
          </p>
          <button
            className="hub-create-trigger"
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
          >
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path
                d="M10 4v12M4 10h12"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
            </svg>
            Create Hub
          </button>
        </div>
        <div className="hub-discover-header-art" aria-hidden="true">
          <span className="hub-discover-orbit hub-discover-orbit-outer" />
          <span className="hub-discover-orbit hub-discover-orbit-inner" />
          <span className="hub-discover-art-mark">H</span>
        </div>
      </header>

      <section
        className="hub-discover-tools"
        aria-label="Search and filter Hubs"
      >
        <div className="hub-search-field">
          <label htmlFor="hub-discover-search">Search Hubs</label>
          <div className="hub-search-control">
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <circle
                cx="8.8"
                cy="8.8"
                r="5.8"
                stroke="currentColor"
                strokeWidth="1.6"
              />
              <path
                d="m13.2 13.2 4 4"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
              />
            </svg>
            <input
              id="hub-discover-search"
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.currentTarget.value)}
              placeholder="Search names, descriptions, slugs, or parent organisations"
              autoComplete="off"
            />
            {searchInput && (
              <button
                className="hub-search-clear"
                type="button"
                onClick={() => setSearchInput('')}
                aria-label="Clear search"
              >
                ×
              </button>
            )}
          </div>
        </div>

        <div className="hub-category-field">
          <label htmlFor="hub-discover-category">Category</label>
          <select
            id="hub-discover-category"
            value={query.hub_type}
            onChange={(event) =>
              handleCategoryChange(event.currentTarget.value)
            }
          >
            <option value="">All categories</option>
            {HUB_CATEGORIES.map((category) => (
              <option key={category.value} value={category.value}>
                {category.label}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section
        className="hub-discover-results"
        aria-labelledby="hub-results-title"
        aria-busy={loading}
      >
        <div className="hub-results-heading">
          <div>
            <span className="hub-discover-eyebrow">YOUR NEXT SPACE</span>
            <h2 id="hub-results-title">Hubs to explore</h2>
          </div>
          {!loading && discovery && (
            <span className="hub-results-count">
              {discovery.count} {discovery.count === 1 ? 'Hub' : 'Hubs'}
            </span>
          )}
        </div>

        <div className="hub-results-content">
          {loading && (
            <div className="hub-discover-state" role="status">
              <span className="hub-loading-indicator" aria-hidden="true" />
              <p>Discovering Hubs...</p>
            </div>
          )}

          {!loading && error && (
            <div className="hub-discover-state hub-error-state" role="alert">
              <span className="hub-state-mark" aria-hidden="true">
                !
              </span>
              <h3>Hubs are temporarily unavailable</h3>
              <p>{error}</p>
              <button type="button" onClick={retry}>
                Try again
              </button>
            </div>
          )}

          {!loading && !error && discovery?.results.length === 0 && (
            <div className="hub-discover-state hub-empty-state" role="status">
              <span className="hub-state-mark" aria-hidden="true">
                H
              </span>
              <h3>No Hubs found</h3>
              <p>
                {query.search || query.hub_type
                  ? 'Try another search or clear your filters to explore all Hubs.'
                  : 'There are no Hubs to show right now. Check back soon.'}
              </p>
              {(query.search || query.hub_type) && (
                <button type="button" onClick={clearFilters}>
                  Clear filters
                </button>
              )}
            </div>
          )}

          {!loading && !error && discovery && discovery.results.length > 0 && (
            <>
              <div className="hub-card-grid">
                {discovery.results.map((hub) => (
                  <HubCard hub={hub} key={hub.id} />
                ))}
              </div>

              {(discovery.previous !== null || discovery.next !== null) && (
                <nav
                  className="hub-pagination"
                  aria-label="Hub results pagination"
                >
                  <button
                    type="button"
                    onClick={() => {
                      const previousPage = discovery.previous
                      if (previousPage !== null) {
                        setQuery((previous) => ({
                          ...previous,
                          page: previousPage,
                        }))
                      }
                    }}
                    disabled={discovery.previous === null}
                  >
                    <span aria-hidden="true">←</span>
                    Previous
                  </button>
                  <span className="hub-pagination-page">
                    Page {query.page}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      const nextPage = discovery.next
                      if (nextPage !== null) {
                        setQuery((previous) => ({
                          ...previous,
                          page: nextPage,
                        }))
                      }
                    }}
                    disabled={discovery.next === null}
                  >
                    Next
                    <span aria-hidden="true">→</span>
                  </button>
                </nav>
              )}
            </>
          )}
        </div>
      </section>

      {isCreateModalOpen && (
        <HubCreateModal
          onClose={() => setIsCreateModalOpen(false)}
          onCreated={(hub) => {
            setIsCreateModalOpen(false)
            navigate(`/hubs/${hub.id}`)
          }}
        />
      )}
    </section>
  )
}
