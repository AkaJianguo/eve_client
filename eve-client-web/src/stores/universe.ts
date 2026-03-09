import { defineStore } from 'pinia'

import request from '@/utils/request'

type NameCache = Record<number, string>

export const useUniverseStore = defineStore('universe', {
  state: () => ({
    nameCache: {} as NameCache,
  }),
  actions: {
    async resolveIds(ids: number[]) {
      const pendingIds = ids.filter((id) => !this.nameCache[id])
      if (pendingIds.length === 0) {
        return
      }

      try {
        const data = await request.post('/universe/names', { ids: pendingIds })
        this.nameCache = { ...this.nameCache, ...(data.data as NameCache) }
      } catch (error) {
        console.error('ID 解析失败:', error)
      }
    },
    getName(id: number) {
      return this.nameCache[id] || `ID: ${id}`
    },
  },
})