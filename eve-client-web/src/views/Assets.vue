<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import axios from 'axios'
import {
  NAlert,
  NButton,
  NCard,
  NDataTable,
  NEmpty,
  NInput,
  NSelect,
  useMessage,
  type DataTableColumns,
} from 'naive-ui'

import EveImage from '@/components/EveImage.vue'
import { useUniverseStore } from '@/stores/universe'
import request from '@/utils/request'

type AssetRow = {
  item_id?: number
  type_id?: number
  quantity?: number
  name?: string
  location_id?: number
  location_name?: string
  location_flag?: string
  location_type?: string
  is_blueprint_copy?: boolean
  is_singleton?: boolean
  type_name?: string
}

type AssetsResponse = {
  assets?: AssetRow[]
  asset_count?: number
  page?: number
  page_size?: number
  total_count?: number
  summary?: {
    blueprint_count?: number
    singleton_count?: number
    total_quantity?: number
  }
}

const message = useMessage()
const universeStore = useUniverseStore()

const loading = ref(false)
const assets = ref<AssetRow[]>([])
const assetPage = ref(1)
const assetPageSize = ref(100)
const assetTotal = ref(0)
const assetSummary = ref({
  blueprint_count: 0,
  singleton_count: 0,
  total_quantity: 0,
})
const assetKeyword = ref('')
const assetKind = ref<'all' | 'blueprint' | 'regular'>('all')
const errorMessage = ref('')

const assetKindOptions = [
  { label: '全部资产', value: 'all' },
  { label: '蓝图相关', value: 'blueprint' },
  { label: '普通物资', value: 'regular' },
]

function extractAssetsErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status
    const serverMessage = typeof error.response?.data?.message === 'string'
      ? error.response.data.message
      : ''

    if (status === 401) {
      return '登录状态已失效，或当前角色尚未重新授权资产权限，请重新登录 EVE SSO。'
    }

    if (status === 502) {
      return serverMessage || '资产上游 ESI 接口暂时不可用，请稍后重试。'
    }

    if (error.code === 'ECONNABORTED') {
      return '资产扫描耗时较长，当前请求已超时，请稍后重试。'
    }

    if (serverMessage) {
      return serverMessage
    }
  }

  return '资产数据读取失败，请稍后重试。'
}

async function fetchAssets() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await request.get<AssetsResponse, AssetsResponse>('/assets/me', {
      timeout: 30000,
      params: {
        page: assetPage.value,
        page_size: assetPageSize.value,
      },
    })
    assets.value = Array.isArray(response?.assets) ? response.assets : []
    assetTotal.value = typeof response?.total_count === 'number' ? response.total_count : assets.value.length
    assetSummary.value = {
      blueprint_count: response?.summary?.blueprint_count ?? 0,
      singleton_count: response?.summary?.singleton_count ?? 0,
      total_quantity: response?.summary?.total_quantity ?? 0,
    }

    const idsToResolve = new Set<number>()
    for (const item of assets.value) {
      if (typeof item.type_id === 'number') {
        idsToResolve.add(item.type_id)
      }
      if (typeof item.location_id === 'number') {
        idsToResolve.add(item.location_id)
      }
    }

    if (idsToResolve.size > 0) {
      await universeStore.resolveIds(Array.from(idsToResolve))
    }
  } catch (error) {
    console.error('资产读取失败:', error)
    errorMessage.value = extractAssetsErrorMessage(error)
    message.error('无法扫描货舱阵列')
  } finally {
    loading.value = false
  }
}

async function handleAssetPageChange(page: number) {
  assetPage.value = page
  await fetchAssets()
}

async function handleAssetPageSizeChange(pageSize: number) {
  assetPageSize.value = pageSize
  assetPage.value = 1
  await fetchAssets()
}

const filteredAssets = computed(() => {
  const keyword = assetKeyword.value.trim().toLowerCase()

  return assets.value.filter((item) => {
    const matchesKeyword = !keyword || [
      item.type_name,
      item.location_name,
      item.location_flag,
      typeof item.type_id === 'number' ? universeStore.getName(item.type_id) : '',
      typeof item.location_id === 'number' ? universeStore.getName(item.location_id) : '',
    ].some((value) => String(value).toLowerCase().includes(keyword))

    const matchesKind = assetKind.value === 'all'
      || (assetKind.value === 'blueprint' && item.is_blueprint_copy)
      || (assetKind.value === 'regular' && !item.is_blueprint_copy)

    return matchesKeyword && matchesKind
  })
})

function normalizeAssetName(value?: string) {
  const text = (value ?? '').trim()
  if (!text || text.toLowerCase() === 'none' || text === '-') {
    return ''
  }
  return text
}

function getAssetDisplayName(row: AssetRow) {
  const fromName = normalizeAssetName(row.name)
  const fromTypeName = normalizeAssetName(row.type_name)
  const fromUniverse = typeof row.type_id === 'number'
    ? normalizeAssetName(universeStore.getName(row.type_id))
    : ''

  return fromName || fromTypeName || fromUniverse || `Type #${row.type_id ?? '--'}`
}

