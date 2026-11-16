import axios from 'axios'
import {
  useEffect,
  useState,
  type FormEvent,
} from 'react'
import { Link } from 'react-router-dom'

import {
  hubsApi,
  type HubMember,
  type HubMemberListResponse,
  type HubMembershipRole,
  type HubMembershipState,
} from '../../services/hubsApi'
import './hub-membership.css'

type AssignableRole = Exclude<HubMembershipRole, 'owner'>
type ListResult = {
  page: number
  revision: number
  data: HubMemberListResponse
}
type ListFailure = {
  page: number
  revision: number
  message: string
}

function isAssignableRole(value: string): value is AssignableRole {
  return value === 'admin' || value === 'editor' || value === 'member'
}

function getErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return 'Something went wrong. Please try again.'
  }

  const status = error.response?.status
  if (status === 401) return 'Your session expired. Please sign in again.'
  if (status === 403) {
    return 'Your Hub permissions changed. Membership information is being refreshed.'
  }
  if (status === 404) {
    return 'This Hub or membership is no longer available. Refresh the page and try again.'
  }

  const data: unknown = error.response?.data
  if (data && typeof data === 'object') {
    const record = data as Record<string, unknown>
    const detail = record.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.every((item) => typeof item === 'string')) {
      return detail.join(' ')
    }

    for (const value of Object.values(record)) {
      if (typeof value === 'string') return value
      if (Array.isArray(value)) {
        const message = value.find((item) => typeof item === 'string')
        if (typeof message === 'string') return message
      }
    }
  }

  if (!error.response) {
    return 'Unable to reach BYB. Check your connection and try again.'
  }
  return 'The request could not be completed. Please try again.'
}

function displayName(member: HubMember, pending = false): string {
  const name = `${member.first_name} ${member.last_name}`.trim()
  if (name) return name
  if (member.username) return `@${member.username}`
  if (member.role === 'owner') return 'Hub owner'
  return pending ? 'Private profile applicant' : 'Private member'
}

function roleLabel(role: HubMembershipRole): string {
  return role.charAt(0).toUpperCase() + role.slice(1)
}

function MemberAvatar({ member, pending = false }: {
  member: HubMember
  pending?: boolean
}) {
  const [imageFailed, setImageFailed] = useState(false)
  const name = displayName(member, pending)

  if (member.profile_picture && !imageFailed) {
    return (
      <img
        className="hub-member-avatar"
        src={member.profile_picture}
        alt=""
        loading="lazy"
        onError={() => setImageFailed(true)}
      />
    )
  }

  return (
    <span className="hub-member-avatar hub-member-avatar-placeholder" aria-hidden="true">
      {name.charAt(0).toUpperCase() || 'M'}
    </span>
  )
}

