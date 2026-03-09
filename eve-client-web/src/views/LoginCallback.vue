<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NCard, NResult, NSpin } from 'naive-ui'

import request from '@/utils/request'
import { useAuthStore } from '@/stores/auth'

type CurrentUserResponse = {
  user_id: number
  sub_level: number
  is_active: boolean
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

onMounted(async () => {
  const accessToken = typeof route.query.access_token === 'string' ? route.query.access_token : ''
  const characterName = typeof route.query.character_name === 'string' ? route.query.character_name : ''
  const userId = typeof route.query.user_id === 'string' ? Number(route.query.user_id) : undefined

  if (!accessToken) {
    await router.replace('/login')
    return
  }

  authStore.setSession({
    token: accessToken,
    userId,
    characterName,
  })

  try {
    const profile = await request.get<CurrentUserResponse, CurrentUserResponse>('/users/me')
    authStore.setUser({
      userId: profile.user_id,
      subLevel: profile.sub_level,
      isActive: profile.is_active,
    })
  } catch {
    // Let the request interceptor handle invalid sessions.
  }

  await router.replace('/dashboard')
})
</script>

<template>
  <div :class="$style.page">
    <n-card :class="$style.card" :bordered="false">
      <n-result status="info" title="正在接入 EVE 授权" description="正在写入令牌并同步用户状态，请稍候。">
        <template #icon>
          <n-spin size="large" />
        </template>
      </n-result>
    </n-card>
  </div>
</template>

<style module lang="scss">
.page {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: 24px;
}

.card {
  width: min(520px, 100%);
  background: rgba(20, 24, 31, 0.92);
}
</style>