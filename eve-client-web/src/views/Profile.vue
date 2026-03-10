<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'

import request from '@/utils/request'
import { useUniverseStore } from '@/stores/universe'

interface Character {
  id: number
  name: string
  corporation_id?: number
  alliance_id?: number
  security_status?: number
  birthday?: string
}

interface UserResponse {
  sub_level?: number
  last_login_at?: string
  characters?: Character[]
  character?: Character
  id?: number
  name?: string
  corporation_id?: number
  alliance_id?: number
  security_status?: number
  birthday?: string
}

const message = useMessage()
const universeStore = useUniverseStore()

const loading = ref(true)
const user = ref<UserResponse | null>(null)
const character = ref<Character | null>(null)

const fetchProfile = async () => {
  loading.value = true
  try {
    const res = (await request.get('/users/me')) as UserResponse
    user.value = res
    character.value = res.characters?.[0] || res.character || (res as Character)

    const idsToResolve: number[] = []
    if (character.value.corporation_id) idsToResolve.push(character.value.corporation_id)
    if (character.value.alliance_id) idsToResolve.push(character.value.alliance_id)

    if (idsToResolve.length > 0) {
      await universeStore.resolveIds(idsToResolve)
    }
  } catch (error) {
    console.error('档案读取失败:', error)
    message.error('无法读取克隆体档案，请检查神经元连接')
  } finally {
    loading.value = false
  }
}

const secStatusClass = (sec: number | undefined | null) => {
  if (sec === undefined || sec === null) return ''
  if (sec < -1.9) return 'text-danger'
  if (sec > 1.9) return 'text-safe'
  return 'text-neutral'
}

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '未知'
  return new Date(dateStr).toISOString().replace('T', ' ').substring(0, 19)
}

onMounted(() => {
  fetchProfile()
})
</script>

<template>
  <div class="profile-container">
    <n-spin :show="loading" stroke="#00fefe">
      <n-card v-if="character" class="pilot-card" :bordered="false">
        <div class="pilot-header">
          <div class="portrait-wrapper">
            <img
              :src="`https://images.evetech.net/characters/${character.id}/portrait?size=256`"
              class="pilot-portrait"
              alt="Pilot Portrait"
            />
            <div class="online-status"></div>
          </div>

          <div class="pilot-title">
            <h1 class="pilot-name">{{ character.name }}</h1>
            <div v-if="character.corporation_id" class="corp-info">
              <img
                :src="`https://images.evetech.net/corporations/${character.corporation_id}/logo?size=32`"
                class="corp-logo"
              />
              <span class="corp-name">{{ universeStore.getName(character.corporation_id) }}</span>
              <span v-if="character.alliance_id" class="alliance-name">
                [ {{ universeStore.getName(character.alliance_id) }} ]
              </span>
            </div>
          </div>
        </div>

        <n-divider dashed />

        <n-descriptions label-placement="left" :column="2" bordered class="pilot-details">
          <n-descriptions-item label="安全等级">
            <span :class="secStatusClass(character.security_status)">
              {{ character.security_status?.toFixed(2) || '0.00' }}
            </span>
          </n-descriptions-item>
          <n-descriptions-item label="出舱日期 (UTC)">
            {{ formatDate(character.birthday) }}
          </n-descriptions-item>
          <n-descriptions-item label="系统权限层级">
            <n-tag type="info" size="small" :bordered="false">Level {{ user?.sub_level || 2 }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="最后同步时间">
            {{ formatDate(user?.last_login_at) }}
          </n-descriptions-item>
        </n-descriptions>
      </n-card>
    </n-spin>
  </div>
</template>

<style lang="scss" scoped>
@import '@/assets/styles/variables.scss';

.profile-container {
  max-width: 800px;
  margin: 0 auto;
}

.pilot-card {
  background-color: $eve-bg-card;
  border: 1px solid $eve-border;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.pilot-header {
  display: flex;
  align-items: center;
  gap: 24px;
}

.portrait-wrapper {
  position: relative;
  width: 128px;
  height: 128px;
  border: 2px solid $eve-border;
  border-radius: 4px;
  background-color: #000;

  .pilot-portrait {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .online-status {
    position: absolute;
    bottom: 4px;
    right: 4px;
    width: 12px;
    height: 12px;
    background-color: $eve-cyan;
    border-radius: 50%;
    box-shadow: 0 0 8px $eve-cyan;
  }
}

.pilot-title {
  flex: 1;

  .pilot-name {
    margin: 0 0 8px 0;
    color: $eve-text-main;
    font-size: 28px;
    letter-spacing: 1px;
  }

  .corp-info {
    display: flex;
    align-items: center;
    gap: 8px;
    color: $eve-armor-yellow;
    font-weight: 500;

    .corp-logo {
      width: 24px;
      height: 24px;
      border-radius: 2px;
    }

    .alliance-name {
      color: #888;
      font-family: monospace;
    }
  }
}

:deep(.n-descriptions) {
  --n-th-color: #0a0c10 !important;
  --n-td-color: #14181f !important;
  --n-border-color: #2a2f3a !important;
  --n-th-text-color: #888 !important;
  --n-td-text-color: #e0e0e0 !important;
}

.text-danger {
  color: $eve-hull-red;
  font-weight: bold;
}

.text-safe {
  color: $eve-cyan;
  font-weight: bold;
}

.text-neutral {
  color: $eve-text-main;
}
</style>
