
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../../../context/AuthContext'
import {
  profileApi,
  type ProfileStatistics,
} from '../../../services/profileApi'
import VibeSpaceContent from '../components/VibeSpaceContent'
import ProfileConnectionsList from '../components/ProfileConnectionsList'
import ProfileSections from '../components/ProfileSections'
import { resolveProfileSection } from '../components/profileSectionUtils'

import './vibespace.css'

function initials(firstName: string, lastName: string) {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.trim().toUpperCase()
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

function TagCard({
  label,
  title,
  items,
}: {
  label: string
  title: string
  items: string[]
}) {
  return (
    <article className="vibespace-card">
      <div className="vibespace-card-head">
        <span className="vibespace-section-label">{label}</span>
        <h2>{title}</h2>
      </div>

      {items?.length ? (
        <div className="vibespace-tags">
          {items.map((item) => (
            <span className="vibespace-tag" key={`${item}-${label}`}>
              {item}
            </span>
          ))}
        </div>
      ) : (
        <p className="vibespace-empty-note">
          No {title.toLowerCase()} added yet.
        </p>
      )}
    </article>
  )
}

export default function ProfilePage() {
  const { user, profile } = useAuth()
  const { section: sectionParam } = useParams()
  const section = resolveProfileSection(sectionParam)
  const [statistics, setStatistics] = useState<ProfileStatistics | null>(null)
  const [statisticsError, setStatisticsError] = useState('')

  useEffect(() => {
    let active = true
    void profileApi.getMyProfileOverview()
      .then((overview) => {
        if (active) setStatistics(overview.statistics)
      })
      .catch((error: unknown) => {
        console.error('Unable to load profile statistics:', error)
        if (active) setStatisticsError('Unable to load profile statistics.')
      })
    return () => {
      active = false
    }
  }, [])

  if (!profile) {
    return null
  }

  const fullName = `${profile.first_name} ${profile.last_name}`.trim()
  const displayName = fullName || profile.username || user?.username || 'BYB Member'
  const profileInitial = displayName.charAt(0).toUpperCase()
  const isStudent = profile.profile_type === 'student'

  const hasBackgroundInfo =
    Boolean(profile.institution) ||
    Boolean(profile.course) ||
    Boolean(profile.current_organization) ||
    Boolean(profile.job_title)

  const hasOnlinePresence =
    Boolean(profile.linkedin_url) ||
    Boolean(profile.github_url) ||
    Boolean(profile.website_url)

  return (
    <main className="vibespace-page">
      <div className="vibespace-container">
        <header className="vibespace-header">
          <div>
            <span className="vibespace-eyebrow">YOUR SPACE</span>
            <h1>Your VibeSpace</h1>
            <p className="vibespace-header-subtitle">Your profile, interests, and stories in one place.</p>
          </div>

          <div className="vibespace-header-actions">
            <span className="vibespace-visibility">
              {profile.visibility === 'public'
                ? 'Public profile'
                : 'Private profile'}
            </span>

            <Link
              to="/edit-profile"
              className="vibespace-edit-button"
            >
              Edit Profile
            </Link>
          </div>
        </header>

        {/* PROFILE HERO */}

        <section className="vibespace-profile-card" aria-label="Your profile">
          <div className="vibespace-cover">
            {profile.cover_image && (
              <img
                src={profile.cover_image}
                alt=""
                onError={(event) => { event.currentTarget.style.visibility = 'hidden' }}
              />
            )}
            <div className="vibespace-cover-shade" />
            <span className="vibespace-cover-mark" aria-hidden="true">BYB</span>
          </div>
          <div className="vibespace-hero">
          <div className="vibespace-identity">
            <div className="vibespace-avatar">
              {profile.profile_picture ? (
                <img src={profile.profile_picture} alt={`${displayName}'s profile`} />
              ) : (
                <span>{initials(profile.first_name, profile.last_name) || profileInitial}</span>
              )}
            </div>

            <div className="vibespace-identity-details">
              <span className="vibespace-profile-type">
                {isStudent ? 'STUDENT' : 'PROFESSIONAL'}
              </span>

              <h2>{displayName}</h2>

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
          </div>
        </section>

        {/* SECTION TABS */}

        {statisticsError && (
          <p className="profile-list-error" role="alert">{statisticsError}</p>
        )}
        {statistics && (
          <ProfileSections
            basePath="/profile"
            statistics={statistics}
            activeSection={section}
          />
        )}
        {!statistics && !statisticsError && (
          <div className="vibespace-statistics-loading" role="status">
            Loading profile statisticsâ€¦
          </div>
        )}

        {section === 'posts' && (
          <>
        {/* PROFILE DETAIL CARDS (above posts / vibes / moments) */}

        <div className="vibespace-details-heading">
          <div>
            <span className="vibespace-section-label">ABOUT YOU</span>
            <h2>Profile details</h2>
          </div>
          <span>Visible according to your profile privacy</span>
        </div>
        <section className="vibespace-cards" aria-label="Profile details">
          <article className="vibespace-card">
            <div className="vibespace-card-head">
              <span className="vibespace-section-label">IDENTITY</span>
              <h2>Identity</h2>
            </div>

            {isStudent ? (
              <div className="vibespace-info-grid">
                <InfoItem label="Institution" value={profile.institution} />
                <InfoItem label="Course" value={profile.course} />
                <InfoItem
                  label="Field of study"
                  value={profile.field_of_study}
                />
                <InfoItem
                  label="Academic year"
                  value={profile.academic_year}
                />
                <InfoItem
                  label="Graduation year"
                  value={profile.graduation_year}
                />
              </div>
            ) : (
              <div className="vibespace-info-grid">
                <InfoItem
                  label="Organisation"
                  value={profile.current_organization}
                />
                <InfoItem label="Job title" value={profile.job_title} />
                <InfoItem label="Industry" value={profile.industry} />
                <InfoItem
                  label="Experience"
                  value={
                    profile.experience_years !== null
                      ? `${profile.experience_years} years`
                      : null
                  }
                />
              </div>
            )}

            {!hasBackgroundInfo && (
              <p className="vibespace-empty-note">
                Your background information will appear here.
              </p>
            )}
          </article>

          <TagCard
            label="SKILLS"
            title="Skills"
            items={profile.skills || []}
          />

          <article className="vibespace-card">
            <div className="vibespace-card-head">
              <span className="vibespace-section-label">ONLINE PRESENCE</span>
              <h2>Online presence</h2>
            </div>

            <div className="vibespace-links">
              {profile.linkedin_url && (
                <a
                  href={profile.linkedin_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  LinkedIn <span>↗</span>
                </a>
              )}

              {profile.github_url && (
                <a
                  href={profile.github_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  GitHub <span>↗</span>
                </a>
              )}

              {profile.website_url && (
                <a
                  href={profile.website_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Personal website <span>↗</span>
                </a>
              )}

              {!hasOnlinePresence && (
                <p className="vibespace-empty-note">
                  Add your online links to your profile.
                </p>
              )}
            </div>
          </article>

          <TagCard
            label="INTERESTS"
            title="Interests"
            items={profile.interests || []}
          />

        </section>
          </>
        )}

        {/* PROFILE CONTENT */}

        <div className="vibespace-content-body">
          {section !== 'followers' && section !== 'following' && (
            <VibeSpaceContent
              key={user?.username || 'anonymous'}
              username={profile.username || user?.username || ''}
              section={section}
            />
          )}

          {(section === 'followers' || section === 'following') && (
            <ProfileConnectionsList
              key={`${profile.username}:${section}`}
              username={profile.username || user?.username || ''}
              relationship={section}
            />
          )}
        </div>

        {/* FOOTER */}

        <footer className="vibespace-footer">
          <span>BEYOND YOUR BUBBLE</span>
          <span>Your world doesn't end at your bubble.</span>
        </footer>
      </div>
    </main>
  )
}
