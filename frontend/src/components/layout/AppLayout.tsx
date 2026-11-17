
import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { notificationsApi } from '../../services/notificationsApi'
import GlobalSearchBox from '../../features/search/GlobalSearchBox'
import Sidebar from './Sidebar'
import RightSidebar from './RightSidebar'
import './app-layout.css'

const mobileNavigation = [
  { label: 'Home', path: '/home', icon: 'home', available: true },
  { label: 'Events', path: '/events', icon: 'events', available: true },
  { label: 'Hubs', path: '/hubs', icon: 'hubs', available: true },
  { label: 'Profile', path: '/profile', icon: 'profile', available: true },
] as const

type MobileNavigationIconName =
  (typeof mobileNavigation)[number]['icon']

function MobileNavigationIcon({
  name,
}: {
  name: MobileNavigationIconName
}) {
  return (
    <svg
      className="byb-mobile-nav-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {name === 'home' && (
        <>
          <path d="m3 10 9-7 9 7" />
          <path d="M5 9v12h14V9" />
          <path d="M9 21v-7h6v7" />
        </>
      )}
      {name === 'events' && (
        <>
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <path d="M16 3v4M8 3v4M3 10h18" />
          <path d="M8 14h.01M12 14h.01M16 14h.01M8 17h.01M12 17h.01" />
        </>
      )}
      {name === 'hubs' && (
        <>
          <path d="m12 3.5 6.5 3.75v7.5L12 18.5l-6.5-3.75v-7.5L12 3.5Z" />
          <circle cx="12" cy="10" r="1.5" />
          <path d="M12 11.5v3.5m-1.3-2.8-2.4 1.4m5.4-1.4 2.4 1.4" />
        </>
      )}
      {name === 'profile' && (
        <>
          <circle cx="12" cy="8" r="3.5" />
          <path d="M5 21c.7-3.7 3.2-5.5 7-5.5s6.3 1.8 7 5.5" />
        </>
      )}
    </svg>
  )
}

