import api from './api'

export type HubType =
  | 'college'
  | 'college_club'
  | 'college_department'
  | 'organisation'
  | 'company'
  | 'community'

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
}
