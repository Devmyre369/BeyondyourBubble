import api from './api'

export type HubType =
  | 'college'
  | 'college_club'
  | 'college_department'
  | 'organisation'
  | 'company'
  | 'community'

export type HubMembershipPolicy = 'open' | 'approval_required'

export interface HubDiscoveryParams {
  hub_type?: HubType
  city?: string
  search?: string
  page?: number
}

export interface HubListItem {
  id: string
  name: string
  slug: string
  hub_type: HubType
  short_description: string
  logo: string
  cover_image: string
  city: string
  college_or_parent_organisation: string
  is_verified: boolean
  created_at: string
}

export interface HubDetail extends HubListItem {
  description: string
  website: string
  membership_policy: HubMembershipPolicy
  can_edit: boolean
  can_edit_membership_policy: boolean
}

export interface HubUpdateRequest {
  name?: string
  hub_type?: HubType
  short_description?: string
  description?: string
  logo?: string
  cover_image?: string
  website?: string
  city?: string
  college_or_parent_organisation?: string
  membership_policy?: HubMembershipPolicy
}

export interface HubCreateRequest {
  name: string
  hub_type: HubType
  visibility?: 'public'
  membership_policy?: HubMembershipPolicy
  short_description?: string
  description?: string
  logo?: string
  cover_image?: string
  website?: string
  contact_email?: string
  city?: string
  college_or_parent_organisation?: string
}

export interface HubDiscoveryResponse {
  count: number
  next: number | null
  previous: number | null
  results: HubListItem[]
}

export const hubsApi = {
  getHubs: async (
    params: HubDiscoveryParams = {},
  ): Promise<HubDiscoveryResponse> => {
    const response = await api.get<HubDiscoveryResponse>('/hubs/', { params })
    return response.data
  },

  getHub: async (hubId: string): Promise<HubDetail> => {
    const response = await api.get<HubDetail>(
      `/hubs/${encodeURIComponent(hubId)}/`,
    )
    return response.data
  },

  createHub: async (data: HubCreateRequest): Promise<HubDetail> => {
    const response = await api.post<HubDetail>('/hubs/', data)
    return response.data
  },

  updateHub: async (
    hubId: string,
    data: HubUpdateRequest,
  ): Promise<HubDetail> => {
    const response = await api.patch<HubDetail>(
      `/hubs/${encodeURIComponent(hubId)}/`,
      data,
    )
    return response.data
  },
}