export default function HubMembershipPanel({ hubId }: { hubId: string }) {
  const [membershipState, setMembershipState] =
    useState<HubMembershipState | null>(null)
  const [membershipLoading, setMembershipLoading] = useState(true)
  const [membershipError, setMembershipError] = useState('')
  const [membershipRevision, setMembershipRevision] = useState(0)

  const [membersPage, setMembersPage] = useState(1)
  const [membersRevision, setMembersRevision] = useState(0)
  const [membersResult, setMembersResult] = useState<ListResult | null>(null)
  const [membersFailure, setMembersFailure] = useState<ListFailure | null>(null)

  const [requestsPage, setRequestsPage] = useState(1)
  const [requestsRevision, setRequestsRevision] = useState(0)
  const [requestsResult, setRequestsResult] = useState<ListResult | null>(null)
  const [requestsFailure, setRequestsFailure] = useState<ListFailure | null>(null)

  const [actionKey, setActionKey] = useState('')
  const [actionError, setActionError] = useState('')
  const [actionSuccess, setActionSuccess] = useState('')
  const [inviteUsername, setInviteUsername] = useState('')
  const [inviteError, setInviteError] = useState('')
  const [roleDrafts, setRoleDrafts] = useState<Record<string, AssignableRole>>({})

  useEffect(() => {
    let active = true
    void hubsApi
      .getMembership(hubId)
      .then((result) => {
        if (active) {
          setMembershipState(result)
          setMembershipError('')
          setMembershipLoading(false)
        }
      })
      .catch((error: unknown) => {
        if (!active) return
        setMembershipError(getErrorMessage(error))
        setMembershipLoading(false)
      })

    return () => {
      active = false
    }
  }, [hubId, membershipRevision])

  useEffect(() => {
    let active = true
    void hubsApi
      .getMembers(hubId, membersPage)
      .then((data) => {
        if (active) {
          setMembersResult({ page: membersPage, revision: membersRevision, data })
          setMembersFailure(null)
        }
      })
      .catch((error: unknown) => {
        if (!active) return
        setMembersFailure({
          page: membersPage,
          revision: membersRevision,
          message: getErrorMessage(error),
        })
      })

    return () => {
      active = false
    }
  }, [hubId, membersPage, membersRevision])

  useEffect(() => {
    if (!membershipState?.can_manage_members) return

    let active = true
    void hubsApi
      .getPendingRequests(hubId, requestsPage)
      .then((data) => {
        if (active) {
          setRequestsResult({
            page: requestsPage,
            revision: requestsRevision,
            data,
          })
          setRequestsFailure(null)
        }
      })
      .catch((error: unknown) => {
        if (!active) return
        setRequestsFailure({
          page: requestsPage,
          revision: requestsRevision,
          message: getErrorMessage(error),
        })
        if (axios.isAxiosError(error) && error.response?.status === 403) {
          setMembershipLoading(true)
          setMembershipRevision((previous) => previous + 1)
        }
      })

    return () => {
      active = false
    }
  }, [
    hubId,
    membershipState?.can_manage_members,
    requestsPage,
    requestsRevision,
  ])

  const refreshMembership = () => {
    setMembershipLoading(true)
    setMembershipError('')
    setMembershipRevision((previous) => previous + 1)
  }

  const refreshLists = (includeRequests = true) => {
    setMembersRevision((previous) => previous + 1)
    if (includeRequests && membershipState?.can_manage_members) {
      setRequestsRevision((previous) => previous + 1)
    }
  }

  const executeAction = async (
    key: string,
    action: () => Promise<void>,
  ) => {
    if (actionKey) return
    setActionKey(key)
    setActionError('')
    setActionSuccess('')
    try {
      await action()
    } catch (error) {
      setActionError(getErrorMessage(error))
      if (axios.isAxiosError(error) && error.response?.status === 403) {
        refreshMembership()
      }
    } finally {
      setActionKey('')
    }
  }

  const handleJoin = () => {
    void executeAction('join', async () => {
      const state = await hubsApi.joinHub(hubId)
      setMembershipState(state)
      refreshLists(false)
      setActionSuccess(
        state.membership?.status === 'approved'
          ? 'You joined this Hub.'
          : 'Your request to join was sent.',
      )
    })
  }

  const handleLeave = () => {
    void executeAction('leave', async () => {
      await hubsApi.leaveHub(hubId)
      refreshMembership()
      refreshLists()
      setActionSuccess('You left this Hub.')
    })
  }

  const handleInvite = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const username = inviteUsername.trim()
    if (!username || actionKey) return
    setInviteError('')
    void executeAction('invite', async () => {
      try {
        await hubsApi.inviteMember(hubId, username)
        setInviteUsername('')
        setActionSuccess(`@${username} was added to this Hub.`)
        refreshLists()
      } catch (error) {
        setInviteError(getErrorMessage(error))
        throw error
      }
    })
  }

  const handleReviewRequest = (
    member: HubMember,
    decision: 'approve' | 'reject',
  ) => {
    void executeAction(`${decision}:${member.id}`, async () => {
      if (decision === 'approve') {
        await hubsApi.approveMembershipRequest(hubId, member.id)
        setActionSuccess(`${displayName(member, true)} was approved.`)
        setMembersRevision((previous) => previous + 1)
      } else {
        await hubsApi.rejectMembershipRequest(hubId, member.id)
        setActionSuccess(`${displayName(member, true)} was declined.`)
      }
      setRequestsRevision((previous) => previous + 1)
      refreshMembership()
    })
  }

  const handleRoleChange = (member: HubMember) => {
    const role = roleDrafts[member.id] ?? member.role
    if (!isAssignableRole(role) || role === member.role) return
    void executeAction(`role:${member.id}`, async () => {
      await hubsApi.updateMemberRole(hubId, member.id, role)
      setActionSuccess(`${displayName(member)}'s role was updated to ${roleLabel(role)}.`)
      setRoleDrafts((previous) => {
        const next = { ...previous }
        delete next[member.id]
        return next
      })
      refreshLists(false)
    })
  }

  const handleRemoveMember = (member: HubMember) => {
    void executeAction(`remove:${member.id}`, async () => {
      await hubsApi.removeMember(hubId, member.id)
      setActionSuccess(`${displayName(member)} was removed from this Hub.`)
      refreshLists(false)
    })
  }

  const currentMembers =
    membersResult?.page === membersPage &&
    membersResult.revision === membersRevision
      ? membersResult.data
      : null
  const currentMembersError =
    membersFailure?.page === membersPage &&
    membersFailure.revision === membersRevision
      ? membersFailure.message
      : ''
  const membersLoading = !currentMembers && !currentMembersError

  const currentRequests =
    requestsResult?.page === requestsPage &&
    requestsResult.revision === requestsRevision
      ? requestsResult.data
      : null
  const currentRequestsError =
    requestsFailure?.page === requestsPage &&
    requestsFailure.revision === requestsRevision
      ? requestsFailure.message
      : ''
  const requestsLoading =
    Boolean(membershipState?.can_manage_members) &&
    !currentRequests &&
    !currentRequestsError

  const isOwner = membershipState?.membership?.role === 'owner'
  const isManager = membershipState?.can_manage_members === true
  const canInvite = isManager
  const canSeeManagement = isManager

  return (
    <section
      className="hub-membership-panel"
      aria-labelledby="hub-membership-title"
    >
      <header className="hub-membership-header">
        <div>
          <span className="hub-membership-eyebrow">THE COMMUNITY</span>
          <h2 id="hub-membership-title">Hub membership</h2>
          <p>Meet the people building this space together.</p>
        </div>
        {currentMembers && (
          <span className="hub-members-count">
            {currentMembers.count} {currentMembers.count === 1 ? 'member' : 'members'}
          </span>
        )}
      </header>

      <div className="hub-membership-status" aria-busy={membershipLoading}>
        {membershipLoading && !membershipState && (
          <p role="status">Checking your membership...</p>
        )}
        {membershipError && (
          <div className="hub-membership-inline-error" role="alert">
            <span>{membershipError}</span>
            <button type="button" onClick={refreshMembership}>Retry</button>
          </div>
        )}
        {!membershipLoading && !membershipError && membershipState && (
          <>
            <div className="hub-membership-status-copy">
              <span className="hub-membership-status-icon" aria-hidden="true">
                {membershipState.membership?.status === 'approved' ? '✓' : '＋'}
              </span>
              <div>
                <strong>
                  {membershipState.membership?.status === 'approved'
                    ? `${roleLabel(membershipState.membership.role)}`
                    : membershipState.membership?.status === 'pending'
                      ? 'Request pending'
                      : 'Join this Hub'}
                </strong>
                <span>
                  {membershipState.membership?.status === 'approved'
                    ? 'You are part of this community.'
                    : membershipState.membership?.status === 'pending'
                      ? 'The Hub team will review your request.'
                      : membershipState.membership_policy === 'open'
                        ? 'Membership is open to everyone.'
                        : 'Your request will be reviewed by the Hub team.'}
                </span>
              </div>
            </div>

            <div className="hub-membership-status-actions">
              {membershipState.membership?.status === 'pending' && (
                <span className="hub-membership-pending-badge">
                  Request Pending
                </span>
              )}
              {membershipState.membership?.status !== 'pending' &&
                membershipState.membership?.status !== 'approved' && (
                  <button
                    className="hub-membership-primary-button"
                    type="button"
                    onClick={handleJoin}
                    disabled={Boolean(actionKey)}
                  >
                    {actionKey === 'join'
                      ? 'Submitting...'
                      : membershipState.membership_policy === 'open'
                        ? 'Join Hub'
                        : 'Request to Join'}
                  </button>
                )}
              {membershipState.can_leave && !isOwner && (
                <button
                  className="hub-membership-secondary-button"
                  type="button"
                  onClick={handleLeave}
                  disabled={Boolean(actionKey)}
                >
                  {actionKey === 'leave' ? 'Leaving...' : 'Leave Hub'}
                </button>
              )}
            </div>
          </>
        )}
      </div>

      {(actionError || actionSuccess) && (
        <div
          className={`hub-membership-feedback${actionError ? ' is-error' : ' is-success'}`}
          role={actionError ? 'alert' : 'status'}
        >
          {actionError || actionSuccess}
        </div>
      )}

      <div className={`hub-community-grid${canSeeManagement ? ' has-management' : ''}`}>
        <section
          className="hub-members-section"
          aria-labelledby="hub-members-title"
          aria-busy={membersLoading}
        >
          <div className="hub-members-section-heading">
            <div>
              <span className="hub-membership-eyebrow">APPROVED MEMBERS</span>
              <h3 id="hub-members-title">Community</h3>
            </div>
          </div>

          {membersLoading && (
            <p className="hub-membership-list-state" role="status">
              Loading members...
            </p>
          )}
          {currentMembersError && (
            <div className="hub-membership-list-state is-error" role="alert">
              <p>{currentMembersError}</p>
              <button
                type="button"
                onClick={() => setMembersRevision((previous) => previous + 1)}
              >
                Retry
              </button>
            </div>
          )}
          {currentMembers && currentMembers.results.length === 0 && (
            <p className="hub-membership-list-state">
              No approved members yet. Be the first to join.
            </p>
          )}
          {currentMembers && currentMembers.results.length > 0 && (
            <div className="hub-member-list">
              {currentMembers.results.map((member) => {
                const isSelf = member.id === membershipState?.membership?.id
                const canManageTarget =
                  canSeeManagement &&
                  !isSelf &&
                  member.role !== 'owner' &&
                  (isOwner ||
                    member.role === 'member' ||
                    member.role === 'editor')
                const role = roleDrafts[member.id] ?? member.role
                const name = displayName(member)

                return (
                  <article className="hub-member-row" key={member.id}>
                    <MemberAvatar member={member} />
                    <div className="hub-member-identity">
                      {member.username ? (
                        <Link to={`/users/${encodeURIComponent(member.username)}`}>
                          {name}
                        </Link>
                      ) : (
                        <strong>{name}</strong>
                      )}
                      {member.username && (
                        <span>@{member.username}</span>
                      )}
                    </div>
                    <span className={`hub-role-badge role-${member.role}`}>
                      {roleLabel(member.role)}
                    </span>

                    {canManageTarget && (
                      <div className="hub-member-actions">
                        <label
                          className="hub-visually-hidden"
                          htmlFor={`hub-role-${member.id}`}
                        >
                          Change role for {name}
                        </label>
                        <select
                          id={`hub-role-${member.id}`}
                          value={role}
                          onChange={(event) => {
                            const nextRole = event.currentTarget.value
                            if (isAssignableRole(nextRole)) {
                              setRoleDrafts((previous) => ({
                                ...previous,
                                [member.id]: nextRole,
                              }))
                            }
                          }}
                          disabled={Boolean(actionKey)}
                        >
                          {isOwner && <option value="admin">Admin</option>}
                          <option value="editor">Editor</option>
                          <option value="member">Member</option>
                        </select>
                        <button
                          type="button"
                          onClick={() => handleRoleChange(member)}
                          disabled={Boolean(actionKey) || role === member.role}
                          aria-label={`Save role for ${name}`}
                        >
                          {actionKey === `role:${member.id}` ? 'Saving...' : 'Save'}
                        </button>
                        <button
                          className="hub-member-remove-button"
                          type="button"
                          onClick={() => handleRemoveMember(member)}
                          disabled={Boolean(actionKey)}
                        >
                          {actionKey === `remove:${member.id}` ? 'Removing...' : 'Remove'}
                        </button>
                      </div>
                    )}
                  </article>
                )
              })}
            </div>
          )}

          {currentMembers && (currentMembers.previous || currentMembers.next) && (
            <nav className="hub-members-pagination" aria-label="Member pages">
              <button
                type="button"
                disabled={!currentMembers.previous || Boolean(actionKey)}
                onClick={() => setMembersPage(currentMembers.previous || 1)}
              >
                Previous
              </button>
              <span>Page {membersPage}</span>
              <button
                type="button"
                disabled={!currentMembers.next || Boolean(actionKey)}
                onClick={() => setMembersPage(currentMembers.next || membersPage)}
              >
                Next
              </button>
            </nav>
          )}
        </section>

        {canSeeManagement && (
          <aside className="hub-member-management">
            {canInvite && (
              <section className="hub-management-card">
                <span className="hub-membership-eyebrow">GROW THE COMMUNITY</span>
                <h3>Invite a member</h3>
                <p>Add an existing BYB user by username.</p>
                <form onSubmit={handleInvite}>
                  <label htmlFor="hub-invite-username">BYB username</label>
                  <div className="hub-invite-controls">
                    <input
                      id="hub-invite-username"
                      name="username"
                      value={inviteUsername}
                      onChange={(event) => {
                        setInviteUsername(event.currentTarget.value)
                        setInviteError('')
                      }}
                      maxLength={150}
                      autoComplete="off"
                      placeholder="Enter username"
                      required
                    />
                    <button
                      type="submit"
                      disabled={!inviteUsername.trim() || Boolean(actionKey)}
                    >
                      {actionKey === 'invite' ? 'Adding...' : 'Invite'}
                    </button>
                  </div>
                  {inviteError && (
                    <span className="hub-invite-error" role="alert">
                      {inviteError}
                    </span>
                  )}
                </form>
              </section>
            )}

            <section
              className="hub-management-card"
              aria-labelledby="hub-requests-title"
              aria-busy={requestsLoading}
            >
              <div className="hub-requests-heading">
                <div>
                  <span className="hub-membership-eyebrow">FOR OWNERS & ADMINS</span>
                  <h3 id="hub-requests-title">Join requests</h3>
                </div>
                {membershipState?.pending_request_count !== null &&
                  membershipState?.pending_request_count !== undefined && (
                    <span className="hub-requests-count">
                      {membershipState.pending_request_count}
                    </span>
                  )}
              </div>

              {requestsLoading && (
                <p className="hub-membership-list-state" role="status">
                  Loading requests...
                </p>
              )}
              {currentRequestsError && (
                <div className="hub-membership-list-state is-error" role="alert">
                  <p>{currentRequestsError}</p>
                  <button
                    type="button"
                    onClick={() => setRequestsRevision((previous) => previous + 1)}
                  >
                    Retry
                  </button>
                </div>
              )}
              {currentRequests && currentRequests.results.length === 0 && (
                <p className="hub-membership-list-state">
                  No pending join requests.
                </p>
              )}
              {currentRequests && currentRequests.results.length > 0 && (
                <div className="hub-request-list">
                  {currentRequests.results.map((member) => {
                    const name = displayName(member, true)
                    return (
                      <article className="hub-request-row" key={member.id}>
                        <MemberAvatar member={member} pending />
                        <div className="hub-member-identity">
                          <strong>{name}</strong>
                          {member.username && <span>@{member.username}</span>}
                        </div>
                        <div className="hub-request-actions">
                          <button
                            type="button"
                            onClick={() => handleReviewRequest(member, 'approve')}
                            disabled={Boolean(actionKey)}
                          >
                            {actionKey === `approve:${member.id}` ? 'Approving...' : 'Approve'}
                          </button>
                          <button
                            className="hub-request-reject"
                            type="button"
                            onClick={() => handleReviewRequest(member, 'reject')}
                            disabled={Boolean(actionKey)}
                          >
                            {actionKey === `reject:${member.id}` ? 'Declining...' : 'Reject'}
                          </button>
                        </div>
                      </article>
                    )
                  })}
                </div>
              )}
              {currentRequests &&
                (currentRequests.previous || currentRequests.next) && (
                  <nav
                    className="hub-members-pagination"
                    aria-label="Join request pages"
                  >
                    <button
                      type="button"
                      disabled={!currentRequests.previous || Boolean(actionKey)}
                      onClick={() =>
                        setRequestsPage(currentRequests.previous || 1)
                      }
                    >
                      Previous
                    </button>
                    <span>Page {requestsPage}</span>
                    <button
                      type="button"
                      disabled={!currentRequests.next || Boolean(actionKey)}
                      onClick={() =>
                        setRequestsPage(currentRequests.next || requestsPage)
                      }
                    >
                      Next
                    </button>
                  </nav>
                )}
            </section>
          </aside>
        )}
      </div>
    </section>
  )
}
