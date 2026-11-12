
import api from './api'

export type ProfileType = 'student' | 'professional'

export type ProfileVisibility = 'public' | 'private'

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

export type CreateProfileData = Omit<
  UserProfile,
  | 'id'
  | 'username'
  | 'created_at'
  | 'updated_at'
>

export type UpdateProfileData = Partial<CreateProfileData>

interface ProfileResponse {
  success: boolean
  message?: string
  profile: UserProfile
}

export const profileApi = {
  getMyProfile: async (): Promise<UserProfile> => {
    const response = await api.get<ProfileResponse>(
      '/accounts/profile/'
    )

    return response.data.profile
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
}

export default profileApi