export default function AppLayout() {
  const { profile } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [isMobile, setIsMobile] = useState(() =>
    window.matchMedia('(max-width: 850px)').matches,
  )
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() =>
    window.matchMedia('(max-width: 850px)').matches,
  )
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const [uploadMenuOpen, setUploadMenuOpen] = useState(false)
  const [unreadNotifications, setUnreadNotifications] = useState(0)
  const mobileMenuButtonRef = useRef<HTMLButtonElement>(null)

  const toggleSidebar = () => {
    setSidebarCollapsed((previous) => !previous)
  }

  useEffect(() => {
    const mobileQuery = window.matchMedia('(max-width: 850px)')
    const handleViewportChange = (event: MediaQueryListEvent) => {
      setIsMobile(event.matches)
      setSidebarCollapsed(event.matches)
      setMobileSidebarOpen(false)
    }

    mobileQuery.addEventListener('change', handleViewportChange)
    return () => mobileQuery.removeEventListener('change', handleViewportChange)
  }, [])

  useEffect(() => {
    if (!mobileSidebarOpen) return

    const previousBodyOverflow = document.body.style.overflow
    const menuButton = mobileMenuButtonRef.current
    document.body.style.overflow = 'hidden'
    const focusFrame = window.requestAnimationFrame(() => {
      document
        .querySelector<HTMLElement>('#byb-main-sidebar .byb-sidebar-toggle')
        ?.focus()
    })
    const handleSidebarKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMobileSidebarOpen(false)
        return
      }
      if (event.key !== 'Tab') return

      const sidebar = document.getElementById('byb-main-sidebar')
      if (!sidebar) return
      const focusableElements = Array.from(
        sidebar.querySelectorAll<HTMLElement>(
          'a[href], button:not(:disabled), [tabindex]:not([tabindex="-1"])',
        ),
      ).filter((element) => element.offsetParent !== null)
      const firstElement = focusableElements[0]
      const lastElement = focusableElements[focusableElements.length - 1]
      if (!firstElement || !lastElement) return

      if (!sidebar.contains(document.activeElement)) {
        event.preventDefault()
        firstElement.focus()
      } else if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault()
        lastElement.focus()
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault()
        firstElement.focus()
      }
    }
    window.addEventListener('keydown', handleSidebarKeyDown)

    return () => {
      window.removeEventListener('keydown', handleSidebarKeyDown)
      window.cancelAnimationFrame(focusFrame)
      document.body.style.overflow = previousBodyOverflow
      if (menuButton?.isConnected) menuButton.focus()
    }
  }, [mobileSidebarOpen])

  useEffect(() => {
    if (!uploadMenuOpen) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setUploadMenuOpen(false)
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [uploadMenuOpen])

  useEffect(() => {
    const refreshUnreadCount = () => {
      notificationsApi.getUnreadCount()
        .then(setUnreadNotifications)
        .catch((requestError: unknown) => {
          console.error('Unable to load notification count:', requestError)
        })
    }

    refreshUnreadCount()
    const intervalId = window.setInterval(refreshUnreadCount, 60_000)
    window.addEventListener('byb:notifications-updated', refreshUnreadCount)

    return () => {
      window.clearInterval(intervalId)
      window.removeEventListener('byb:notifications-updated', refreshUnreadCount)
    }
  }, [location.pathname])

  const openComposer = (type: 'vibe' | 'moment') => {
    setUploadMenuOpen(false)
    navigate(`/create/${type}`)
  }

  const searchQuery =
    location.pathname === '/search'
      ? new URLSearchParams(location.search).get('q') || ''
      : ''

  const handleGlobalSearch = (query: string) => {
    const params = new URLSearchParams({
      q: query,
      category: 'all',
      page: '1',
    })
    navigate(`/search?${params.toString()}`)
  }

  const renderNavigationItem = (
    item: (typeof mobileNavigation)[number],
  ) =>
    item.available ? (
      <NavLink
        key={item.path}
        to={item.path}
        className={({ isActive }) =>
          `byb-mobile-nav-item${isActive ? ' active' : ''}`
        }
      >
        {item.icon === 'profile' && profile?.profile_picture ? (
          <img
            className="byb-mobile-profile-avatar"
            src={profile.profile_picture}
            alt=""
          />
        ) : (
          <MobileNavigationIcon name={item.icon} />
        )}
        <span>{item.label}</span>
      </NavLink>
    ) : (
      <button
        key={item.path}
        type="button"
        className="byb-mobile-nav-item disabled"
        title={`${item.label} — Coming soon`}
        aria-label={`${item.label}, coming soon`}
        disabled
      >
        <MobileNavigationIcon name={item.icon} />
        <span>{item.label}</span>
      </button>
    )

  return (
    <div
      className={`byb-app-layout${sidebarCollapsed ? ' sidebar-collapsed' : ''}${mobileSidebarOpen ? ' mobile-sidebar-open' : ''}`}
    >
      {mobileSidebarOpen && (
        <button
          type="button"
          className="byb-mobile-sidebar-backdrop"
          aria-label="Close navigation menu"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}
      <Sidebar
        collapsed={!isMobile && sidebarCollapsed}
        mobile={isMobile}
        mobileOpen={mobileSidebarOpen}
        onToggle={() => {
          if (isMobile) setMobileSidebarOpen(false)
          else toggleSidebar()
        }}
        onNavigate={() => {
          if (isMobile) setMobileSidebarOpen(false)
        }}
      />

      <main className="byb-main-content">
        <header className="byb-create-toolbar">
          {isMobile ? (
            <button
              ref={mobileMenuButtonRef}
              type="button"
              className="byb-mobile-menu-button"
              aria-label={mobileSidebarOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-controls="byb-main-sidebar"
              aria-expanded={mobileSidebarOpen}
              onClick={() => {
                setUploadMenuOpen(false)
                setMobileSidebarOpen((previous) => !previous)
              }}
            >
              <span aria-hidden="true" />
              <span aria-hidden="true" />
              <span aria-hidden="true" />
            </button>
          ) : (
            <span
              className="byb-header-spacer byb-header-spacer-left"
              aria-hidden="true"
            />
          )}

          <NavLink
            to="/home"
            className="byb-header-brand"
            aria-label="BYB Home"
          >
            <span className="byb-brand-mark">B</span>
            <span className="byb-brand-name">
              BYB<span>.</span>
            </span>
          </NavLink>

          <NavLink
            to="/notifications"
            className={({ isActive }) =>
              `byb-header-notifications${isActive ? ' active' : ''}`
            }
            aria-label={`Notifications${unreadNotifications ? `, ${unreadNotifications} unread` : ''}`}
            title="Notifications"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <path d="M20.8 8.8c0 5.2-8.8 11-8.8 11s-8.8-5.8-8.8-11A4.8 4.8 0 0 1 12 6.1a4.8 4.8 0 0 1 8.8 2.7Z" />
            </svg>
            {unreadNotifications > 0 && (
              <span className="byb-notification-badge">
                {unreadNotifications > 99 ? '99+' : unreadNotifications}
              </span>
            )}
          </NavLink>

          <div className="byb-global-search-slot">
            <GlobalSearchBox
              key={location.pathname === '/search' ? `search:${searchQuery}` : 'global-search'}
              initialQuery={searchQuery}
              onSearch={handleGlobalSearch}
            />
          </div>
        </header>
        <Outlet />
      </main>

      <RightSidebar />

      <nav className="byb-mobile-navigation" aria-label="Mobile navigation">
        {mobileNavigation.slice(0, 2).map(renderNavigationItem)}
        <div className="byb-mobile-create-nav-item">
          <div className="byb-create-menu">
            <div
              id="byb-create-options"
              className="byb-create-options"
              aria-label="Upload options"
              hidden={!uploadMenuOpen}
            >
              <button type="button" onClick={() => openComposer('vibe')}>
                Upload a vibe
              </button>
              <button type="button" onClick={() => openComposer('moment')}>
                Upload a moment
              </button>
            </div>
            <button
              type="button"
              className={`byb-mobile-nav-item byb-mobile-create-button${uploadMenuOpen ? ' active' : ''}`}
              aria-label="Create a vibe or moment"
              aria-controls="byb-create-options"
              aria-expanded={uploadMenuOpen}
              onClick={() => setUploadMenuOpen((previous) => !previous)}
            >
              <span className="byb-mobile-create-icon" aria-hidden="true">+</span>
              <span>Create</span>
            </button>
          </div>
        </div>
        {mobileNavigation.slice(2).map(renderNavigationItem)}
      </nav>
    </div>
  )
}
