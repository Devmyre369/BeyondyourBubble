
import api from './api'

// ==============================
// TYPES
// ==============================

export interface PostCounts {
  like_count: number
  comment_count: number
  revibe_count: number
  save_count: number
  share_count: number
}

export interface EventChoice {
  id: string
  title: string
  starts_at: string | null
  venue_name: string
  city: string
  status: 'published' | 'completed'
}

export interface Vibe extends PostCounts {
  id: string
  author_username: string
  event: string | null
  event_title: string | null
  text: string
  created_at: string
  updated_at: string
}

export interface Moment extends PostCounts {
  id: string
  author_username: string
  event: string | null
  event_title: string | null
  image_url: string
  caption: string
  created_at: string
  updated_at: string
}

export interface Comment {
  id: string
  author_username: string
  text: string
  created_at: string
  updated_at: string
}

export interface Revibe {
  id: string
  author_username: string
  vibe: string | null
  moment: string | null
  revibe_type: 'direct' | 'quote'
  quote_text: string
  created_at: string
}

export interface SavedContent {
  id: string
  vibe: string | null
  moment: string | null
  created_at: string
}

export interface LikeState {
  liked: boolean
  like_count: number
}

export interface ShareState {
  share_count: number
}

interface MomentCreateResponse {
  success: boolean
  message: string
  moment: Moment
}

interface CommentCreateResponse {
  success: boolean
  message: string
  comment: Comment
}

interface RevibeResponse {
  success: boolean
  message: string
  revibe: Revibe
}

interface SavedContentResponse {
  success: boolean
  message: string
  saved_content: SavedContent
}

// ==============================
// API
// ==============================

