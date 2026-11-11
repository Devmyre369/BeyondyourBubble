
import type { ReactNode } from 'react'

interface AuthLayoutProps {
  children: ReactNode
  eyebrow?: string
  title: string
  subtitle: string
}

export default function AuthLayout({
  children,
  eyebrow = 'BEYOND YOUR BUBBLE',
  title,
  subtitle,
}: AuthLayoutProps) {
  return (
    <main className="auth-layout">
      <section className="auth-visual">
        <div className="auth-brand">
          <span className="brand-mark">B</span>
          <span>BYB</span>
        </div>

        <div className="auth-visual-content">
          <span className="auth-visual-eyebrow">
            DISCOVER. CONNECT. EXPERIENCE.
          </span>

          <h1>
            Life happens
            <br />
            <span>beyond</span> your bubble.
          </h1>

          <p>
            Discover experiences, meet people, and become part of
            something happening around you.
          </p>
        </div>

        <div className="auth-visual-footer">
          <span>YOUR WORLD IS BIGGER THAN YOU THINK.</span>
          <span>(C) 2026 BYB</span>
        </div>
      </section>

      <section className="auth-form-section">
        <div className="auth-form-container">
          <div className="auth-mobile-brand">
            <span className="brand-mark">B</span>
            <span>BYB</span>
          </div>

          <div className="auth-heading">
            <span className="auth-eyebrow">{eyebrow}</span>
            <h2>{title}</h2>
            <p>{subtitle}</p>
          </div>

          <div className="auth-form-content">
            {children}
          </div>
        </div>

        <footer className="auth-bottom-footer">
          Made for the world beyond your bubble.
        </footer>
      </section>
    </main>
  )
}


import '../auth.css'
