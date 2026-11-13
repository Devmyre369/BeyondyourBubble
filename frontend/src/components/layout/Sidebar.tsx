
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

type SidebarProps = {
  collapsed: boolean
  onToggle: () => void
}

const navigationItems = [
  { label: 'Home', path: '/home', icon: '\u2302', available: true },
  { label: 'Discover', path: '/discover', icon: '\u2315', available: false },
  { label: 'Events', path: '/events', icon: '\u25A6', available: false },
  { label: 'Hubs', path: '/hubs', icon: '\u25C8', available: false },
  { label: 'Saved', path: '/saved', icon: '\u2661', available: false },
]

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
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
    <aside className={`byb-sidebar${collapsed ? ' collapsed' : ''}`}>
      <div className="byb-sidebar-top">
        <NavLink to="/home" className="byb-brand" title="BYB Home">
          <span className="byb-brand-mark">B</span>
          <span className="byb-brand-name">
            BYB<span>.</span>
          </span>
        </NavLink>

        <button
          type="button"
          className="byb-sidebar-toggle"
          onClick={onToggle}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-expanded={!collapsed}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? '\u00BB' : '\u00AB'}
        </button>
      </div>

      <div className="byb-sidebar-scroll">
        <div className="byb-sidebar-section">
          <span className="byb-sidebar-label">MENU</span>

          <nav className="byb-navigation" aria-label="Main navigation">
            {navigationItems.map((item) =>
              item.available ? (
                <NavLink
                  key={item.path}
                  to={item.path}
                  title={collapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    `byb-nav-item${isActive ? ' active' : ''}`
                  }
                >
                  <span className="byb-nav-icon" aria-hidden="true">
                    {item.icon}
                  </span>
                  <span className="byb-nav-text">{item.label}</span>
                </NavLink>
              ) : (
                <div
                  key={item.path}
                  className="byb-nav-item disabled"
                  aria-disabled="true"
                  title={`${item.label} — Coming soon`}
                >
                  <span className="byb-nav-icon" aria-hidden="true">
                    {item.icon}
                  </span>
                  <span className="byb-nav-text">{item.label}</span>
                  <span className="byb-nav-soon">Soon</span>
                </div>
              )
            )}
          </nav>
        </div>
      </div>

      <div className="byb-sidebar-bottom">
        <span className="byb-sidebar-label">YOUR SPACE</span>

        <NavLink
          to="/profile"
          title={collapsed ? displayName : undefined}
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
          title={collapsed ? 'Log out' : undefined}
        >
          <span aria-hidden="true">{'\u2197'}</span>
          <span className="byb-logout-text">Log out</span>
        </button>
      </div>
    </aside>
  )
}
