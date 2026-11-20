import axios from 'axios'
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

import {
  notificationsApi,
  type NotificationItem,
} from '../../services/notificationsApi'
import './notifications.css'

const notificationMessages: Record<NotificationItem['verb'], string> = {
  like: 'liked your post',
  comment: 'commented on your post',
  save: 'saved your post',
  share: 'shared your post',
  follow: 'started following you',
  revibe: 'revibed your post',
  handshake_request: 'sent you a Handshake request',
  handshake_accepted: 'accepted your Handshake request',
  event_approved: 'approved your event',
  event_rejected: 'requested changes to your event',
  event_submitted: 'submitted an event for review',
  event_updated: 'updated a Hub event',
  event_cancelled: 'cancelled a Hub event',
  hub_application_submitted: 'submitted a Hub application for review',
  hub_application_approved: 'approved your Hub application',
  hub_application_rejected: 'rejected your Hub application',
  hub_membership_request: 'requested to join your Hub',
  hub_member_joined: 'joined your Hub',
  hub_member_left: 'left your Hub',
  hub_membership_approved: 'approved your Hub membership',
  hub_membership_rejected: 'declined your Hub membership request',
  hub_invited: 'added you to a Hub',
  hub_member_removed: 'removed you from a Hub',
  hub_role_changed: 'changed your Hub role',
  hub_verification_requested: 'requested Hub verification',
  hub_verification_approved: 'verified your Hub',
  hub_verification_rejected: 'declined your Hub verification request',
}

