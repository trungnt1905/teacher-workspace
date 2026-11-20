import { defineStore } from 'pinia'

// Shows "Đang khởi động máy chủ…" when an API call is slow (Render cold start, §10.4).
export const SLOW_AFTER_MS = 6000

export const useUiStore = defineStore('ui', {
  state: () => ({ slowRequests: 0 }),
  getters: {
    serverWaking: (state) => state.slowRequests > 0,
  },
})