export const vibespaceApi = {
  // EVENT CHOICES

  getEventChoices: async (): Promise<EventChoice[]> => {
    const response = await api.get<EventChoice[]>('/events/choices/')
    return response.data
  },

  // VIBES

  getVibes: async (username?: string): Promise<Vibe[]> => {
    const response = await api.get<Vibe[]>('/vibespace/vibes/', {
      params: username ? { username } : {},
    })

    return response.data
  },

  createVibe: async (data: {
    text: string
    event?: string | null
  }): Promise<Vibe> => {
    const response = await api.post<Vibe>('/vibespace/vibes/', data)
    return response.data
  },

  updateVibe: async (
    id: string,
    data: {
      text?: string
      event?: string | null
    },
  ): Promise<Vibe> => {
    const response = await api.patch<Vibe>(
      `/vibespace/vibes/${id}/`,
      data,
    )

    return response.data
  },

  deleteVibe: async (id: string): Promise<void> => {
    await api.delete(`/vibespace/vibes/${id}/`)
  },

  // MOMENTS

  getMoments: async (username?: string): Promise<Moment[]> => {
    const response = await api.get<Moment[]>('/vibespace/moments/', {
      params: username ? { username } : {},
    })

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
      formData,
    )

    return response.data.moment
  },

  updateMoment: async (
    id: string,
    data: {
      caption?: string
      event?: string | null
    },
  ): Promise<Moment> => {
    const response = await api.patch<Moment>(
      `/vibespace/moments/${id}/`,
      data,
    )

    return response.data
  },

  deleteMoment: async (id: string): Promise<void> => {
    await api.delete(`/vibespace/moments/${id}/`)
  },

  // COMMENTS

  getVibeComments: async (vibeId: string): Promise<Comment[]> => {
    const response = await api.get<Comment[]>(
      `/vibespace/vibe/${vibeId}/comments/`,
    )

    return response.data
  },

  getMomentComments: async (momentId: string): Promise<Comment[]> => {
    const response = await api.get<Comment[]>(
      `/vibespace/moment/${momentId}/comments/`,
    )

    return response.data
  },

  createVibeComment: async (
    vibeId: string,
    text: string,
  ): Promise<Comment> => {
    const response = await api.post<CommentCreateResponse>(
      `/vibespace/vibe/${vibeId}/comments/`,
      { text },
    )

    return response.data.comment
  },

  createMomentComment: async (
    momentId: string,
    text: string,
  ): Promise<Comment> => {
    const response = await api.post<CommentCreateResponse>(
      `/vibespace/moment/${momentId}/comments/`,
      { text },
    )

    return response.data.comment
  },

  updateComment: async (
    commentId: string,
    text: string,
  ): Promise<Comment> => {
    const response = await api.patch<Comment>(
      `/vibespace/comments/${commentId}/`,
      { text },
    )

    return response.data
  },

  deleteComment: async (commentId: string): Promise<void> => {
    await api.delete(`/vibespace/comments/${commentId}/`)
  },

  // REVIBES

  getVibeRevibe: async (vibeId: string): Promise<Revibe | null> => {
    const response = await api.get<Revibe | null>(
      `/vibespace/vibe/${vibeId}/revibe/`,
    )

    return response.data
  },

  getMomentRevibe: async (momentId: string): Promise<Revibe | null> => {
    const response = await api.get<Revibe | null>(
      `/vibespace/moment/${momentId}/revibe/`,
    )

    return response.data
  },

  revibeVibe: async (
    vibeId: string,
    data: {
      revibe_type: 'direct' | 'quote'
      quote_text?: string
    },
  ): Promise<Revibe> => {
    const response = await api.post<RevibeResponse>(
      `/vibespace/vibe/${vibeId}/revibe/`,
      data,
    )

    return response.data.revibe
  },

  revibeMoment: async (
    momentId: string,
    data: {
      revibe_type: 'direct' | 'quote'
      quote_text?: string
    },
  ): Promise<Revibe> => {
    const response = await api.post<RevibeResponse>(
      `/vibespace/moment/${momentId}/revibe/`,
      data,
    )

    return response.data.revibe
  },

  removeVibeRevibe: async (vibeId: string): Promise<void> => {
    await api.delete(`/vibespace/vibe/${vibeId}/revibe/`)
  },

  removeMomentRevibe: async (momentId: string): Promise<void> => {
    await api.delete(`/vibespace/moment/${momentId}/revibe/`)
  },

  // LIKES

  getLikeState: async (
    type: 'vibe' | 'moment',
    id: string,
  ): Promise<LikeState> => {
    const response = await api.get<LikeState>(
      `/vibespace/${type}/${id}/like/`,
    )

    return response.data
  },

  likeContent: async (
    type: 'vibe' | 'moment',
    id: string,
  ): Promise<LikeState> => {
    const response = await api.post<LikeState>(
      `/vibespace/${type}/${id}/like/`,
    )

    return response.data
  },

  unlikeContent: async (
    type: 'vibe' | 'moment',
    id: string,
  ): Promise<LikeState> => {
    const response = await api.delete<LikeState>(
      `/vibespace/${type}/${id}/like/`,
    )

    return response.data
  },

  shareContent: async (
    type: 'vibe' | 'moment',
    id: string,
  ): Promise<ShareState> => {
    const response = await api.post<ShareState>(
      `/vibespace/${type}/${id}/share/`,
    )

    return response.data
  },

  // SAVED CONTENT

  getSavedContent: async (): Promise<SavedContent[]> => {
    const response = await api.get<SavedContent[]>('/vibespace/saved/')
    return response.data
  },

  saveVibe: async (vibeId: string): Promise<SavedContent> => {
    const response = await api.post<SavedContentResponse>(
      '/vibespace/saved/',
      { vibe: vibeId },
    )

    return response.data.saved_content
  },

  saveMoment: async (momentId: string): Promise<SavedContent> => {
    const response = await api.post<SavedContentResponse>(
      '/vibespace/saved/',
      { moment: momentId },
    )

    return response.data.saved_content
  },

  removeSavedContent: async (savedId: string): Promise<void> => {
    await api.delete(`/vibespace/saved/${savedId}/`)
  },
}

export default vibespaceApi
