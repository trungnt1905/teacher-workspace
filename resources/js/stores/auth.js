import { defineStore } from 'pinia'
import api from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({ user: null, checked: false }),
  getters: {
    loggedIn: (state) => state.user !== null,
  },
  actions: {
    /** Ask the server once per page load whether the session cookie is still valid. */
    async check() {
      if (this.checked) return
      try {
        const { data } = await api.get('/auth/me', { skipAuthRedirect: true })
        this.user = data.data
      } catch {
        this.user = null
      } finally {
        this.checked = true
      }
    },
    async login(email, password) {
      const { data } = await api.post('/auth/login', { email, password }, { skipAuthRedirect: true })
      this.user = data.data
      this.checked = true
    },
    async logout() {
      try {
        await api.post('/auth/logout', null, { skipAuthRedirect: true })
      } finally {
        this.user = null
      }
    },
    forget() {
      this.user = null
    },
  },
})
