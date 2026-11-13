
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import Sidebar from './Sidebar'
import RightSidebar from './RightSidebar'
import './app-layout.css'

const mobileNavigation = [
  { label: 'Home', path: '/home', icon: 'home', available: true },
  { label: 'Explore', path: '/discover', icon: 'explore', available: false },
  { label: 'Events', path: '/events', icon: 'events', available: false },
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
      {name === 'explore' && (
        <>
          <circle cx="10.5" cy="10.5" r="6.5" />
          <path d="m16 16 5 5" />
        </>
      )}
      {name === 'events' && (
        <>
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <path d="M16 3v4M8 3v4M3 10h18" />
          <path d="M8 14h.01M12 14h.01M16 14h.01M8 17h.01M12 17h.01" />
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
  const navigate = useNavigate()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() =>
    window.matchMedia('(max-width: 850px)').matches,
  )
  const [uploadMenuOpen, setUploadMenuOpen] = useState(false)

  const toggleSidebar = () => {
    setSidebarCollapsed((previous) => !previous)
  }

  useEffect(() => {
    const mobileQuery = window.matchMedia('(max-width: 850px)')
    const handleViewportChange = (event: MediaQueryListEvent) => {
      setSidebarCollapsed(event.matches)
    }

    mobileQuery.addEventListener('change', handleViewportChange)
    return () => mobileQuery.removeEventListener('change', handleViewportChange)
  }, [])

  useEffect(() => {
    if (!uploadMenuOpen) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setUploadMenuOpen(false)
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [uploadMenuOpen])

  const openComposer = (type: 'vibe' | 'moment') => {
    setUploadMenuOpen(false)
    navigate(`/home?compose=${type}`)
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
        <MobileNavigationIcon name={item.icon} />
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
      className={`byb-app-layout${sidebarCollapsed ? ' sidebar-collapsed' : ''}`}
    >
      <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />

      <main className="byb-main-content">
        <Outlet />
      </main>

      <RightSidebar />

      <nav className="byb-mobile-navigation" aria-label="Mobile navigation">
        {mobileNavigation.slice(0, 2).map(renderNavigationItem)}

        <div className="byb-mobile-create">
          <div
            id="byb-mobile-create-options"
            className="byb-mobile-create-options"
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
            aria-controls="byb-mobile-create-options"
            aria-expanded={uploadMenuOpen}
            onClick={() => setUploadMenuOpen((previous) => !previous)}
          >
            <span className="byb-mobile-create-icon" aria-hidden="true">
              +
            </span>
            <span>Create</span>
          </button>
        </div>

        {mobileNavigation.slice(2).map(renderNavigationItem)}
      </nav>
    </div>
  )
}
