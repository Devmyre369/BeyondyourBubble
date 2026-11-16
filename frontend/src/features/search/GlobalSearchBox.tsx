import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from 'react'
import { useAuth } from '../../context/AuthContext'
import {
  searchApi,
  type SearchResponse,
} from '../../services/searchApi'
import './global-search.css'

interface GlobalSearchBoxProps {
  initialQuery?: string
  onSearch: (query: string) => void
}

interface SearchSuggestion {
  label: string
  query: string
  category: string
}

function readSearchHistory(storageKey: string | null): string[] {
  if (!storageKey) return []

  try {
    const saved = localStorage.getItem(storageKey)
    if (!saved) return []

    const parsed: unknown = JSON.parse(saved)
    if (!Array.isArray(parsed)) return []
    return parsed.filter(
      (item): item is string =>
        typeof item === 'string' && item.trim().length > 0,
    )
  } catch (error) {
    console.error('Unable to load search history:', error)
    return []
  }
}

function suggestionsFromResults(
  response: SearchResponse | null,
  query: string,
): SearchSuggestion[] {
  if (!response) return []

  const suggestions: SearchSuggestion[] = []
  response.results.users.forEach((user) => {
    const name = `${user.first_name} ${user.last_name}`.trim()
    suggestions.push({
      label: name ? `${name} · @${user.username}` : `@${user.username}`,
      query: user.username,
      category: 'Person',
    })
  })
  response.results.hubs.forEach((hub) => {
    suggestions.push({
      label: hub.name,
      query: hub.name,
      category: 'Hub',
    })
  })
  response.results.events.forEach((event) => {
    suggestions.push({
      label: event.title,
      query: event.title,
      category: 'Event',
    })
  })
  response.results.posts.forEach((post) => {
    const excerpt = post.content_text.trim() || post.event_title || query
    suggestions.push({
      label: `@${post.author_username} · ${excerpt}`,
      query: query,
      category: post.content_type === 'vibe' ? 'Vibe' : 'Moment',
    })
  })

  return suggestions.slice(0, 7)
}