function getNotificationPath(notification: NotificationItem, isStaff: boolean) {
  if (notification.verb === 'handshake_request' || notification.verb === 'handshake_accepted') {
    return '/handshakes'
  }
  if (notification.verb === 'follow') {
    return `/users/${encodeURIComponent(notification.actor_username)}`
  }
  if (notification.vibe_id || notification.moment_id) {
    const type = notification.vibe_id ? 'vibe' : 'moment'
    const id = notification.vibe_id || notification.moment_id
    if (notification.content_author_username && id) {
      return `/users/${encodeURIComponent(notification.content_author_username)}/posts#${type}-${id}`
    }
    return '/home'
  }
  if (notification.verb === 'event_submitted') {
    return isStaff ? '/staff/events/moderation' : notification.hub_id ? `/hubs/${notification.hub_id}` : '/events'
  }
  if (notification.verb === 'hub_application_submitted') {
    return isStaff ? '/staff/hubs/review' : '/hubs/applications'
  }
  if (notification.verb === 'hub_verification_requested') {
    return isStaff ? '/staff/hubs/review' : notification.hub_id ? `/hubs/${notification.hub_id}` : '/hubs'
  }
  if (notification.verb === 'event_approved' && notification.event_id) {
    return `/events/${encodeURIComponent(notification.event_id)}`
  }
  if (notification.verb === 'event_updated' && notification.event_id) {
    return `/events/${encodeURIComponent(notification.event_id)}`
  }
  if (notification.verb === 'hub_application_approved' && notification.hub_id) {
    return `/hubs/${encodeURIComponent(notification.hub_id)}`
  }
  if (notification.hub_id) {
    return `/hubs/${encodeURIComponent(notification.hub_id)}`
  }
  if (notification.verb === 'hub_application_approved' || notification.verb === 'hub_application_rejected') {
    return '/hubs/applications'
  }
  if (notification.verb.startsWith('event_')) return '/events'
  return `/users/${encodeURIComponent(notification.actor_username)}`
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [nextPage, setNextPage] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [markingAllRead, setMarkingAllRead] = useState(false)
  const [reload, setReload] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    notificationsApi.getNotifications()
      .then((page) => {
        if (!active) return
        setNotifications(page.results)
        setUnreadCount(page.unread_count)
        setNextPage(page.next)
      })
      .catch((requestError: unknown) => {
        if (!active) return
        if (axios.isCancel(requestError)) return
        console.error('Unable to load notifications:', requestError)
        setError('Notifications could not be loaded. Please try again.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reload])

  const retryLoad = () => {
    setLoading(true)
    setError('')
    setReload((value) => value + 1)
  }

  const markAllRead = async () => {
    if (markingAllRead) return
    setError('')
    setMarkingAllRead(true)
    try {
      await notificationsApi.markAllRead()
      setUnreadCount(0)
      window.dispatchEvent(new Event('byb:notifications-updated'))
      setNotifications((current) =>
        current.map((notification) => ({
          ...notification,
          read_at: notification.read_at || new Date().toISOString(),
        })),
      )
    } catch (requestError) {
      if (!axios.isCancel(requestError)) {
        console.error('Unable to mark notifications as read:', requestError)
        setError('Notifications could not be marked as read. Please try again.')
      }
    } finally {
      setMarkingAllRead(false)
    }
  }

  const openNotification = async (notification: NotificationItem) => {
    if (notification.read_at) return true

    setError('')
    try {
      await notificationsApi.markRead(notification.id)
      window.dispatchEvent(new Event('byb:notifications-updated'))
      setNotifications((current) =>
        current.map((item) =>
          item.id === notification.id
            ? { ...item, read_at: new Date().toISOString() }
            : item,
        ),
      )
      setUnreadCount((current) => Math.max(0, current - 1))
      return true
    } catch (requestError) {
      if (!axios.isCancel(requestError)) {
        console.error('Unable to mark notification as read:', requestError)
        setError('This notification could not be marked as read.')
      }
      return false
    }
  }

  const loadMore = async () => {
    if (nextPage === null || loadingMore) return

    setError('')
    setLoadingMore(true)
    try {
      const page = await notificationsApi.getNotifications(nextPage)
      setNotifications((current) => {
        const seen = new Set(current.map((item) => item.id))
        return [...current, ...page.results.filter((item) => !seen.has(item.id))]
      })
      setNextPage(page.next)
    } catch (requestError) {
      if (!axios.isCancel(requestError)) {
        console.error('Unable to load more notifications:', requestError)
        setError('More notifications could not be loaded. Please try again.')
      }
    } finally {
      setLoadingMore(false)
    }
  }

  return (
    <section className="byb-notifications-page" aria-labelledby="notifications-title">
      <header className="byb-notifications-header">
        <div>
          <span className="byb-notifications-eyebrow">YOUR UPDATES</span>
          <h1 id="notifications-title">Notifications</h1>
          <p>Keep up with the people and posts around you.</p>
        </div>
        {unreadCount > 0 && (
          <button type="button" disabled={markingAllRead} onClick={() => void markAllRead()}>
            {markingAllRead ? 'Marking…' : 'Mark all as read'}
          </button>
        )}
      </header>

      {error && notifications.length > 0 && <p className="byb-notifications-error" role="alert">{error}</p>}

      {loading ? (
        <p className="byb-notifications-state" role="status">Loading notifications…</p>
      ) : error && notifications.length === 0 ? (
        <div className="byb-notifications-error-state" role="alert">
          <p>{error}</p>
          <button type="button" onClick={retryLoad}>Try again</button>
        </div>
      ) : notifications.length === 0 ? (
        <div className="byb-notifications-empty">
          <span aria-hidden="true">♡</span>
          <h2>You’re all caught up</h2>
          <p>New updates from Events, Hubs, Handshake, VibeSpace, and Feed will show up here.</p>
        </div>
      ) : (
        <div className="byb-notifications-list">
          {notifications.map((notification) => {
            const displayName =
              `${notification.actor_first_name} ${notification.actor_last_name}`.trim() ||
              notification.actor_username

            return (
              <Link
                key={notification.id}
                to={getNotificationPath(notification, Boolean(user?.is_staff))}
                className={`byb-notification${notification.read_at ? '' : ' unread'}`}
                onClick={(event) => {
                  if (notification.read_at) return
                  event.preventDefault()
                  void openNotification(notification).then((opened) => {
                    if (opened) navigate(getNotificationPath(notification, Boolean(user?.is_staff)))
                  })
                }}
              >
                {notification.actor_profile_picture ? (
                  <img src={notification.actor_profile_picture} alt="" />
                ) : (
                  <span className="byb-notification-avatar" aria-hidden="true">
                    {displayName.charAt(0).toUpperCase()}
                  </span>
                )}
                <span className="byb-notification-copy">
                  <span>
                    <strong>{displayName}</strong> {notificationMessages[notification.verb]}
                    {notification.event_title && (
                      <span> · {notification.event_title}</span>
                    )}
                    {notification.hub_name && (
                      <span> · {notification.hub_name}</span>
                    )}
                    {notification.verb === 'handshake_request' && notification.handshake_status && notification.handshake_status !== 'pending' && (
                      <span className="byb-notification-handshake-status"> ({notification.handshake_status})</span>
                    )}
                  </span>
                  <time dateTime={notification.created_at}>
                    {new Intl.DateTimeFormat(undefined, {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    }).format(new Date(notification.created_at))}
                  </time>
                </span>
                {!notification.read_at && (
                  <span className="byb-notification-unread-dot" aria-label="Unread" />
                )}
              </Link>
            )
          })}
        </div>
      )}
      {!loading && nextPage !== null && (
        <button
          type="button"
          className="byb-notifications-load-more"
          disabled={loadingMore}
          onClick={() => void loadMore()}
        >
          {loadingMore ? 'Loading…' : 'Load more'}
        </button>
      )}
    </section>
  )
}
