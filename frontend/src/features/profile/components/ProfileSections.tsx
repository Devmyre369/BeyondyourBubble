import { Link } from 'react-router-dom'

import type { ProfileStatistics } from '../../../services/profileApi'
import type { ProfileSection } from './profileSectionUtils'

const sections: { key: ProfileSection; label: string }[] = [
  { key: 'posts', label: 'Posts' },
  { key: 'vibes', label: 'Vibes' },
  { key: 'moments', label: 'Moments' },
  { key: 'followers', label: 'Followers' },
  { key: 'following', label: 'Following' },
]

export default function ProfileSections({
  basePath,
  statistics,
  activeSection,
}: {
  basePath: string
  statistics: ProfileStatistics
  activeSection: ProfileSection
}) {
  const counts: Record<ProfileSection, number> = {
    posts: statistics.posts_count,
    vibes: statistics.vibes_count,
    moments: statistics.moments_count,
    followers: statistics.followers_count,
    following: statistics.following_count,
  }

  return (
    <nav className="profile-section-tabs" aria-label="Profile sections">
      {sections.map(({ key, label }) => (
        <Link
          key={key}
          to={`${basePath}/${key}`}
          className={activeSection === key ? 'active' : ''}
        >
          {label}
          <span>{counts[key]}</span>
        </Link>
      ))}
    </nav>
  )
}
