
import { Link } from 'react-router-dom'

export default function RightSidebar() {
  return (
    <aside className="byb-right-sidebar">
      <section className="byb-context-card byb-intro-card">
        <span className="byb-context-eyebrow">BEYOND YOUR BUBBLE</span>
        <h2>There's more happening out there.</h2>
        <p>
          Discover real-world experiences, explore communities, and stay
          connected to moments beyond your everyday circle.
        </p>
        <Link to="/home" className="byb-context-link">
          Explore your feed <span aria-hidden="true">{'\u2192'}</span>
        </Link>
      </section>

      <section className="byb-context-card">
        <span className="byb-context-eyebrow">YOUR BYB SPACE</span>
        <h3>Stay connected</h3>
        <p>
          Your VibeSpace is where your experiences, thoughts, and event
          moments come together.
        </p>
        <Link to="/profile" className="byb-context-link">
          Visit your profile <span aria-hidden="true">{'\u2192'}</span>
        </Link>
      </section>

      <section className="byb-context-footer">
        <span>BYB. Beyond Your Bubble</span>
        <p>Discover more. Experience more. Connect beyond.</p>
      </section>
    </aside>
  )
}
