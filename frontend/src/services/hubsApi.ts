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
export type HubApplicationStatus = 'pending' | 'approved' | 'rejected'
export type HubVerificationStatus = 'not_requested' | 'pending' | 'approved' | 'rejected'

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
  verification_status: HubVerificationStatus
  created_at: string
}

export interface HubDetail extends HubListItem {
  description: string
  website: string
  membership_policy: HubMembershipPolicy
  can_edit: boolean
  can_edit_membership_policy: boolean
  can_request_verification: boolean
  verification_review_notes: string
  verification_reviewed_at: string | null
}

export interface HubApplication {
  id: string
  requested_name: string
  requested_slug: string
  hub_type: HubType
  organisation_description: string
  college_or_parent_organisation: string
  city: string
  website: string
  contact_email: string
  status: HubApplicationStatus
  applicant: string
  applicant_username: string
  reviewer: string | null
  reviewer_username: string | null
  review_notes: string
  created_at: string
  reviewed_at: string | null
  created_hub_id: string | null
}

export interface HubApplicationSubmitRequest {
  requested_name: string
  requested_slug: string
  hub_type: HubType
  organisation_description?: string
  college_or_parent_organisation?: string
  city?: string
  website?: string
  contact_email?: string
}

export interface HubVerificationRequest {
  id: string
  hub: string
  hub_name: string
  hub_slug: string
  hub_type: HubType
  hub_city: string
  hub_is_verified: boolean
  requested_by: string
  requested_by_username: string
  request_notes: string
  status: HubApplicationStatus
  reviewer: string | null
  reviewer_username: string | null
  review_notes: string
  requested_at: string
  reviewed_at: string | null
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

export interface HubDiscoveryResponse<T = HubListItem> {
  count: number
  next: number | null
  previous: number | null
  results: T[]
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

  submitApplication: async (data: HubApplicationSubmitRequest): Promise<HubApplication> => {
    const response = await api.post<HubApplication>('/hubs/applications/', data)
    return response.data
  },

  getMyApplications: async (page = 1): Promise<HubDiscoveryResponse<HubApplication>> => {
    const response = await api.get<HubDiscoveryResponse<HubApplication>>(
      '/hubs/applications/mine/', { params: { page } },
    )
    return response.data
  },

  getApplicationReviewQueue: async (
    status: HubApplicationStatus = 'pending',
    page = 1,
  ): Promise<HubDiscoveryResponse<HubApplication>> => {
    const response = await api.get<HubDiscoveryResponse<HubApplication>>(
      '/hubs/applications/review/', { params: { status, page } },
    )
    return response.data
  },

  reviewApplication: async (
    applicationId: string,
    decision: 'approve' | 'reject',
    review_notes = '',
  ): Promise<{ application: HubApplication; hub_id: string | null }> => {
    const response = await api.post<{ application: HubApplication; hub_id: string | null }>(
      `/hubs/applications/review/${encodeURIComponent(applicationId)}/`,
      { decision, review_notes },
    )
    return response.data
  },

  requestVerification: async (
    hubId: string,
    request_notes = '',
  ): Promise<HubVerificationRequest> => {
    const response = await api.post<HubVerificationRequest>(
      `/hubs/${encodeURIComponent(hubId)}/verification-requests/`,
      { request_notes },
    )
    return response.data
  },

  getVerificationReviewQueue: async (page = 1, status: HubApplicationStatus = 'pending'): Promise<HubDiscoveryResponse<HubVerificationRequest>> => {
    const response = await api.get<HubDiscoveryResponse<HubVerificationRequest>>(
      '/hubs/verification-requests/review/', { params: { page, status } },
    )
    return response.data
  },

  reviewVerificationRequest: async (
    requestId: string,
    decision: 'approve' | 'reject',
    review_notes = '',
  ): Promise<HubVerificationRequest> => {
    const response = await api.post<HubVerificationRequest>(
      `/hubs/verification-requests/review/${encodeURIComponent(requestId)}/`,
      { decision, review_notes },
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
