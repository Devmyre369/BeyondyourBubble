
import { Link } from 'react-router-dom'

import AuthLayout from '../components/AuthLayout'

export default function WelcomePage() {
  return (
    <AuthLayout
      eyebrow="BEYOND YOUR BUBBLE"
      title="Your world is bigger than you think."
      subtitle="Discover events, explore experiences, meet people, and connect with what is happening around you."
    >
      <div className="auth-form">
        <Link
          to="/signup"
          className="auth-submit-button auth-button-link"
        >
          Create Your Account
        </Link>

        <Link
          to="/login"
          className="auth-secondary-button auth-button-link"
        >
          Log In to BYB
        </Link>

        <p className="auth-switch-text">
          Discover. Connect. Experience.
        </p>
      </div>
    </AuthLayout>
  )
}
