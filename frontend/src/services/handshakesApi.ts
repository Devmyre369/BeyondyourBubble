import api from './api'

export type HandshakeStatus = 'pending' | 'accepted' | 'rejected' | 'cancelled'
export type HandshakeViewState =
  | 'none'
  | 'outgoing_pending'
  | 'incoming_pending'
  | 'connected'
  | 'self'

export interface HandshakePerson {
  id: string
  username: string
  first_name: string
  last_name: string
  profile_picture: string
  byb_signature: string | null
}

export interface HandshakeItem {
  id: string
  status: HandshakeStatus
  direction: 'incoming' | 'outgoing'
  person: HandshakePerson
  created_at: string
  responded_at: string | null
  cancelled_at: string | null
}

export interface HandshakeStatusResponse {
  state: HandshakeViewState
  request_id: string | null
  handshake: HandshakeItem | null
}

export interface HandshakePage {
  count: number
  next: number | null
  previous: number | null
  results: HandshakeItem[]
}

export const handshakesApi = {
  async getStatus(username: string): Promise<HandshakeStatusResponse> {
    const response = await api.get<HandshakeStatusResponse>(
      `/accounts/handshakes/status/${encodeURIComponent(username)}/`,
    )
    return response.data
  },

  async sendRequest(username: string): Promise<HandshakeStatusResponse> {
    const response = await api.post<{ state: HandshakeStatusResponse }>(
      '/accounts/handshakes/',
      { recipient_username: username },
    )
    return response.data.state
  },

  async getIncoming(page = 1): Promise<HandshakePage> {
    const response = await api.get<HandshakePage>('/accounts/handshakes/incoming/', { params: { page } })
    return response.data
  },

  async getOutgoing(page = 1): Promise<HandshakePage> {
    const response = await api.get<HandshakePage>('/accounts/handshakes/outgoing/', { params: { page } })
    return response.data
  },

  async getConnections(page = 1): Promise<HandshakePage> {
    const response = await api.get<HandshakePage>('/accounts/handshakes/connections/', { params: { page } })
    return response.data
  },

  async respond(id: string, decision: 'accept' | 'reject' | 'cancel'): Promise<void> {
    await api.post(`/accounts/handshakes/requests/${id}/${decision}/`)
  },

  async removeConnection(id: string): Promise<void> {
    await api.delete(`/accounts/handshakes/connections/${id}/`)
  },
}
