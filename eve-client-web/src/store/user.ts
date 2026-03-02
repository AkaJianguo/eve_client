// src/store/user.ts
export const useUserStore = defineStore('user', {
  state: () => ({
    // 未来这里通过接口获取，现在直接写死为 true
    isPremium: true 
  })
})