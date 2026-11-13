import { NavLink, Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import RightSidebar from './RightSidebar'
import './app-layout.css'

const mobileNavigation = [
  { label: 'Home', path: '/home', icon: '\u2302' },
  { label: 'Discover', path: '/discover', icon: '\u2315' },
  { label: 'Events', path: '/events', icon: '\u25A6' },
  { label: 'Profile', path: '/profile', icon: '\u25CB' },
]

export default function AppLayout() {
  return (
    <div className="byb-app-layout">
      <Sidebar />

      <main className="byb-main-content">
        <Outlet />
      </main>

      <RightSidebar />

      <nav className="byb-mobile-navigation" aria-label="Mobile navigation">
        {mobileNavigation.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `byb-mobile-nav-item${isActive ? ' active' : ''}`
            }
          >
            <span aria-hidden="true">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
