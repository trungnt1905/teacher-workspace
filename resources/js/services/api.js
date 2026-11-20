import axios from 'axios'
import { SLOW_AFTER_MS, useUiStore } from '../stores/ui'

// The SPA is served by Laravel, so /api is always same-origin (no proxy, no CORS).
// Laravel sets the XSRF-TOKEN cookie; axios echoes it in X-XSRF-TOKEN on every write request.
const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  withXSRFToken: true,
  headers: { Accept: 'application/json' },
})

let onUnauthenticated = () => {}

/** Called by the router setup: where to go when the session has ended. */
export function setUnauthenticatedHandler(handler) {
  onUnauthenticated = handler
}

api.interceptors.request.use((config) => {
  const ui = useUiStore()
  config.slowTimer = setTimeout(() => {
    config.markedSlow = true
    ui.slowRequests++
  }, SLOW_AFTER_MS)
  return config
})

function settle(config) {
  if (!config) return
  clearTimeout(config.slowTimer)
  if (config.markedSlow) useUiStore().slowRequests--
}

api.interceptors.response.use(
  (response) => {
    settle(response.config)
    return response
  },
  (error) => {
    settle(error.config)
    if (error.response?.status === 401 && !error.config?.skipAuthRedirect) onUnauthenticated()
    return Promise.reject(error)
  },
)

/** { code, message, details } from any failure, with a Vietnamese message the teacher can act on. */
export function apiError(error) {
  const body = error?.response?.data?.error
  if (body?.code) return { code: body.code, message: body.message, details: body.details ?? {} }
  if (!error?.response) {
    return { code: 'NETWORK_ERROR', message: 'Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.', details: {} }
  }
  return { code: 'SERVER_ERROR', message: 'Có lỗi hệ thống, vui lòng thử lại.', details: {} }
}

/** First field-level validation message if any, else the error message. */
export function errorText(err) {
  const first = Object.values(err.details ?? {}).flat().find((v) => typeof v === 'string')
  return err.code === 'VALIDATION_FAILED' && first ? first : err.message
}

export default api

export async function getHealth() {
  const { data } = await api.get('/health')
  return data
}
