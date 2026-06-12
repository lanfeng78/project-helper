import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref('')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  function setTokens({ access_token, refresh_token }) {
    accessToken.value = access_token
    refreshToken.value = refresh_token
    if (refresh_token) {
      localStorage.setItem('refresh_token', refresh_token)
    }
  }

  function clear() {
    user.value = null
    accessToken.value = ''
    refreshToken.value = ''
    localStorage.removeItem('refresh_token')
  }

  async function login(email, password) {
    const data = await authApi.login(email, password)
    setTokens(data)
    user.value = data.user
  }

  async function registerUser(username, email, password) {
    const data = await authApi.register(username, email, password)
    setTokens(data)
    user.value = data.user
  }

  async function tryRefresh() {
    if (!refreshToken.value) return false
    try {
      const data = await authApi.refresh(refreshToken.value)
      setTokens(data)
      return true
    } catch {
      clear()
      return false
    }
  }

  async function tryRestoreSession() {
    if (!refreshToken.value) return false
    try {
      const data = await authApi.refresh(refreshToken.value)
      setTokens(data)
      const me = await authApi.fetchMe(data.access_token)
      user.value = me.user
      return true
    } catch {
      clear()
      return false
    }
  }

  async function logout() {
    try { await authApi.logout() } catch {}
    clear()
  }

  return {
    user, accessToken, refreshToken,
    login, registerUser, logout,
    tryRestoreSession, tryRefresh, clear
  }
})
