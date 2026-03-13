<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import {
  NCard,
  NDataTable,
  NEmpty,
  NLayout,
  NLayoutContent,
  NLayoutSider,
  NRadioButton,
  NRadioGroup,
  NSpin,
  NTag,
  NTree,
  useMessage,
  type DataTableColumns,
  type TreeOption,
} from 'naive-ui'

import EveTreeIconSource from '@/components/common/EveTreeIconSource.vue'
import request from '@/utils/request'

type MarketGroupNode = TreeOption & {
  key: string
  parent_key?: string | null
  name: string
  iconname?: string | null
  is_group: boolean
  type_id?: number | null
  children?: MarketGroupNode[]
}

const message = useMessage()
const TREE_REQUEST_TIMEOUT_MS = 120000
const ORDER_REQUEST_TIMEOUT_MS = 30000
const GLOBAL_MARKET_REGION_LABEL = '全局市场'
const GLOBAL_MARKET_ITEM_IDS = new Set([44992])

const loadingTree = ref(false)
const loadingOrders = ref(false)
const marketGroups = ref<MarketGroupNode[]>([])
const selectedRegion = ref(10000002)
const currentItem = ref<MarketGroupNode | null>(null)
const orderList = ref<MarketOrderRow[]>([])

type MarketOrderRow = {
  order_id: number
  is_buy_order: boolean
  price: number
  volume_remain: number
  location_id: number
  system_id: number
  location_name: string
  system_name: string
}

const tradeHubs = [
  { label: '吉他 (Jita)', value: 10000002 },
  { label: '艾玛 (Amarr)', value: 10000043 },
  { label: '多迪克斯 (Dodixie)', value: 10000032 },
  { label: '伦斯 (Rens)', value: 10000030 },
  { label: '赫克 (Hek)', value: 10000042 },
]

const normalizedTreeData = computed<TreeOption[]>(() => {
  function normalize(nodes: MarketGroupNode[]): TreeOption[] {
    return nodes.map((node) => {
      const normalizedNode: Record<string, unknown> = { ...node }
      if (Array.isArray(node.children) && node.children.length > 0) {
        normalizedNode.children = normalize(node.children)
      } else {
        delete normalizedNode.children
      }
      return normalizedNode as TreeOption
    })
  }

  return normalize(marketGroups.value)
})

const isGlobalMarketItem = computed(() => {
  const typeId = currentItem.value?.type_id
  return typeof typeId === 'number' && GLOBAL_MARKET_ITEM_IDS.has(typeId)
})

const orderColumns: DataTableColumns<MarketOrderRow> = [
  {
    title: '类型',
    key: 'is_buy_order',
    width: 92,
    render(row) {
      const isBuyOrder = row.is_buy_order
      return h(
        NTag,
        {
          bordered: false,
          type: isBuyOrder ? 'success' : 'error',
          size: 'small',
        },
        {
          default: () => (isBuyOrder ? '买单' : '卖单'),
        },
      )
    },
  },
  {
    title: '价格 (ISK)',
    key: 'price',
    width: 150,
    align: 'right',
    render(row) {
      return h(
        'span',
        { class: 'mono-cell' },
        row.price.toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }),
      )
    },
  },
  {
    title: '数量',
    key: 'volume_remain',
    width: 120,
    align: 'right',
    render(row) {
      return h('span', { class: 'mono-cell' }, row.volume_remain.toLocaleString('en-US'))
    },
  },
  {
    title: '星系',
    key: 'system_name',
    width: 120,
    render(row) {
      return h('span', { class: 'system-name-cell' }, row.system_name)
    },
  },
  {
    title: '空间站 / 星堡位置',
    key: 'location_name',
    render(row) {
      const isCitadel = row.location_name === '玩家星堡 (Citadel)'
      return h(
        'span',
        { class: isCitadel ? 'location-name-cell location-name-cell--citadel' : 'location-name-cell' },
        row.location_name,
      )
    },
  },
]

function getOrderRowKey(row: MarketOrderRow) {
  return row.order_id
}

function renderTreeIcon({ option }: { option: TreeOption }) {
  const node = option as MarketGroupNode
  if (!node.iconname) {
    return null
  }

  return h(EveTreeIconSource, {
    iconName: node.iconname,
    alt: node.name,
  })
}

function treeNodeProps({ option }: { option: TreeOption }) {
  const node = option as MarketGroupNode

  return {
    onClick() {
      if (!node.is_group && node.type_id) {
        currentItem.value = node
        fetchMarketOrders()
      }
    },
  }
}

async function fetchMarketGroups() {
  loadingTree.value = true
  try {
    const response = await request.get<MarketGroupNode[], MarketGroupNode[]>('/sde/market-groups/tree', {
      timeout: TREE_REQUEST_TIMEOUT_MS,
    })
    marketGroups.value = Array.isArray(response) ? response : []
  } catch (error) {
    console.error('市场分类树加载失败:', error)
    message.error('市场分类树数据量较大，读取超时或失败，请稍后重试')
  } finally {
    loadingTree.value = false
  }
}

async function fetchMarketOrders() {
  if (!currentItem.value?.type_id) {
    return
  }

  loadingOrders.value = true
  orderList.value = []

  try {
    const response = await request.get<MarketOrderRow[], MarketOrderRow[]>(`/market/orders/${currentItem.value.type_id}`, {
      params: { region_id: selectedRegion.value },
      timeout: ORDER_REQUEST_TIMEOUT_MS,
    })

    orderList.value = Array.isArray(response) ? response : []
  } catch (error) {
    console.error('市场订单读取失败:', error)
    message.error('无法读取当前星域实时盘口')
  } finally {
    loadingOrders.value = false
  }
}

