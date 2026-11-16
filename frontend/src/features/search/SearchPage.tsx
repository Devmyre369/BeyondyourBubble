import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { useAuth } from '../../context/AuthContext'
import {
  searchApi,
  type SearchCategory,
  type SearchResponse,
} from '../../services/searchApi'
import GlobalSearchBox from './GlobalSearchBox'
import './search-page.css'

type ResultCategory = Exclude<SearchCategory, 'all'>

const resultCategories: { id: ResultCategory; label: string }[] = [
  { id: 'posts', label: 'Posts & Vibes' },
  { id: 'users', label: 'People' },
  { id: 'events', label: 'Events' },
  { id: 'hubs', label: 'Hubs' },
]

const categories: { id: SearchCategory; label: string }[] = [
  { id: 'all', label: 'All' },
  ...resultCategories,
]

type SearchPageState =
  | { key: string; status: 'success'; response: SearchResponse }
  | { key: string; status: 'error' }

function isSearchCategory(value: string | null): value is SearchCategory {
  return categories.some((category) => category.id === value)
}

function formatDate(value: string | null): string {
  if (!value) return 'Date to be announced'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Date to be announced'
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

export default function SearchPage() {
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const query = searchParams.get('q')?.trim() || ''
  const categoryParam = searchParams.get('category')
  const category = isSearchCategory(categoryParam) ? categoryParam : 'all'
  const requestedPage = Number(searchParams.get('page') || 1)
  const page =
    Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1
  const [retryToken, setRetryToken] = useState(0)
  const requestKey = JSON.stringify([query, category, page, retryToken])
  const [state, setState] = useState<SearchPageState | null>(null)

  useEffect(() => {
    if (query.length < 2) return

    let active = true
    void searchApi
      .search(query, { category, page, pageSize: 10 })
      .then((response) => {
        if (active) setState({ key: requestKey, status: 'success', response })
      })
      .catch((error: unknown) => {
        if (!active) return
        console.error('Global search failed:', error)
        setState({ key: requestKey, status: 'error' })
      })

    return () => {
      active = false
    }
  }, [category, page, query, requestKey])

  const handleSearch = (nextQuery: string) => {
    setSearchParams({ q: nextQuery, category: 'all', page: '1' })
  }

  const selectCategory = (nextCategory: SearchCategory) => {
    setSearchParams({
      q: query,
      category: nextCategory,
      page: '1',
    })
  }

  const selectPage = (nextPage: number) => {
    setSearchParams({
      q: query,
      category,
      page: String(nextPage),
    })
  }

  const currentState =
    state?.key === requestKey ? state : query.length >= 2 ? null : undefined
  const response =
    currentState?.status === 'success' ? currentState.response : null
  const currentResults = response?.results
  const visibleCategories =
    category === 'all'
      ? resultCategories
      : resultCategories.filter((item) => item.id === category)
  const showResultsLoading =
    query.length >= 2 && currentState === null
  const showResultsError = currentState?.status === 'error'
  const nextAvailable =
    category === 'all'
      ? Boolean(
          response &&
            (response.has_more.posts ||
              response.has_more.users ||
              response.has_more.events ||
              response.has_more.hubs),
        )
      : Boolean(response?.has_more[category])
  const previousAvailable =
    page > 1 &&
    (category === 'all'
      ? Boolean(
          response &&
            (response.counts.posts > 0 ||
              response.counts.users > 0 ||
              response.counts.events > 0 ||
              response.counts.hubs > 0),
        )
      : Boolean(response && response.counts[category] > 0))

  return (
    <div className="search-page">
      <header className="search-page-header">
        <span className="search-page-eyebrow">DISCOVER BEYOND YOUR BUBBLE</span>
        <h1>Search BYB</h1>
        <p>Find posts, people, Vibes, events, and Hubs across the community.</p>
        <GlobalSearchBox
          key={query}
          initialQuery={query}
          onSearch={handleSearch}
        />
      </header>

      {query.length >= 2 && (
        <section className="search-results" aria-labelledby="search-results-title">
          <div className="search-results-heading">
            <div>
              <span className="search-page-eyebrow">SEARCH RESULTS</span>
              <h2 id="search-results-title">
                Results for <span>“{query}”</span>
              </h2>
            </div>
            {response && (
              <p>
                {response.counts.posts +
                  response.counts.users +
                  response.counts.events +
                  response.counts.hubs}{' '}
                matches
              </p>
            )}
          </div>

          <div className="search-category-tabs" aria-label="Search categories">
            {categories.map((item) => (
              <button
                type="button"
                key={item.id}
                aria-pressed={category === item.id}
                className={category === item.id ? 'active' : ''}
                onClick={() => selectCategory(item.id)}
              >
                {item.label}
                {response && (
                  <span>
                    {item.id === 'all'
                      ? response.counts.posts +
                        response.counts.users +
                        response.counts.events +
                        response.counts.hubs
                      : response.counts[item.id]}
                  </span>
                )}
              </button>
            ))}
          </div>

          {showResultsLoading && (
            <div className="search-page-state" role="status">
              Searching the BYB community...
            </div>
          )}

          {showResultsError && (
            <div className="search-page-state search-page-error" role="alert">
              <p>Search is temporarily unavailable. Please try again.</p>
              <button
                type="button"
                onClick={() => setRetryToken((previous) => previous + 1)}
              >
                Try again
              </button>
            </div>
          )}

          {response && currentResults && (
            <>
              {visibleCategories.map((item) => {
                const items = currentResults[item.id]
                const count = response.counts[item.id]

                return (
                  <section
                    className="search-result-group"
                    aria-labelledby={`search-${item.id}-title`}
                    key={item.id}
                  >
                    {category === 'all' && (
                      <div className="search-result-group-heading">
                        <h3 id={`search-${item.id}-title`}>{item.label}</h3>
                        <span>{count}</span>
                      </div>
                    )}
                    {items.length > 0 ? (
                      <div className="search-result-grid">
                        {item.id === 'posts' &&
                          currentResults.posts.map((post) => (
                            <article
                              className="search-result-card search-post-card"
                              key={`${post.content_type}:${post.id}`}
                            >
                              <div className="search-post-heading">
                                <span className="search-result-badge">
                                  {post.content_type === 'vibe' ? 'Vibe' : 'Moment'}
                                </span>
                                <Link
                                  to={
                                    post.author_username === user?.username
                                      ? '/profile'
                                      : `/users/${encodeURIComponent(post.author_username)}`
                                  }
                                >
                                  @{post.author_username}
                                </Link>
                                <time dateTime={post.created_at}>
                                  {formatDate(post.created_at)}
                                </time>
                              </div>
                              {post.image_url && (
                                <img
                                  className="search-post-image"
                                  src={post.image_url}
                                  alt=""
                                  loading="lazy"
                                />
                              )}
                              {post.content_text && (
                                <p>{post.content_text}</p>
                              )}
                              {post.event_title && (
                                <span className="search-post-event">
                                  Event: {post.event_title}
                                </span>
                              )}
                            </article>
                          ))}

                        {item.id === 'users' &&
                          currentResults.users.map((resultUser) => {
                            const fullName =
                              `${resultUser.first_name} ${resultUser.last_name}`.trim()
                            const profilePath =
                              resultUser.username === user?.username
                                ? '/profile'
                                : `/users/${encodeURIComponent(resultUser.username)}`

                            return (
                              <Link
                                className="search-result-card search-user-card"
                                to={profilePath}
                                key={resultUser.username}
                              >
                                {resultUser.profile_picture ? (
                                  <img
                                    src={resultUser.profile_picture}
                                    alt=""
                                    loading="lazy"
                                  />
                                ) : (
                                  <span
                                    className="search-avatar-placeholder"
                                    aria-hidden="true"
                                  >
                                    {(fullName || resultUser.username)
                                      .charAt(0)
                                      .toUpperCase()}
                                  </span>
                                )}
                                <span className="search-user-details">
                                  <strong>{fullName || resultUser.username}</strong>
                                  <span>@{resultUser.username}</span>
                                  {resultUser.bio && <small>{resultUser.bio}</small>}
                                  {resultUser.city && <small>{resultUser.city}</small>}
                                </span>
                                <span
                                  className="search-result-arrow"
                                  aria-hidden="true"
                                >
                                  →
                                </span>
                              </Link>
                            )
                          })}

                        {item.id === 'events' &&
                          currentResults.events.map((event) => (
                            <article
                              className="search-result-card search-event-card"
                              key={event.id}
                            >
                              <span className="search-result-badge">Event</span>
                              <h4>{event.title}</h4>
                              <p>{event.description || 'No description provided.'}</p>
                              <div>
                                <span>{formatDate(event.starts_at)}</span>
                                {(event.venue_name || event.city) && (
                                  <span>
                                    {[event.venue_name, event.city]
                                      .filter(Boolean)
                                      .join(' · ')}
                                  </span>
                                )}
                              </div>
                            </article>
                          ))}

                        {item.id === 'hubs' &&
                          currentResults.hubs.map((hub) => (
                            <Link
                              className="search-result-card search-hub-card"
                              to={`/hubs/${encodeURIComponent(hub.id)}`}
                              key={hub.id}
                            >
                              {hub.logo ? (
                                <img src={hub.logo} alt="" loading="lazy" />
                              ) : (
                                <span className="search-avatar-placeholder" aria-hidden="true">
                                  {hub.name.charAt(0).toUpperCase()}
                                </span>
                              )}
                              <span className="search-hub-details">
                                <strong>
                                  {hub.name}
                                  {hub.is_verified && (
                                    <span className="search-hub-verified" aria-label="Verified">
                                      ✓
                                    </span>
                                  )}
                                </strong>
                                <span>{hub.short_description || hub.hub_type}</span>
                                {hub.city && <small>{hub.city}</small>}
                              </span>
                              <span className="search-result-arrow" aria-hidden="true">
                                →
                              </span>
                            </Link>
                          ))}
                      </div>
                    ) : (
                      <p className="search-no-category-results">
                        No {item.label.toLowerCase()} matched this search.
                      </p>
                    )}
                  </section>
                )
              })}

              {response.counts.posts +
                response.counts.users +
                response.counts.events +
                response.counts.hubs ===
                0 && (
                <div className="search-page-state" role="status">
                  <h3>No results found</h3>
                  <p>Try a different name, keyword, event, or Hub.</p>
                </div>
              )}

              {(previousAvailable || nextAvailable) && (
                <nav className="search-pagination" aria-label="Search results pages">
                  <button
                    type="button"
                    onClick={() => selectPage(page - 1)}
                    disabled={!previousAvailable}
                  >
                    Previous
                  </button>
                  <span>Page {page}</span>
                  <button
                    type="button"
                    onClick={() => selectPage(page + 1)}
                    disabled={!nextAvailable}
                  >
                    Next
                  </button>
                </nav>
              )}
            </>
          )}
        </section>
      )}

      {query.length < 2 && (
        <div className="search-page-state">
          <h2>Search the BYB community</h2>
          <p>Enter at least two characters to find people, posts, events, and Hubs.</p>
        </div>
      )}
    </div>
  )
}
