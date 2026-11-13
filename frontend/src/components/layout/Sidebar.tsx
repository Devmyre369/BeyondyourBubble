
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const navigationItems = [
  { label: 'Home', path: '/home', icon: '⌂', available: true },
  { label: 'Discover', path: '/discover', icon: '⌕', available: false },
  { label: 'Events', path: '/events', icon: '▦', available: false },
  { label: 'Hubs', path: '/hubs', icon: '◈', available: false },
  { label: 'Saved', path: '/saved', icon: '♡', available: false },
]

export default function Sidebar() {
  const { user, profile, logout } = useAuth()
  const navigate = useNavigate()

  const displayName = profile
    ? `${profile.first_name} ${profile.last_name}`.trim()
    : user?.username || 'BYB Member'

  const username = profile?.username || user?.username || ''

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <aside className="byb-sidebar">
      <NavLink to="/home" className="byb-brand">
        <span className="byb-brand-mark">B</span>
        <span className="byb-brand-name">BYB<span>.</span></span>
      </NavLink>

      <div className="byb-sidebar-section">
        <span className="byb-sidebar-label">MENU</span>

        <nav className="byb-navigation" aria-label="Main navigation">
          {navigationItems.map((item) =>
            item.available ? (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `byb-nav-item${isActive ? ' active' : ''}`
                }
              >
                <span className="byb-nav-icon" aria-hidden="true">
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </NavLink>
            ) : (
              <div
                key={item.path}
                className="byb-nav-item disabled"
                aria-disabled="true"
                title="Coming soon"
              >
                <span className="byb-nav-icon" aria-hidden="true">
                  {item.icon}
                </span>
                <span>{item.label}</span>
                <span className="byb-nav-soon">Soon</span>
              </div>
            )
          )}
        </nav>
      </div>

      <div className="byb-sidebar-bottom">
        <span className="byb-sidebar-label">YOUR SPACE</span>

        <NavLink
          to="/profile"
          className={({ isActive }) =>
            `byb-profile-link${isActive ? ' active' : ''}`
          }
        >
          {profile?.profile_picture ? (
            <img
              src={profile.profile_picture}
              alt=""
              className="byb-sidebar-avatar"
            />
          ) : (
            <span className="byb-sidebar-avatar byb-sidebar-avatar-placeholder">
              {displayName.charAt(0).toUpperCase()}
            </span>
          )}

          <span className="byb-sidebar-user-info">
            <strong>{displayName}</strong>
            <span>@{username}</span>
          </span>
        </NavLink>

        <button
          type="button"
          className="byb-logout-button"
          onClick={handleLogout}
        >
          <span aria-hidden="true">↗</span>
          <span>Log out</span>
        </button>
      </div>
    </aside>
  )
}