function handleRegionChange() {
  if (currentItem.value) {
    fetchMarketOrders()
  }
}

onMounted(() => {
  fetchMarketGroups()
})
</script>

<template>
  <div class="market-browser-container">
    <n-card class="main-card" :bordered="false" content-style="padding: 0;">
      <n-layout has-sider class="market-layout">
        <n-layout-sider bordered collapse-mode="width" :width="320" class="sider-panel">
          <div class="sider-header">市场分类目录</div>
          <n-spin :show="loadingTree" class="tree-spin">
            <n-tree
              block-line
              expand-on-click
              :data="normalizedTreeData"
              key-field="key"
              label-field="name"
              children-field="children"
              :render-prefix="renderTreeIcon"
              :node-props="treeNodeProps"
              class="eve-tree"
            />
          </n-spin>
        </n-layout-sider>

        <n-layout-content class="content-panel">
          <div class="region-toolbar">
            <n-radio-group v-model:value="selectedRegion" size="medium" @update:value="handleRegionChange">
              <n-radio-button v-for="hub in tradeHubs" :key="hub.value" :value="hub.value">
                {{ hub.label }}
              </n-radio-button>
            </n-radio-group>

            <div v-if="currentItem" class="current-target">
              正在扫描: <span class="highlight">{{ currentItem.name }}</span>
              (ID: {{ currentItem.type_id }})
            </div>
            <div v-else class="current-target">点击左侧物品节点后加载对应星域盘口。</div>
          </div>

          <div v-if="isGlobalMarketItem" class="global-market-notice">
            该物品已自动切换到{{ GLOBAL_MARKET_REGION_LABEL }}。
          </div>

          <div class="table-container">
            <n-data-table
              :columns="orderColumns"
              :data="orderList"
              :row-key="getOrderRowKey"
              :loading="loadingOrders"
              :bordered="false"
              striped
              class="market-table"
            >
              <template #empty>
                <n-empty description="请选择左侧具体物品节点以加载实时盘口" />
              </template>
            </n-data-table>
          </div>
        </n-layout-content>
      </n-layout>
    </n-card>
  </div>
</template>

<style lang="scss" scoped>
@use '../assets/styles/variables.scss' as *;

.market-browser-container {
  height: calc(100vh - 100px);
  max-width: 1600px;
  margin: 0 auto;
}

.main-card {
  height: 100%;
  background-color: $eve-bg-dark;
  border: 1px solid $eve-border;
}

.market-layout {
  height: 100%;
}

.sider-panel {
  display: flex;
  flex-direction: column;
  background-color: rgba(20, 24, 31, 0.94);
}

.sider-header {
  padding: 16px;
  font-size: 16px;
  font-weight: 700;
  color: $eve-cyan;
  border-bottom: 1px solid $eve-border;
}

.tree-spin {
  height: calc(100% - 58px);
}

.eve-tree {
  height: 100%;
  padding: 12px;
  overflow: auto;
  --n-node-height: 34px !important;
  --n-node-text-color: #a7b1c2 !important;
  --n-node-text-color-hover: #00fefe !important;
  --n-node-text-color-pressed: #00fefe !important;
  --n-node-text-color-active: #00fefe !important;
  --n-node-color-hover: rgba(0, 254, 254, 0.08) !important;
  --n-node-color-active: rgba(0, 254, 254, 0.12) !important;
  --n-node-color-active-hover: rgba(0, 254, 254, 0.14) !important;
}

.content-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background:
    radial-gradient(circle at top left, rgba(0, 254, 254, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(20, 24, 31, 0.96) 0%, rgba(10, 12, 16, 0.98) 100%);
}

.region-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 20px;
  border: 1px solid $eve-border;
  border-radius: 4px;
  background-color: rgba(20, 24, 31, 0.6);
}

.current-target {
  font-size: 14px;
  color: #8893a7;
}

.highlight {
  color: $eve-cyan;
  font-weight: 700;
}

.global-market-notice {
  padding: 10px 14px;
  border: 1px solid rgba(230, 162, 60, 0.35);
  border-radius: 4px;
  background: linear-gradient(90deg, rgba(230, 162, 60, 0.16) 0%, rgba(230, 162, 60, 0.05) 100%);
  color: #f0c674;
  font-size: 14px;
  font-weight: 600;
}

.table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  border: 1px solid $eve-border;
  border-radius: 4px;
  background-color: rgba(20, 24, 31, 0.94);
}

.market-table {
  height: 100%;

  :deep(.n-data-table-th) {
    background-color: #0a0c10 !important;
    color: #8893a7;
    font-weight: 700;
  }

  :deep(.n-data-table-td) {
    background-color: #14181f !important;
    color: #d6deeb;
  }
}

.mono-cell {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 14px;
}

.system-name-cell {
  color: #e6a23c;
  font-weight: 700;
}

.location-name-cell {
  color: #cfd7e6;
}

.location-name-cell--citadel {
  color: #8893a7;
  font-style: italic;
}

@media (max-width: 960px) {
  .market-browser-container {
    height: auto;
    min-height: calc(100vh - 100px);
  }

  .market-layout {
    display: block;
  }

  .sider-panel {
    width: 100%;
    height: 420px;
  }

  .region-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>