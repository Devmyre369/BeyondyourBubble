
import './SplashScreen.css'

export default function SplashScreen() {
  return (
    <div className="byb-splash-screen">
      <div className="byb-splash-brand">
        <img
          src="/images/byb-splash-logo.png"
          alt="BYB logo"
          className="byb-splash-logo"
        />
        <span className="byb-splash-wordmark" aria-hidden="true">BYB</span>
      </div>
    </div>
  )
}