export default function GlobalSearchBox({
  initialQuery = '',
  onSearch,
}: GlobalSearchBoxProps) {
  const { user } = useAuth()
  const storageKey = user?.id
    ? `byb_search_history:${user.id}`
    : user?.username
      ? `byb_search_history:${user.username}`
      : null
  const listId = `search-options-${useId().replace(/:/g, '')}`
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [query, setQuery] = useState(initialQuery)
  const [history, setHistory] = useState(() => readSearchHistory(storageKey))
  const [historyError, setHistoryError] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [isSuggesting, setIsSuggesting] = useState(false)
  const [suggestionData, setSuggestionData] = useState<{
    query: string
    response: SearchResponse
  } | null>(null)
  const [suggestionError, setSuggestionError] = useState('')
  const normalizedQuery = query.trim()

  useEffect(() => {
    if (normalizedQuery.length < 2) return

    let cancelled = false
    const timeout = window.setTimeout(() => {
      setIsSuggesting(true)
      setSuggestionError('')
      void searchApi
        .search(normalizedQuery, { pageSize: 3 })
        .then((response) => {
          if (!cancelled) {
            setSuggestionData({ query: normalizedQuery, response })
          }
        })
        .catch((error: unknown) => {
          if (cancelled) return
          console.error('Search suggestions failed:', error)
          setSuggestionError('Suggestions are temporarily unavailable.')
        })
        .finally(() => {
          if (!cancelled) setIsSuggesting(false)
        })
    }, 250)

    return () => {
      cancelled = true
      window.clearTimeout(timeout)
    }
  }, [normalizedQuery])

  useEffect(() => {
    if (!isOpen) return
    const handlePointerDown = (event: PointerEvent) => {
      if (
        event.target instanceof Node &&
        !containerRef.current?.contains(event.target)
      ) {
        setIsOpen(false)
      }
    }
    document.addEventListener('pointerdown', handlePointerDown)
    return () => document.removeEventListener('pointerdown', handlePointerDown)
  }, [isOpen])

  const matchingHistory = useMemo(
    () =>
      history.filter((item) =>
        normalizedQuery
          ? item.toLocaleLowerCase().includes(normalizedQuery.toLocaleLowerCase())
          : true,
      ),
    [history, normalizedQuery],
  )

  const liveSuggestions = useMemo(
    () =>
      suggestionData?.query === normalizedQuery
        ? suggestionsFromResults(suggestionData.response, normalizedQuery)
        : [],
    [normalizedQuery, suggestionData],
  )

  const saveSearch = (term: string) => {
    if (!storageKey) return

    const nextHistory = [
      term,
      ...history.filter(
        (item) => item.toLocaleLowerCase() !== term.toLocaleLowerCase(),
      ),
    ].slice(0, 10)

    try {
      localStorage.setItem(storageKey, JSON.stringify(nextHistory))
      setHistory(nextHistory)
      setHistoryError('')
    } catch (error) {
      console.error('Unable to save search history:', error)
      setHistoryError('Search history could not be saved on this device.')
    }
  }

  const submitSearch = (value: string) => {
    const term = value.trim()
    if (term.length < 2) {
      inputRef.current?.focus()
      return
    }

    setQuery(term)
    saveSearch(term)
    setIsOpen(false)
    onSearch(term)
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!event.currentTarget.reportValidity()) return
    submitSearch(query)
  }

  const clearHistory = () => {
    if (!storageKey) return
    try {
      localStorage.removeItem(storageKey)
      setHistory([])
      setHistoryError('')
    } catch (error) {
      console.error('Unable to clear search history:', error)
      setHistoryError('Search history could not be cleared on this device.')
    }
  }

  const showHistory = isOpen && matchingHistory.length > 0
  const showLiveSuggestions = isOpen && normalizedQuery.length >= 2
  return (
    <div className="global-search" ref={containerRef}>
      <form className="global-search-form" role="search" onSubmit={handleSubmit}>
        <label className="global-search-visually-hidden" htmlFor={listId}>
          Search posts, people, Vibes, events, and Hubs
        </label>
        <svg
          className="global-search-icon"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <circle
            cx="10.8"
            cy="10.8"
            r="6.8"
            stroke="currentColor"
            strokeWidth="1.8"
          />
          <path
            d="m16 16 4.5 4.5"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
        <input
          ref={inputRef}
          id={listId}
          type="search"
          value={query}
          minLength={2}
          maxLength={120}
          placeholder="Search posts, people, Vibes, events, Hubs..."
          autoComplete="off"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={isOpen}
          aria-controls={`${listId}-list`}
          onFocus={() => setIsOpen(true)}
          onChange={(event) => {
            setQuery(event.currentTarget.value)
            setIsOpen(true)
            setSuggestionError('')
            setIsSuggesting(false)
          }}
          onKeyDown={(event) => {
            if (event.key === 'Escape') setIsOpen(false)
            if (event.key === 'ArrowDown') {
              const firstOption =
                containerRef.current?.querySelector<HTMLButtonElement>(
                  '.global-search-option',
                )
              if (firstOption) {
                event.preventDefault()
                firstOption.focus()
              }
            }
          }}
        />
        {query && (
          <button
            className="global-search-clear"
            type="button"
            aria-label="Clear search query"
            onClick={() => {
              setQuery('')
              setIsOpen(true)
              inputRef.current?.focus()
            }}
          >
            ×
          </button>
        )}
        <button className="global-search-submit" type="submit">
          Search
        </button>
      </form>

      {isOpen && (
        <div
          className="global-search-dropdown"
          id={`${listId}-list`}
          role="listbox"
          aria-label="Search history and suggestions"
        >
          {showHistory && (
            <section className="global-search-group">
              <div className="global-search-group-heading">
                <h2>Recent searches</h2>
                <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={clearHistory}>
                  Clear
                </button>
              </div>
              {matchingHistory.map((item) => (
                <button
                  className="global-search-option"
                  type="button"
                  role="option"
                  aria-selected="false"
                  key={item}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => submitSearch(item)}
                >
                  <span className="global-search-option-icon" aria-hidden="true">
                    ↻
                  </span>
                  <span>{item}</span>
                </button>
              ))}
            </section>
          )}

          {showLiveSuggestions && (
            <section className="global-search-group">
              <div className="global-search-group-heading">
                <h2>Suggestions</h2>
                {isSuggesting && <span>Searching...</span>}
              </div>
              <button
                className="global-search-option"
                type="button"
                role="option"
                aria-selected="false"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => submitSearch(normalizedQuery)}
              >
                <span className="global-search-option-icon" aria-hidden="true">
                  ⌕
                </span>
                <span>Search all for “{normalizedQuery}”</span>
              </button>
              {liveSuggestions.map((suggestion, index) => (
                <button
                  className="global-search-option"
                  type="button"
                  role="option"
                  aria-selected="false"
                  key={`${suggestion.category}:${suggestion.label}:${index}`}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => submitSearch(suggestion.query)}
                >
                  <span className="global-search-suggestion-type">
                    {suggestion.category}
                  </span>
                  <span className="global-search-suggestion-label">
                    {suggestion.label}
                  </span>
                </button>
              ))}
              {suggestionError && (
                <p className="global-search-message" role="status">
                  {suggestionError}
                </p>
              )}
              {!isSuggesting &&
                !suggestionError &&
                liveSuggestions.length === 0 && (
                  <p className="global-search-message">
                    No matching suggestions yet.
                  </p>
                )}
            </section>
          )}

          {historyError && (
            <p className="global-search-message" role="status">
              {historyError}
            </p>
          )}
          {!showHistory && !showLiveSuggestions && (
            <p className="global-search-message">
              {history.length > 0
                ? 'No recent searches match.'
                : 'Your recent searches will appear here.'}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
