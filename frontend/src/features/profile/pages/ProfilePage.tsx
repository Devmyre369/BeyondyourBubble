import { useAuth } from '../../../context/AuthContext'
import './vibespace.css'

import './vibespace.css'

function initials(firstName: string, lastName: string) {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase()
}

function InfoItem({
  label,
  value,
}: {
  label: string
  value: string | number | null | undefined
}) {
  if (value === null || value === undefined || value === '') {
    return null
  }

  return (
    <div className="vibespace-info-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function TagList({
  title,
  items,
}: {
  title: string
  items: string[]
}) {
  if (!items?.length) return null

  return (
    <section className="vibespace-card">
      <h2>{title}</h2>
      <div className="vibespace-tags">
        {items.map((item) => (
          <span className="vibespace-tag" key={item}>
            {item}
          </span>
        ))}
      </div>
    </section>
  )
}

export default function ProfilePage() {
  const { user, profile } = useAuth()

  if (!profile) {
    return null
  }

  const fullName = `${profile.first_name} ${profile.last_name}`.trim()

  const isStudent = profile.profile_type === 'student'

  return (
    <main className="vibespace-page">
      <div className="vibespace-container">
        <header className="vibespace-header">
          <div>
            <span className="vibespace-eyebrow">BEYOND YOUR BUBBLE</span>
            <h1>Your VibeSpace</h1>
          </div>

          <span className="vibespace-visibility">
            {profile.visibility === 'public' ? 'Public profile' : 'Private profile'}
          </span>
        </header>

        <section className="vibespace-hero">
          <div className="vibespace-cover">
            {profile.cover_image ? (
              <img src={profile.cover_image} alt={`${fullName}'s cover`} />
            ) : (
              <div className="vibespace-cover-placeholder">
                <span>YOUR WORLD. YOUR EXPERIENCES.</span>
              </div>
            )}
          </div>

          <div className="vibespace-identity">
            <div className="vibespace-avatar">
              {profile.profile_picture ? (
                <img src={profile.profile_picture} alt={fullName} />
              ) : (
                <span>{initials(profile.first_name, profile.last_name)}</span>
              )}
            </div>

            <div className="vibespace-identity-details">
              <span className="vibespace-profile-type">
                {isStudent ? 'STUDENT' : 'PROFESSIONAL'}
              </span>

              <h2>{fullName}</h2>

              <p className="vibespace-username">
                @{profile.username || user?.username}
              </p>

              {profile.byb_signature && (
                <p className="vibespace-signature">
                  {profile.byb_signature}
                </p>
              )}
            </div>
          </div>

          {profile.bio && (
            <p className="vibespace-bio">{profile.bio}</p>
          )}

          {profile.city && (
            <p className="vibespace-location">
              <span aria-hidden="true">⌖</span>
              {profile.city}
            </p>
          )}
        </section>

        <div className="vibespace-content-grid">
          <div className="vibespace-main-column">
            <section className="vibespace-card">
              <div className="vibespace-section-heading">
                <div>
                  <span className="vibespace-section-label">01 / IDENTITY</span>
                  <h2>About me</h2>
                </div>
              </div>

              {isStudent ? (
                <div className="vibespace-info-grid">
                  <InfoItem label="Institution" value={profile.institution} />
                  <InfoItem label="Course" value={profile.course} />
                  <InfoItem label="Field of study" value={profile.field_of_study} />
                  <InfoItem label="Academic year" value={profile.academic_year} />
                  <InfoItem label="Graduation year" value={profile.graduation_year} />
                </div>
              ) : (
                <div className="vibespace-info-grid">
                  <InfoItem label="Organisation" value={profile.current_organization} />
                  <InfoItem label="Job title" value={profile.job_title} />
                  <InfoItem label="Industry" value={profile.industry} />
                  <InfoItem label="Experience" value={
                    profile.experience_years !== null
                      ? `${profile.experience_years} years`
                      : null
                  } />
                </div>
              )}

              {!profile.institution &&
                !profile.course &&
                !profile.current_organization &&
                !profile.job_title && (
                  <p className="vibespace-empty-note">
                    Your background information will appear here.
                  </p>
                )}
            </section>

            <section className="vibespace-card vibespace-experiences">
              <div className="vibespace-section-heading">
                <div>
                  <span className="vibespace-section-label">02 / EXPERIENCES</span>
                  <h2>Your Vibes</h2>
                </div>
              </div>

              <div className="vibespace-empty-state">
                <span className="vibespace-empty-icon">✳</span>
                <h3>Your experiences deserve to be heard.</h3>
                <p>
                  Event-related Vibes you share will appear here.
                  Connect your thoughts and experiences to the real
                  events that inspire them.
                </p>
                <span className="vibespace-coming-soon">VIBE POSTING — COMING SOON</span>
              </div>
            </section>

            <section className="vibespace-card vibespace-experiences">
              <div className="vibespace-section-heading">
                <div>
                  <span className="vibespace-section-label">03 / MOMENTS</span>
                  <h2>Captured moments</h2>
                </div>
              </div>

              <div className="vibespace-empty-state">
                <span className="vibespace-empty-icon">▧</span>
                <h3>Every event has a story.</h3>
                <p>
                  Your event-related photo Moments will live here,
                  helping others experience what happened even
                  when they couldn't attend.
                </p>
                <span className="vibespace-coming-soon">MOMENTS — COMING SOON</span>
              </div>
            </section>
          </div>

          <aside className="vibespace-sidebar">
            <TagList title="Interests" items={profile.interests || []} />
            <TagList title="Skills" items={profile.skills || []} />

            <section className="vibespace-card">
              <h2>Online presence</h2>

              <div className="vibespace-links">
                {profile.linkedin_url && (
                  <a href={profile.linkedin_url} target="_blank" rel="noreferrer">
                    LinkedIn <span>↗</span>
                  </a>
                )}

                {profile.github_url && (
                  <a href={profile.github_url} target="_blank" rel="noreferrer">
                    GitHub <span>↗</span>
                  </a>
                )}

                {profile.website_url && (
                  <a href={profile.website_url} target="_blank" rel="noreferrer">
                    Personal website <span>↗</span>
                  </a>
                )}

                {!profile.linkedin_url &&
                  !profile.github_url &&
                  !profile.website_url && (
                    <p className="vibespace-empty-note">
                      Add your online links to your profile.
                    </p>
                  )}
              </div>
            </section>

            <section className="vibespace-card vibespace-philosophy">
              <span>THE BYB IDEA</span>
              <p>
                You don't have to be physically present to be
                part of an experience.
              </p>
            </section>
          </aside>
        </div>

        <footer className="vibespace-footer">
          <span>BEYOND YOUR BUBBLE</span>
          <span>Your world doesn't end at your bubble.</span>
        </footer>
      </div>
    </main>
  )
}
