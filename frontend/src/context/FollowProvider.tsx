import {
  useCallback,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { FollowContext } from './followContext'
import type { FollowState } from './followContext'
import type { FollowMutationResponse } from '../services/profileApi'

export function FollowProvider({ children }: { children: ReactNode }) {
  const [states, setStates] = useState<Record<string, FollowState>>({})

  const setInitialState = useCallback((key: string, state: FollowState) => {
    setStates((previous) =>
      previous[key]?.hasMutation
        ? previous
        : { ...previous, [key]: state },
    )
  }, [])

  const applyMutation = useCallback((response: FollowMutationResponse) => {
    const key = `${response.viewer_username.toLowerCase()}:${response.target_username.toLowerCase()}`
    setStates((previous) => ({
      ...previous,
      [key]: {
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
