import axios from 'axios'
import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import {
  hubsApi,
  type HubDetail,
  type HubType,
} from '../../services/hubsApi'
import HubEditModal from './HubEditModal'
import HubMembershipPanel from './HubMembershipPanel'
import HubEventManagement from '../events/components/HubEventManagement'
import './hub-detail.css'

const CATEGORY_LABELS: Record<HubType, string> = {
  company: 'Company',
  organisation: 'Organisation',
  college: 'College',
  college_club: 'College Club',
  college_department: 'College Department',
  community: 'Community',
}

type HubDetailState =
  | { status: 'loading'; hubId: string | undefined }
  | { status: 'error'; hubId: string }
  | { status: 'notFound'; hubId: string | undefined }
  | { status: 'success'; hubId: string; hub: HubDetail }

function formatCreatedAt(createdAt: string): string | null {
  const date = new Date(createdAt)
  if (Number.isNaN(date.getTime())) return null

  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date)
}

function HubDetailContent({ hub }: { hub: HubDetail }) {
  const createdDate = formatCreatedAt(hub.created_at)

  return (
    <article className="hub-detail-card">
      <div className="hub-detail-cover">
        {hub.cover_image && (
          <img
            src={hub.cover_image}
            alt=""
            loading="lazy"
            onError={(event) => {
              event.currentTarget.style.visibility = 'hidden'
            }}
          />
        )}
        <div className="hub-detail-cover-shade" />
        <span className="hub-detail-cover-mark" aria-hidden="true">
          BYB
        </span>
      </div>

      <div className="hub-detail-body">
        <header className="hub-detail-identity">
          <div className="hub-detail-logo" aria-hidden="true">
            {hub.logo && (
              <img
                src={hub.logo}
                alt=""
                loading="lazy"
                onError={(event) => {
                  event.currentTarget.style.visibility = 'hidden'
                }}
              />
            )}
            <span>{hub.name.trim().charAt(0).toUpperCase() || 'H'}</span>
          </div>

          <div className="hub-detail-heading">
            <span className="hub-detail-category">
              {CATEGORY_LABELS[hub.hub_type]}
            </span>
            <div className="hub-detail-title-line">
              <h1 id="hub-detail-title">{hub.name}</h1>
              {hub.is_verified && (
                <span
                  className="hub-detail-verified"
                  role="img"
                  aria-label="Verified Hub"
                  title="Verified Hub"
                >
                  <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                    <path
                      d="m5 10 3.2 3.2L15.5 6"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </span>
              )}
            </div>
            {hub.short_description.trim() && (
              <p className="hub-detail-short-description">
                {hub.short_description}
              </p>
            )}
          </div>
        </header>

        <div className="hub-detail-sections">
          <section
            className="hub-detail-description"
            aria-labelledby="hub-about-title"
          >
            <span className="hub-detail-eyebrow">ABOUT THIS SPACE</span>
            <h2 id="hub-about-title">About {hub.name}</h2>
            <p>
              {hub.description.trim() ||
                'No full description has been added yet.'}
            </p>
          </section>

          <aside className="hub-detail-information" aria-label="Hub information">
            <h2>Hub information</h2>
            <dl>
              {hub.city.trim() && (
                <div>
                  <dt>Location</dt>
                  <dd>{hub.city}</dd>
                </div>
              )}
              {hub.college_or_parent_organisation.trim() && (
                <div>
                  <dt>College or parent organisation</dt>
                  <dd>{hub.college_or_parent_organisation}</dd>
                </div>
              )}
              {hub.website.trim() && (
                <div>
                  <dt>Website</dt>
                  <dd>
                    <a
                      href={hub.website}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {hub.website}
                    </a>
                  </dd>
                </div>
              )}
              {createdDate && (
                <div>
                  <dt>Created</dt>
                  <dd>
                    <time dateTime={hub.created_at}>{createdDate}</time>
                  </dd>
                </div>
              )}
            </dl>
          </aside>
        </div>
      </div>
    </article>
  )
}

