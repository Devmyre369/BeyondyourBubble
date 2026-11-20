import api from './api'

export interface NotificationItem {
  id: string
  verb:
    | 'like'
    | 'comment'
    | 'save'
    | 'share'
    | 'follow'
    | 'revibe'
    | 'handshake_request'
    | 'handshake_accepted'
    | 'event_approved'
    | 'event_rejected'
    | 'event_submitted'
    | 'event_updated'
    | 'event_cancelled'
    | 'hub_application_submitted'
    | 'hub_application_approved'
    | 'hub_application_rejected'
    | 'hub_membership_request'
    | 'hub_member_joined'
    | 'hub_member_left'
    | 'hub_membership_approved'
    | 'hub_membership_rejected'
    | 'hub_invited'
    | 'hub_member_removed'
    | 'hub_role_changed'
    | 'hub_verification_requested'
    | 'hub_verification_approved'
    | 'hub_verification_rejected'
  actor_username: string
  actor_first_name: string
  actor_last_name: string
  actor_profile_picture: string
  vibe_id: string | null
  moment_id: string | null
  handshake_id: string | null
  handshake_status: 'pending' | 'accepted' | 'rejected' | 'cancelled' | null
  event_id: string | null
  event_title: string | null
  event_status: string | null
  event_moderation_status: string | null
  hub_id: string | null
  hub_name: string | null
  content_author_username: string | null
  created_at: string
  read_at: string | null
}

export interface NotificationPage {
  count: number
  next: number | null
  previous: number | null
  unread_count: number
  results: NotificationItem[]
}

let unreadCountRequest: Promise<number> | null = null

export const notificationsApi = {
  getNotifications: async (page = 1): Promise<NotificationPage> => {
    const response = await api.get<NotificationPage>('/accounts/notifications/', {
      params: { page },
    })
    return response.data
  },

  getUnreadCount: async (): Promise<number> => {
    if (!unreadCountRequest) {
      unreadCountRequest = api.get<{ unread_count: number }>(
        '/accounts/notifications/unread-count/',
      )
        .then((response) => response.data.unread_count)
        .finally(() => {
          unreadCountRequest = null
        })
    }
    return unreadCountRequest
  },

  markRead: async (id: string): Promise<void> => {
    await api.post(`/accounts/notifications/${id}/read/`)
  },

  markAllRead: async (): Promise<void> => {
    await api.post('/accounts/notifications/read-all/')
  },
}
