import api from './api'

export interface NotificationItem {
  id: string
  verb: 'like' | 'comment' | 'save' | 'share' | 'follow' | 'revibe'
  actor_username: string
  actor_first_name: string
  actor_last_name: string
  actor_profile_picture: string
  vibe_id: string | null
  moment_id: string | null
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

export const notificationsApi = {
  getNotifications: async (page = 1): Promise<NotificationPage> => {
    const response = await api.get<NotificationPage>('/accounts/notifications/', {
      params: { page },
    })
    return response.data
  },

  getUnreadCount: async (): Promise<number> => {
    const response = await api.get<{ unread_count: number }>(
      '/accounts/notifications/unread-count/',
    )
    return response.data.unread_count
  },

  markRead: async (id: string): Promise<void> => {
    await api.post(`/accounts/notifications/${id}/read/`)
  },

  markAllRead: async (): Promise<void> => {
    await api.post('/accounts/notifications/read-all/')
  },
}
