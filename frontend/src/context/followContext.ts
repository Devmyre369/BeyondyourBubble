import { createContext } from 'react'

import type { FollowMutationResponse } from '../services/profileApi'

export interface FollowState {
  isFollowing: boolean
  followersCount?: number
  followingCount?: number
  hasMutation?: boolean
}

export interface FollowContextValue {
  states: Record<string, FollowState>
  setInitialState: (key: string, state: FollowState) => void
  applyMutation: (response: FollowMutationResponse) => void
}

export const FollowContext =
  createContext<FollowContextValue | undefined>(undefined)
