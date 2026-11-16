export type ProfileSection =
  | 'posts'
  | 'vibes'
  | 'moments'
  | 'followers'
  | 'following'

const sectionKeys: ProfileSection[] = [
  'posts',
  'vibes',
  'moments',
  'followers',
  'following',
]

export function resolveProfileSection(
  value: string | undefined,
): ProfileSection {
  return sectionKeys.includes(value as ProfileSection)
    ? value as ProfileSection
    : 'posts'
}
