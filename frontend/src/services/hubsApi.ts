import api from './api'

export type HubType =
  | 'college'
  | 'college_club'
  | 'college_department'
  | 'organisation'
  | 'company'
  | 'community'

export type HubMembershipPolicy = 'open' | 'approval_required'
export type HubMembershipRole = 'owner' | 'admin' | 'editor' | 'member'
export type HubMembershipStatus = 'pending' | 'approved' | 'rejected'

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

export interface HubMembership {
  id: string
  role: HubMembershipRole
  status: HubMembershipStatus
  joined_at: string | null
}

export interface HubMembershipState {
  membership: HubMembership | null
  membership_policy: HubMembershipPolicy
  can_leave: boolean
  can_manage_members: boolean
  pending_request_count: number | null
}

export interface HubMember {
  id: string
  username: string | null
  first_name: string
  last_name: string
  profile_picture: string
  role: HubMembershipRole
  status: HubMembershipStatus
  joined_at: string | null
}

export interface HubMemberListResponse {
  count: number
  next: number | null
  previous: number | null
  results: HubMember[]
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

  uploadHubImage: async (
    hubId: string,
    imageType: 'logo' | 'cover_image',
    file: File,
  ): Promise<HubDetail> => {
    const formData = new FormData()
    formData.append('image', file)

    const response = await api.post<HubDetail>(
      `/hubs/${encodeURIComponent(hubId)}/images/${imageType}/`,
      formData,
    )
    return response.data
  },

  getMembership: async (hubId: string): Promise<HubMembershipState> => {
    const response = await api.get<HubMembershipState>(
      `/hubs/${encodeURIComponent(hubId)}/membership/`,
    )
    return response.data
  },

  joinHub: async (hubId: string): Promise<HubMembershipState> => {
    const response = await api.post<HubMembershipState>(
      `/hubs/${encodeURIComponent(hubId)}/membership/`,
      {},
    )
    return response.data
  },

  leaveHub: async (hubId: string): Promise<void> => {
    await api.delete<void>(
      `/hubs/${encodeURIComponent(hubId)}/membership/`,
    )
  },

  getMembers: async (
    hubId: string,
    page = 1,
  ): Promise<HubMemberListResponse> => {
    const response = await api.get<HubMemberListResponse>(
      `/hubs/${encodeURIComponent(hubId)}/members/`,
      { params: { page } },
    )
    return response.data
  },

  getPendingRequests: async (
    hubId: string,
    page = 1,
  ): Promise<HubMemberListResponse> => {
    const response = await api.get<HubMemberListResponse>(
      `/hubs/${encodeURIComponent(hubId)}/members/requests/`,
      { params: { page } },
    )
    return response.data
  },

  approveMembershipRequest: async (
    hubId: string,
    membershipId: string,
  ): Promise<HubMember> => {
    const response = await api.post<HubMember>(
      `/hubs/${encodeURIComponent(hubId)}/members/requests/${encodeURIComponent(membershipId)}/approve/`,
      {},
    )
    return response.data
  },

  rejectMembershipRequest: async (
    hubId: string,
    membershipId: string,
  ): Promise<HubMember> => {
    const response = await api.post<HubMember>(
      `/hubs/${encodeURIComponent(hubId)}/members/requests/${encodeURIComponent(membershipId)}/reject/`,
      {},
    )
    return response.data
  },

  inviteMember: async (
    hubId: string,
    username: string,
  ): Promise<HubMember> => {
    const response = await api.post<HubMember>(
      `/hubs/${encodeURIComponent(hubId)}/members/invitations/`,
      { username },
    )
    return response.data
  },

  removeMember: async (
    hubId: string,
    membershipId: string,
  ): Promise<void> => {
    await api.delete<void>(
      `/hubs/${encodeURIComponent(hubId)}/members/${encodeURIComponent(membershipId)}/`,
    )
  },

  updateMemberRole: async (
    hubId: string,
    membershipId: string,
    role: Exclude<HubMembershipRole, 'owner'>,
  ): Promise<HubMember> => {
    const response = await api.patch<HubMember>(
      `/hubs/${encodeURIComponent(hubId)}/members/${encodeURIComponent(membershipId)}/role/`,
      { role },
    )
    return response.data
  },
}
