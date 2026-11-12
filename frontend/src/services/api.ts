
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const accessToken = sessionStorage.getItem('byb_access_token')

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }

  // Allow Axios to automatically set multipart/form-data
  // with the correct boundary when uploading files.
  if (
    typeof FormData !== 'undefined' &&
    config.data instanceof FormData
  ) {
    config.headers.delete('Content-Type')
  }

  return config
})

export default api
