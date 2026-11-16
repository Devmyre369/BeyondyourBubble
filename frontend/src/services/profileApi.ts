
import api from './api'

export type ProfileType = 'student' | 'professional'
export type ProfileVisibility = 'public' | 'private'
export type ProfileImageType = 'profile_picture' | 'cover_image'

export interface UserProfile {
  id: string
  username: string

  first_name: string
  last_name: string

  profile_type: ProfileType
  byb_signature: string | null
  bio: string
  city: string

  profile_picture: string
  cover_image: string

  institution: string
  course: string
  field_of_study: string
  academic_year: string
  graduation_year: number | null

  current_organization: string
  job_title: string
  industry: string
  experience_years: number | null

  interests: string[]
  skills: string[]

  linkedin_url: string
  github_url: string
  website_url: string

  visibility: ProfileVisibility

  created_at: string
  updated_at: string
}

export interface ProfileStatistics {
  posts_count: number
  vibes_count: number
  moments_count: number
  followers_count: number
  following_count: number
}

export interface ProfileOverview {
  profile: UserProfile
  statistics: ProfileStatistics
  is_following: boolean
}

export interface FollowMutationResponse {
  target_username: string
  is_following: boolean
  followers_count: number
  viewer_username: string
  viewer_following_count: number
}

export interface PublicConnectionUser {
  id: string
  username: string
  first_name: string
  last_name: string
  profile_picture: string
  byb_signature: string | null
  profile_type: ProfileType | null
  bio: string
  city: string
  institution: string
  current_organization: string
  job_title: string
  is_following: boolean
}

export interface PaginatedResponse<T> {
  count: number
  next: number | null
  previous: number | null
  results: T[]
}

export type CreateProfileData = Omit<
  UserProfile,
  | 'id'
  | 'username'
  | 'profile_picture'
  | 'cover_image'
  | 'created_at'
  | 'updated_at'
>

export type UpdateProfileData = Partial<CreateProfileData>

interface ProfileResponse {
  success: boolean
  message?: string
  profile: UserProfile
  statistics?: ProfileStatistics
  is_following?: boolean
}

interface ProfileOverviewResponse {
  profile: UserProfile
  statistics: ProfileStatistics
  is_following: boolean
}

interface ProfileImageResponse {
  success: boolean
  message?: string
  image_type?: ProfileImageType
  image_url?: string
  profile: UserProfile
}

export const profileApi = {
  getMyProfile: async (): Promise<UserProfile> => {
    const response = await api.get<ProfileResponse>(
      '/accounts/profile/'
    )

    return response.data.profile
  },

  getMyProfileOverview: async (): Promise<ProfileOverview> => {
    const response = await api.get<ProfileOverviewResponse>('/accounts/profile/')
    return {
      profile: response.data.profile,
      statistics: response.data.statistics,
      is_following: response.data.is_following,
    }
  },

  createProfile: async (
    data: CreateProfileData
  ): Promise<UserProfile> => {
    const response = await api.post<ProfileResponse>(
      '/accounts/profile/',
      data
    )

    return response.data.profile
  },

  updateProfile: async (
    data: UpdateProfileData
  ): Promise<UserProfile> => {
    const response = await api.patch<ProfileResponse>(
      '/accounts/profile/',
      data
    )

    return response.data.profile
  },

  getPublicProfile: async (
    username: string
  ): Promise<UserProfile> => {
    const response = await api.get<ProfileResponse>(
      `/accounts/profile/${encodeURIComponent(username)}/`
    )

    return response.data.profile
  },

  getPublicProfileOverview: async (
    username: string
  ): Promise<ProfileOverview> => {
    const response = await api.get<ProfileOverviewResponse>(
      `/accounts/profile/${encodeURIComponent(username)}/`
    )
    return {
      profile: response.data.profile,
      statistics: response.data.statistics,
      is_following: response.data.is_following,
    }
  },

  followUser: async (username: string): Promise<FollowMutationResponse> => {
    const response = await api.post<FollowMutationResponse>(
      `/accounts/profile/${encodeURIComponent(username)}/follow/`
    )
    return response.data
  },

  unfollowUser: async (username: string): Promise<FollowMutationResponse> => {
    const response = await api.delete<FollowMutationResponse>(
      `/accounts/profile/${encodeURIComponent(username)}/follow/`
    )
    return response.data
  },

  getProfileConnections: async (
    username: string,
    relationship: 'followers' | 'following',
    page = 1,
  ): Promise<PaginatedResponse<PublicConnectionUser>> => {
    const response = await api.get<PaginatedResponse<PublicConnectionUser>>(
      `/accounts/profile/${encodeURIComponent(username)}/${relationship}/`,
      { params: { page } },
    )
    return response.data
  },

  uploadProfileImage: async (
    imageType: ProfileImageType,
    file: File
  ): Promise<UserProfile> => {
    const formData = new FormData()
    formData.append('image', file)

    const response = await api.post<ProfileImageResponse>(
      `/accounts/profile/image/${imageType}/`,
      formData
    )

    return response.data.profile
  },

  deleteProfileImage: async (
    imageType: ProfileImageType
  ): Promise<UserProfile> => {
    const response = await api.delete<ProfileImageResponse>(
      `/accounts/profile/image/${imageType}/`
    )

    return response.data.profile
  },
}

export default profileApi
