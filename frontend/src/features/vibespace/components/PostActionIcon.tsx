export type PostActionIconName =
  | 'like'
  | 'comment'
  | 'revibe'
  | 'save'
  | 'share'
  | 'delete'

interface PostActionIconProps {
  name: PostActionIconName
  active?: boolean
}

export default function PostActionIcon({
  name,
  active = false,
}: PostActionIconProps) {
  return (
    <svg
      className="post-action-icon"
      viewBox="0 0 24 24"
      fill={name === 'like' && active ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {name === 'like' && (
        <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.5 1.1-1.1a5.5 5.5 0 0 0-.1-7.8Z" />
      )}
      {name === 'comment' && (
        <path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5 8 8 0 0 1-3.5-.8L4 20l1.2-4.1A7.4 7.4 0 0 1 4 11.5 7.5 7.5 0 0 1 11.5 4H12a7.5 7.5 0 0 1 8 7.5Z" />
      )}
      {name === 'revibe' && (
        <>
          <path d="M17 2l4 4-4 4" />
          <path d="M3 11V9a3 3 0 0 1 3-3h15" />
          <path d="M7 22l-4-4 4-4" />
          <path d="M21 13v2a3 3 0 0 1-3 3H3" />
        </>
      )}
      {name === 'save' && (
        <path d="M6 4.8A1.8 1.8 0 0 1 7.8 3h8.4A1.8 1.8 0 0 1 18 4.8V21l-6-4-6 4V4.8Z" />
      )}
      {name === 'share' && (
        <>
          <path d="M12 16V3" />
          <path d="m7 8 5-5 5 5" />
          <path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7" />
        </>
      )}
      {name === 'delete' && (
        <>
          <path d="M3 6h18" />
          <path d="M8 6V4h8v2" />
          <path d="m19 6-1 14H6L5 6" />
          <path d="M10 11v5M14 11v5" />
        </>
      )}
    </svg>
  )
}
