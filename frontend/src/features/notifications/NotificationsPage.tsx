import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

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
}

function getNotificationPath(notification: NotificationItem) {
  return notification.verb === 'follow'
    ? `/users/${encodeURIComponent(notification.actor_username)}`
    : '/profile'
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [nextPage, setNextPage] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
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
        console.error('Unable to load notifications:', requestError)
        setError('Notifications could not be loaded. Please try again.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  const markAllRead = async () => {
    setError('')
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
      console.error('Unable to mark notifications as read:', requestError)
      setError('Notifications could not be marked as read. Please try again.')
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
      console.error('Unable to mark notification as read:', requestError)
      setError('This notification could not be marked as read.')
      return false
    }
  }

  const loadMore = async () => {
    if (nextPage === null) return

    setError('')
    try {
      const page = await notificationsApi.getNotifications(nextPage)
      setNotifications((current) => [...current, ...page.results])
      setNextPage(page.next)
    } catch (requestError) {
      console.error('Unable to load more notifications:', requestError)
      setError('More notifications could not be loaded. Please try again.')
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
          <button type="button" onClick={() => void markAllRead()}>
            Mark all as read
          </button>
        )}
      </header>

      {error && <p className="byb-notifications-error" role="alert">{error}</p>}

      {loading ? (
        <p className="byb-notifications-state" role="status">Loading notifications…</p>
      ) : notifications.length === 0 ? (
        <div className="byb-notifications-empty">
          <span aria-hidden="true">♡</span>
          <h2>You’re all caught up</h2>
          <p>New likes, comments, shares, saves, revibes, and follows will show up here.</p>
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
                to={getNotificationPath(notification)}
                className={`byb-notification${notification.read_at ? '' : ' unread'}`}
                onClick={(event) => {
                  if (notification.read_at) return
                  event.preventDefault()
                  void openNotification(notification).then((opened) => {
                    if (opened) navigate(getNotificationPath(notification))
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
                  <span><strong>{displayName}</strong> {notificationMessages[notification.verb]}</span>
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
          onClick={() => void loadMore()}
        >
          Load more
        </button>
      )}
    </section>
  )
}
