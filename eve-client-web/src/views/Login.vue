<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NAlert, NButton, NCard, NFlex, NTag } from 'naive-ui'
import { ShieldCheck, Zap } from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

onMounted(() => {
  if (authStore.isAuthenticated) {
    router.replace('/dashboard')
  }
})

function handleSSOLogin() {
  window.location.href = '/api/v1/auth/login'
}
</script>

<template>
  <div :class="$style.page">
    <div :class="$style.backdrop"></div>
    <n-card :class="$style.panel" :bordered="false">
      <n-flex vertical :size="18">
        <div :class="$style.kicker">Industrial Data Relay</div>
        <div :class="$style.heading">EVE 工业数据管理工具</div>
        <div :class="$style.description">
          面向生产线、蓝图、工单与资产流向的单页指挥台。通过 EVE SSO 授权后接入角色工业权限。
        </div>

        <n-flex :size="8">
          <n-tag type="info" :bordered="false">Naive UI Console</n-tag>
          <n-tag type="warning" :bordered="false">High Density HUD</n-tag>
        </n-flex>

        <n-alert type="info" :show-icon="false" :bordered="false">
          当前接入流程为 EVE 官方 SSO。授权后会自动签发本站 JWT，并进入工业监控页面。
        </n-alert>

        <div :class="$style.actions">
          <n-button type="primary" size="large" :class="$style.primaryButton" @click="handleSSOLogin">
            <template #icon>
              <ShieldCheck :size="18" />
            </template>
            使用 EVE SSO 登录
          </n-button>
          <n-button quaternary size="large">
            <template #icon>
              <Zap :size="18" />
            </template>
            查看系统状态
          </n-button>
        </div>
      </n-flex>
    </n-card>
  </div>
</template>

<style module lang="scss">
.page {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: 24px;
}

.backdrop {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 20%, rgba(0, 254, 254, 0.12), transparent 25%),
    radial-gradient(circle at 80% 10%, rgba(245, 197, 66, 0.1), transparent 22%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 24%);
  pointer-events: none;
}

.panel {
  position: relative;
  z-index: 1;
  width: min(560px, 100%);
  background: rgba(20, 24, 31, 0.92);
  box-shadow:
    0 24px 60px rgba(0, 0, 0, 0.45),
    0 0 0 1px rgba(255, 255, 255, 0.04);
}

.kicker {
  color: var(--eve-cyan);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
}

.heading {
  font-size: clamp(28px, 4vw, 38px);
  font-weight: 800;
  line-height: 1.08;
}

.description {
  color: rgba(224, 224, 224, 0.72);
  line-height: 1.7;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.primaryButton {
  min-width: 220px;
}
</style>