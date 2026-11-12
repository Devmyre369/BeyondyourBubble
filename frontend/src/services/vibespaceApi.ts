import api from './api'

// ==============================
// TYPES
// ==============================

export interface EventChoice {
  id: string
  title: string
  starts_at: string | null
  venue_name: string
  city: string
  status: 'published' | 'completed'
}

export interface Vibe {
  id: string
  author_username: string
  event: string | null
  event_title: string | null
  text: string
  created_at: string
  updated_at: string
}

export interface Moment {
  id: string
  author_username: string
  event: string | null
  event_title: string | null
  image_url: string
  caption: string
  created_at: string
  updated_at: string
}

interface MomentCreateResponse {
  success: boolean
  message: string
  moment: Moment
}

// ==============================
// API
// ==============================

export const vibespaceApi = {

  // EVENT CHOICES

  getEventChoices: async (): Promise<EventChoice[]> => {
    const response = await api.get<EventChoice[]>(
      '/events/choices/'
    )

    return response.data
  },

  // VIBES

  getVibes: async (username?: string): Promise<Vibe[]> => {
    const response = await api.get<Vibe[]>(
      '/vibespace/vibes/',
      {
        params: username ? { username } : {},
      }
    )

    return response.data
  },

  createVibe: async (data: {
    text: string
    event?: string | null
  }): Promise<Vibe> => {
    const response = await api.post<Vibe>(
      '/vibespace/vibes/',
      data
    )

    return response.data
  },

  updateVibe: async (
    id: string,
    data: {
      text?: string
      event?: string | null
    }
  ): Promise<Vibe> => {
    const response = await api.patch<Vibe>(
      `/vibespace/vibes/${id}/`,
      data
    )

    return response.data
  },

  deleteVibe: async (id: string): Promise<void> => {
    await api.delete(`/vibespace/vibes/${id}/`)
  },

  // MOMENTS

  getMoments: async (username?: string): Promise<Moment[]> => {
    const response = await api.get<Moment[]>(
      '/vibespace/moments/',
      {
        params: username ? { username } : {},
      }
    )

    return response.data
  },

  createMoment: async (data: {
    image: File
    caption?: string
    event?: string | null
  }): Promise<Moment> => {
    const formData = new FormData()

    formData.append('image', data.image)
    formData.append('caption', data.caption || '')

    if (data.event) {
      formData.append('event', data.event)
    }

    const response = await api.post<MomentCreateResponse>(
      '/vibespace/moments/',
      formData
    )

    return response.data.moment
  },

  updateMoment: async (
    id: string,
    data: {
      caption?: string
      event?: string | null
    }
  ): Promise<Moment> => {
    const response = await api.patch<Moment>(
      `/vibespace/moments/${id}/`,
      data
    )

    return response.data
  },

  deleteMoment: async (id: string): Promise<void> => {
    await api.delete(`/vibespace/moments/${id}/`)
  },
}

export default vibespaceApi