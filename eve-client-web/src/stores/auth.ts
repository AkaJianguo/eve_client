import { defineStore } from 'pinia'

type CharacterSummary = {
  id?: number
  name?: string
} | null

type UserSummary = {
  userId: number
  subLevel?: number
  isActive?: boolean
} | null

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('eve_access_token') || null,
    character: null as CharacterSummary,
    user: null as UserSummary,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem('eve_access_token', token)
    },
    setCharacter(character: CharacterSummary) {
      this.character = character
    },
    setUser(user: UserSummary) {
      this.user = user
    },
    setSession(payload: { token: string; userId?: number; characterName?: string }) {
      this.setToken(payload.token)
      if (payload.userId) {
        this.user = { userId: payload.userId }
      }
      if (payload.characterName) {
        this.character = { ...this.character, name: payload.characterName }
      }
    },
    logout() {
      this.token = null
      this.character = null
      this.user = null
      localStorage.removeItem('eve_access_token')
    },
  },
})