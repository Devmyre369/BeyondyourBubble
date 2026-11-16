import api from './api'
import type { HubType } from './hubsApi'

export type SearchCategory = 'all' | 'posts' | 'users' | 'events' | 'hubs'

export interface SearchPost {
  id: string
  content_type: 'vibe' | 'moment'
  author_username: string
  author_profile_picture: string
  content_text: string
  image_url: string
  event_title: string | null
  created_at: string
}

export interface SearchUser {
  username: string
  first_name: string
  last_name: string
  profile_type: 'student' | 'professional'
  profile_picture: string
  bio: string
  city: string
}

export interface SearchEvent {
  id: string
  title: string
  description: string
  starts_at: string | null
  venue_name: string
  city: string
}

export interface SearchHub {
  id: string
  name: string
  slug: string
  hub_type: HubType
  short_description: string
  logo: string
  city: string
  is_verified: boolean
}

export interface SearchResults {
  posts: SearchPost[]
  users: SearchUser[]
  events: SearchEvent[]
  hubs: SearchHub[]
}

export type SearchResultCounts = Record<
  Exclude<SearchCategory, 'all'>,
  number
>

export interface SearchResponse {
  query: string
  category: SearchCategory
  page: number
  page_size: number
  counts: SearchResultCounts
  has_more: Record<Exclude<SearchCategory, 'all'>, boolean>
  results: SearchResults
}

export const searchApi = {
  async search(
    query: string,
    options: {
      category?: SearchCategory
      page?: number
      pageSize?: number
    } = {},
  ): Promise<SearchResponse> {
    const response = await api.get<SearchResponse>('/search/', {
      params: {
        q: query,
        category: options.category ?? 'all',
        page: options.page ?? 1,
        page_size: options.pageSize ?? 10,
      },
    })
    return response.data
  },
}