export default function HubDetailPage() {
  const { hubId } = useParams<{ hubId: string }>()
  const pendingRequests = useRef(new Map<string, Promise<HubDetail>>())
  const [retryCount, setRetryCount] = useState(0)
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [canHostEvent, setCanHostEvent] = useState(false)
  const [state, setState] = useState<HubDetailState>({
    status: 'loading',
    hubId,
  })

  useEffect(() => {
    let isCurrentRequest = true
    const requestKey = JSON.stringify([hubId, retryCount])

    const loadHub = async () => {
      setState({ status: 'loading', hubId })

      if (!hubId) {
        setState({ status: 'notFound', hubId })
        return
      }

      let request = pendingRequests.current.get(requestKey)
      if (!request) {
        request = hubsApi.getHub(hubId)
        pendingRequests.current.set(requestKey, request)
      }

      try {
        const hub = await request
        if (isCurrentRequest) {
          setState({ status: 'success', hubId, hub })
        }
      } catch (requestError) {
        if (!isCurrentRequest) return

        if (axios.isAxiosError(requestError) && requestError.response?.status === 404) {
          setState({ status: 'notFound', hubId })
        } else {
          console.error('Hub detail loading failed:', requestError)
          setState({ status: 'error', hubId })
        }
      } finally {
        if (pendingRequests.current.get(requestKey) === request) {
          pendingRequests.current.delete(requestKey)
        }
      }
    }

    void loadHub()

    return () => {
      isCurrentRequest = false
    }
  }, [hubId, retryCount])

  useEffect(() => {
    let active = true

    async function loadMembership() {
      if (!hubId) {
        setCanHostEvent(false)
        return
      }

      try {
        const membershipState = await hubsApi.getMembership(hubId)
        if (!active) return

        const role = membershipState.membership?.role
        const status = membershipState.membership?.status
        setCanHostEvent(
          status === 'approved' &&
            (role === 'owner' ||
              role === 'admin' ||
              role === 'editor'),
        )
      } catch {
        if (active) setCanHostEvent(false)
      }
    }

    void loadMembership()

    return () => {
      active = false
    }
  }, [hubId])

  const isCurrentState = state.hubId === hubId

  const refreshHubAfterPermissionError = async () => {
    if (!hubId) return
    try {
      const hub = await hubsApi.getHub(hubId)
      setState((current) =>
        current.hubId === hubId && current.status === 'success'
          ? { status: 'success', hubId, hub }
          : current,
      )
    } catch (requestError) {
      if (axios.isAxiosError(requestError) && requestError.response?.status === 404) {
        setState({ status: 'notFound', hubId })
      } else {
        console.error('Hub detail refresh failed:', requestError)
      }
    }
  }

  const handleHubUpdated = (hub: HubDetail) => {
    setState({ status: 'success', hubId: hub.id, hub })
    setIsEditOpen(false)
  }

  return (
    <section
      className="hub-detail-page"
      aria-labelledby="hub-detail-title"
      aria-busy={!isCurrentState || state.status === 'loading'}
    >
      <div className="hub-detail-toolbar">
        <Link className="hub-detail-back-link" to="/hubs">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path
              d="M15.5 10H4.5m0 0 5-5m-5 5 5 5"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span>Back to Hubs</span>
        </Link>
        {isCurrentState &&
          state.status === 'success' &&
          state.hub.can_edit && (
            <button
              className="hub-detail-edit-button"
              type="button"
              onClick={() => setIsEditOpen(true)}
            >
              Edit Hub
            </button>
          )}
        {isCurrentState &&
          state.status === 'success' &&
          canHostEvent && (
            <Link
              className="hub-detail-edit-button"
              to={`/hubs/${state.hub.id}/events/create`}
            >
              + Host an Event
            </Link>
          )}
      </div>

      {(!isCurrentState || state.status === 'loading') && (
        <div className="hub-detail-state" role="status">
          <span className="hub-detail-loader" aria-hidden="true" />
          <h1 id="hub-detail-title">Loading Hub</h1>
          <p>Loading Hub details...</p>
        </div>
      )}

      {isCurrentState && state.status === 'error' && (
        <div className="hub-detail-state hub-detail-error" role="alert">
          <span className="hub-detail-state-mark" aria-hidden="true">
            !
          </span>
          <h1 id="hub-detail-title">Hub unavailable</h1>
          <p>We couldn't load this Hub. Please try again.</p>
          <button
            type="button"
            onClick={() => setRetryCount((previous) => previous + 1)}
          >
            Try again
          </button>
        </div>
      )}

      {isCurrentState && state.status === 'notFound' && (
        <div className="hub-detail-state" role="status">
          <span className="hub-detail-state-mark" aria-hidden="true">
            H
          </span>
          <h1 id="hub-detail-title">Hub not found</h1>
          <p>This Hub may no longer be available or the link may be incorrect.</p>
        </div>
      )}

      {isCurrentState && state.status === 'success' && (
        <>
          <HubDetailContent hub={state.hub} />
          <HubMembershipPanel key={state.hub.id} hubId={state.hub.id} />
          {canHostEvent && <HubEventManagement key={`events-${state.hub.id}`} hubId={state.hub.id} />}
        </>
      )}
      {isCurrentState &&
        state.status === 'success' &&
        isEditOpen && (
          <HubEditModal
            hub={state.hub}
            canEdit={state.hub.can_edit}
            onClose={() => setIsEditOpen(false)}
            onUpdated={handleHubUpdated}
            onPermissionError={() => void refreshHubAfterPermissionError()}
          />
        )}
    </section>
  )
}
