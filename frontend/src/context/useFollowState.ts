import { useContext, useEffect } from 'react'

import { useAuth } from './AuthContext'
import { FollowContext, type FollowState } from './followContext'

export function useFollowState(
  username: string,
  initialFollowing: boolean,
  initialFollowersCount?: number,
) {
  const context = useContext(FollowContext)
  const { user } = useAuth()
  if (!context) {
    throw new Error('useFollowState must be used inside a FollowProvider')
  }

  const key = `${user?.username.toLowerCase() ?? 'anonymous'}:${username.toLowerCase()}`
  const { states, setInitialState, applyMutation } = context

  useEffect(() => {
    if (!username) return
    const initialState: FollowState = {
      isFollowing: initialFollowing,
      followersCount: initialFollowersCount,
    }
    setInitialState(key, initialState)
  }, [initialFollowersCount, initialFollowing, key, setInitialState, username])

  return {
    state: states[key],
    applyMutation,
  }
}
