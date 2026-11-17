import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { useAuth } from './AuthContext'
import type { FollowMutationResponse } from '../services/profileApi'

interface FollowState {
  isFollowing: boolean
  followersCount?: number
  followingCount?: number
  hasMutation?: boolean
}

interface FollowContextValue {
  states: Record<string, FollowState>
  setInitialState: (username: string, state: FollowState) => void
  applyMutation: (response: FollowMutationResponse) => void
}

const FollowContext = createContext<FollowContextValue | undefined>(undefined)

export function FollowProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, user } = useAuth()
  const [states, setStates] = useState<Record<string, FollowState>>({})

  useEffect(() => {
    setStates({})
  }, [isAuthenticated, user?.id])

  const setInitialState = useCallback((username: string, state: FollowState) => {
    setStates((previous) =>
      previous[username]?.hasMutation
        ? previous
        : { ...previous, [username]: state },
    )
  }, [])

  const applyMutation = useCallback((response: FollowMutationResponse) => {
    setStates((previous) => ({
      ...previous,
      [response.target_username]: {
        isFollowing: response.is_following,
        followersCount: response.followers_count,
        hasMutation: true,
      },
    }))
  }, [])

  const value = useMemo(
    () => ({ states, setInitialState, applyMutation }),
    [states, setInitialState, applyMutation],
  )

  return (
    <FollowContext.Provider value={value}>
      {children}
    </FollowContext.Provider>
  )
}

export function useFollowState(
  username: string,
  initialFollowing: boolean,
  initialFollowersCount?: number,
) {
  const context = useContext(FollowContext)
  if (!context) {
    throw new Error('useFollowState must be used inside a FollowProvider')
  }

  useEffect(() => {
    if (!username) return
    context.setInitialState(username, {
      isFollowing: initialFollowing,
      followersCount: initialFollowersCount,
    })
  }, [context.setInitialState, initialFollowing, initialFollowersCount, username])

  return {
    state: context.states[username],
    applyMutation: context.applyMutation,
  }
}
