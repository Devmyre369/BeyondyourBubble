
import api from './api'
import type { PostCounts } from './vibespaceApi'

export interface FeedEntry extends PostCounts {
  id: string
  content_type: 'vibe' | 'moment'
  author_username: string
  author_profile_picture: string
  event_id: string | null
  event_title: string | null
  content_text: string
  image_url: string
  created_at: string
}

export interface FeedResponse {
  count: number
  next: number | null
  previous: number | null
  results: FeedEntry[]
}

export const feedApi = {
  async getFeed(page = 1): Promise<FeedResponse> {
    const response = await api.get<FeedResponse>(
      `/vibespace/feed/?page=${page}`
    )

    return response.data
  },
}