const columns: DataTableColumns<AssetRow> = [
  {
    title: '物品',
    key: 'type_id',
    render(row) {
      return h('div', {
        style: {
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          minWidth: 0,
        },
      }, [
        h(EveImage, {
          typeId: row.type_id ?? 0,
          category: row.is_blueprint_copy ? 'bp' : 'icon',
          size: 32,
        }),
        h('span', {
          style: {
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          },
        }, getAssetDisplayName(row)),
      ])
    },
  },
  {
    title: '数量',
    key: 'quantity',
    align: 'right',
    render: (row) => new Intl.NumberFormat('en-US').format(row.quantity ?? 0),
  },
//   {
//     title: '位置',
//     key: 'location_id',
//     render: (row) =>
//       h(
//         'span',
//         { class: 'text-location' },
//         row.location_name || (typeof row.location_id === 'number' ? universeStore.getName(row.location_id) : '--'),
//       ),
//   },
//   {
//     title: '状态',
//     key: 'location_flag',
//     render: (row) =>
//       h(NTag, { size: 'small', bordered: false, type: 'info' }, { default: () => row.location_flag || 'unknown' }),
//   },
//   {
//     title: '位置类型',
//     key: 'location_type',
//     render: (row) => row.location_type || '--',
//   },
]

function assetRowKey(row: AssetRow) {
  return String(row.item_id ?? `${row.type_id ?? 'unknown'}-${row.location_id ?? 'unknown'}-${row.quantity ?? 0}`)
}

onMounted(() => {
  fetchAssets()
})
</script>

<template>
  <div class="assets-container">
    <n-card title="安全库房资产总览" :bordered="false" class="assets-card">
      <template #header-extra>
        <n-button type="primary" ghost :loading="loading" @click="fetchAssets">
          刷新传感器
        </n-button>
      </template>

      <div class="toolbar">
        <n-input v-model:value="assetKeyword" placeholder="搜索物品、位置或状态" clearable />
        <n-select v-model:value="assetKind" :options="assetKindOptions" class="kind-select" />
      </div>

      <n-alert v-if="errorMessage" type="warning" :show-icon="false" class="warn-box">
        {{ errorMessage }}
      </n-alert>

      <div class="stats-grid">
        <n-card class="stat-card" :bordered="false">
          <div class="stat-label">蓝图条目</div>
          <div class="stat-value">{{ assetSummary.blueprint_count }}</div>
        </n-card>
        <n-card class="stat-card" :bordered="false">
          <div class="stat-label">唯一实例</div>
          <div class="stat-value">{{ assetSummary.singleton_count }}</div>
        </n-card>
        <n-card class="stat-card" :bordered="false">
          <div class="stat-label">数量总和</div>
          <div class="stat-value">{{ new Intl.NumberFormat('en-US').format(assetSummary.total_quantity) }}</div>
        </n-card>
      </div>

      <div class="summary">当前筛选命中 {{ filteredAssets.length }} 条，本接口总量 {{ assetTotal }} 条</div>

      <n-data-table
        v-if="filteredAssets.length > 0"
        :columns="columns"
        :data="filteredAssets"
        :row-key="assetRowKey"
        :loading="loading"
        :bordered="false"
        striped
        :remote="true"
        :pagination="{
          page: assetPage,
          pageSize: assetPageSize,
          itemCount: assetTotal,
          showSizePicker: true,
          pageSizes: [50, 100, 200, 500],
          onUpdatePage: handleAssetPageChange,
          onUpdatePageSize: handleAssetPageSizeChange,
        }"
      />
      <n-empty v-else-if="!loading" description="当前没有可展示的资产记录" class="empty-box" />
    </n-card>
  </div>
</template>

<style lang="scss" scoped>
@import '@/assets/styles/variables.scss';

.assets-container {
  max-width: 1200px;
  margin: 0 auto;
}

.assets-card {
  background-color: $eve-bg-card;
  border: 1px solid $eve-border;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.kind-select {
  width: 180px;
}

.warn-box {
  margin-bottom: 16px;
}

.summary {
  margin-bottom: 12px;
  color: #96a2b8;
  font-size: 13px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  background-color: rgba(10, 12, 16, 0.8);
  border: 1px solid $eve-border;
}

.stat-label {
  color: #96a2b8;
  font-size: 12px;
  letter-spacing: 0.08em;
}

.stat-value {
  margin-top: 8px;
  color: $eve-text-main;
  font-size: 24px;
  font-weight: 700;
}

.empty-box {
  padding: 32px 0;
}

.item-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  color: $eve-text-main;
  font-weight: 500;
}

.item-meta {
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  min-width: 0;

  span {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  small {
    color: #96a2b8;
    font-size: 12px;
    font-weight: 400;
    white-space: nowrap;
  }
}

.text-location {
  color: $eve-armor-yellow;
  font-family: monospace;
  font-size: 13px;
}

:deep(.n-data-table) {
  --n-th-color: #0a0c10 !important;
  --n-td-color: #14181f !important;
  --n-border-color: #2a2f3a !important;
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>