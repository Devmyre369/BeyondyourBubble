
import api from './api'

export type EventCategory =
  | 'technical'
  | 'cultural'
  | 'academic'
  | 'sports'
  | 'business'
  | 'entertainment'
  | 'social'
  | 'political'
  | 'workshop'
  | 'other'

export type EventFormat = 'offline' | 'online' | 'hybrid'

export type EventStatus =
  | 'draft'
  | 'published'
  | 'cancelled'
  | 'completed'

export type EventModerationStatus =
  | 'pending'
  | 'approved'
  | 'rejected'

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface EventDiscoveryParams {
  search?: string
  category?: EventCategory
  city?: string
  format?: EventFormat
  page?: number
  upcoming?: boolean
  hub_id?: string
  hub?: string
}

export interface Event {
  id: string
  title: string
  description: string
  category: EventCategory
  cover_image_url: string
  starts_at: string | null
  ends_at: string | null
  format: EventFormat
  venue_name: string
  venue_address: string
  city: string
  online_join_url: string
  online_access_instructions: string
  status: EventStatus
  is_registered: boolean
  organising_hub: string
  organising_hub_name: string
  created_by_username: string
  created_at: string
}

export interface EventChoice {
  id: string
  title: string
  starts_at: string | null
  venue_name: string
  city: string
  status: 'published' | 'completed'
}

export interface EventSubmissionRequest {
  hub_id: string
  title: string
  description?: string
  category: EventCategory
  cover_image_url?: string
  starts_at: string
  ends_at: string
  format: EventFormat
  venue_name?: string
  venue_address?: string
  city?: string
  online_join_url?: string
  online_access_instructions?: string
}

export interface EventUpdateRequest {
  title?: string
  description?: string
  category?: EventCategory
  cover_image_url?: string
  starts_at?: string
  ends_at?: string
  format?: EventFormat
  venue_name?: string
  venue_address?: string
  city?: string
  online_join_url?: string
  online_access_instructions?: string
}

export interface ManagedEvent extends Omit<
  Event,
  'created_by_username' | 'is_registered'
> {
  moderation_status: EventModerationStatus
  created_by: string
  created_by_username: string
  reviewed_by: string | null
  reviewed_by_username: string | null
  review_notes: string
  review_category: EventRejectionCategory | ''
  reviewed_at: string | null
  updated_at: string
  moderation_history: EventModerationHistoryItem[]
}

export interface EventModerationHistoryItem {
  id: number
  decision: 'approved' | 'rejected'
  review_notes: string
  review_category: EventRejectionCategory | ''
  reviewed_at: string
  reviewer_username: string | null
}

export interface EventModerationItem {
  id: string
  title: string
  description: string
  category: EventCategory
  cover_image_url: string
  starts_at: string | null
  ends_at: string | null
  format: EventFormat
  venue_name: string
  venue_address: string
  city: string
  online_join_url: string
  online_access_instructions: string
  organising_hub: string
  organising_hub_name: string
  created_by: string
  created_by_username: string
  created_at: string
  review_category: EventRejectionCategory | ''
  review_notes: string
  moderation_history: EventModerationHistoryItem[]
}

export type EventRejectionCategory =
  | 'incomplete'
  | 'unverifiable'
  | 'duplicate'
  | 'misleading'
  | 'policy_violation'
  | 'inappropriate'
  | 'other'

export interface EventModerationParams {
  search?: string
  category?: EventCategory
  format?: EventFormat
  city?: string
  hub_id?: string
  submitted_after?: string
  submitted_before?: string
}

export interface EventModerationReviewRequest {
  decision: 'approve' | 'reject'
  review_notes?: string
  review_category?: EventRejectionCategory
}

export interface EventCancellationResponse {
  message: string
  event_id: string
  status: EventStatus
  moderation_status: EventModerationStatus
}

export interface EventRegistrationResponse {
  event_id: string
  is_registered: boolean
}

export interface EventModerationReviewResponse {
  message: string
  event_id: string
  status: EventStatus
  moderation_status: EventModerationStatus
  review_notes: string
  review_category: EventRejectionCategory | ''
  reviewed_at: string | null
}

export const eventsApi = {
  getEvents: async (
    params: EventDiscoveryParams = {},
  ): Promise<PaginatedResponse<Event>> => {
    const response = await api.get<PaginatedResponse<Event>>(
      '/events/',
      { params },
    )
    return response.data
  },

  getEvent: async (eventId: string): Promise<Event> => {
    const response = await api.get<Event>(
      `/events/${encodeURIComponent(eventId)}/`,
    )
    return response.data
  },

  registerForEvent: async (eventId: string): Promise<EventRegistrationResponse> => {
    const response = await api.post<EventRegistrationResponse>(
      `/events/${encodeURIComponent(eventId)}/registration/`,
      {},
    )
    return response.data
  },

  cancelRegistration: async (eventId: string): Promise<EventRegistrationResponse> => {
    const response = await api.delete<EventRegistrationResponse>(
      `/events/${encodeURIComponent(eventId)}/registration/`,
    )
    return response.data
  },

  submitEvent: async (
    data: EventSubmissionRequest,
  ): Promise<ManagedEvent> => {
    const response = await api.post<ManagedEvent>(
      '/events/',
      data,
    )
    return response.data
  },

  uploadEventCoverImage: async (
    eventId: string,
    image: File,
  ): Promise<string> => {
    const formData = new FormData()
    formData.append('image', image)

    const response = await api.post<{ cover_image_url: string }>(
      `/events/manage/${encodeURIComponent(eventId)}/cover-image/`,
      formData,
    )
    return response.data.cover_image_url
  },

  getEventChoices: async (): Promise<EventChoice[]> => {
    const response = await api.get<EventChoice[]>(
      '/events/choices/',
    )
    return response.data
  },

  getHubEvents: async (
    hubId: string,
    page = 1,
  ): Promise<PaginatedResponse<ManagedEvent>> => {
    const response = await api.get<PaginatedResponse<ManagedEvent>>(
      `/events/hubs/${encodeURIComponent(hubId)}/`,
      { params: { page } },
    )
    return response.data
  },

  getManagedEvent: async (
    eventId: string,
  ): Promise<ManagedEvent> => {
    const response = await api.get<ManagedEvent>(
      `/events/manage/${encodeURIComponent(eventId)}/`,
    )
    return response.data
  },

  updateEvent: async (
    eventId: string,
    data: EventUpdateRequest,
  ): Promise<ManagedEvent> => {
    const response = await api.patch<ManagedEvent>(
      `/events/manage/${encodeURIComponent(eventId)}/`,
      data,
    )
    return response.data
  },

  cancelEvent: async (
    eventId: string,
  ): Promise<EventCancellationResponse> => {
    const response = await api.post<EventCancellationResponse>(
      `/events/manage/${encodeURIComponent(eventId)}/cancel/`,
      {},
    )
    return response.data
  },

  getModerationQueue: async (page = 1, params: EventModerationParams = {}): Promise<
    PaginatedResponse<EventModerationItem>
  > => {
    const response = await api.get<
      PaginatedResponse<EventModerationItem>
    >('/events/moderation/', { params: { page, ...params } })
    return response.data
  },

  reviewEvent: async (
    eventId: string,
    data: EventModerationReviewRequest,
  ): Promise<EventModerationReviewResponse> => {
    const response = await api.post<EventModerationReviewResponse>(
      `/events/moderation/${encodeURIComponent(eventId)}/review/`,
      data,
    )
    return response.data
  },
}
