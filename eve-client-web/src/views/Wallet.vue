<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import axios from 'axios'
import {
  NAlert,
  NCard,
  NDataTable,
  NEmpty,
  NInput,
  NSelect,
  NSpin,
  NTabPane,
  NTabs,
  NTag,
  useMessage,
  type DataTableColumns,
} from 'naive-ui'

import request from '@/utils/request'
import { translateRefType } from '@/utils/eve-dict'
import { useUniverseStore } from '@/stores/universe'

type WalletCacheStatus = 'hit_fresh' | 'stale_refreshing' | 'miss_refreshed'

type WalletBalanceResponse = {
  user_id?: number
  character_id?: number
  character_name?: string
  balance?: number
  updated_at?: string
  cache_status?: WalletCacheStatus
}

type WalletJournalResponse = {
  page?: number
  page_size?: number
  total_count?: number
  income_total?: number
  expense_total?: number
  cache_status?: WalletCacheStatus
  entries?: WalletJournalEntry[]
}

type WalletTransactionsResponse = {
  page?: number
  page_size?: number
  total_count?: number
  buy_count?: number
  sell_count?: number
  cache_status?: WalletCacheStatus
  transactions?: WalletTransactionEntry[]
}

type WalletJournalEntry = {
  id?: number | string
  date?: string
  ref_type?: string
  amount?: number
  balance?: number
  reason?: string | null
  description?: string | null
  first_party_name?: string
  second_party_name?: string
  context_id?: number
  context_id_type?: string | null
  context_name?: string
}

type WalletTransactionEntry = {
  transaction_id?: number | string
  date?: string
  type_id?: number
  location_id?: number
  unit_price?: number
  quantity?: number
  is_buy?: boolean
  type_name?: string
  location_name?: string
}

const message = useMessage()
const universeStore = useUniverseStore()

const loading = ref(false)
const balance = ref(0)
const journal = ref<WalletJournalEntry[]>([])
const transactions = ref<WalletTransactionEntry[]>([])
const journalPage = ref(1)
const journalPageSize = ref(50)
const journalTotal = ref(0)
const journalIncomeTotal = ref(0)
const journalExpenseTotal = ref(0)
const transactionPage = ref(1)
const transactionPageSize = ref(50)
const transactionTotal = ref(0)
const transactionBuyCount = ref(0)
const transactionSellCount = ref(0)
const walletKeyword = ref('')
const journalRefType = ref('all')
const transactionDirection = ref<'all' | 'buy' | 'sell'>('all')
const errorMessage = ref('')
const balanceCacheStatus = ref<WalletCacheStatus | null>(null)
const journalCacheStatus = ref<WalletCacheStatus | null>(null)
const transactionCacheStatus = ref<WalletCacheStatus | null>(null)

const directionOptions = [
  { label: '全部交易', value: 'all' },
  { label: '仅买入', value: 'buy' },
  { label: '仅卖出', value: 'sell' },
]

function formatIsk(amount?: number | null) {
  if (amount === undefined || amount === null) {
    return '0.00'
  }

  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

function formatDate(dateStr?: string) {
  if (!dateStr) {
    return '--'
  }

  const date = new Date(dateStr)
  if (Number.isNaN(date.getTime())) {
    return dateStr
  }

  return date.toLocaleString('zh-CN', {
    hour12: false,
  })
}

function formatJournalParties(entry: WalletJournalEntry) {
  const firstParty = entry.first_party_name || '--'
  const secondParty = entry.second_party_name || '--'
  return `${firstParty} -> ${secondParty}`
}

function extractWalletErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status
    const serverMessage = typeof error.response?.data?.message === 'string'
      ? error.response.data.message
      : ''

    if (status === 401) {
      return '登录状态已失效，或当前角色尚未重新授权钱包权限，请重新登录 EVE SSO。'
    }

    if (status === 502) {
      return serverMessage || '钱包上游 ESI 接口暂时不可用，请稍后重试。'
    }

    if (error.code === 'ECONNABORTED') {
      return '钱包数据读取超时，请稍后重试。'
    }

    if (serverMessage) {
      return serverMessage
    }
  }

  return '钱包数据读取失败，请稍后重试。'
}

function getCacheStatusMeta(scope: string, status: WalletCacheStatus | null) {
  if (!status) {
    return null
  }

  if (status === 'stale_refreshing') {
    return {
      scope,
      type: 'warning' as const,
      text: `${scope}当前显示缓存数据，后台正在刷新。`,
    }
  }

  if (status === 'miss_refreshed') {
    return {
      scope,
      type: 'info' as const,
      text: `${scope}刚完成冷启动刷新，数据已写入本地缓存。`,
    }
  }

  return {
    scope,
    type: 'success' as const,
    text: `${scope}当前命中新鲜缓存。`,
  }
}

async function fetchWalletData() {
  loading.value = true
  errorMessage.value = ''
  try {
    const balanceResponse = await request.get<WalletBalanceResponse, WalletBalanceResponse>('/wallet/balance')

    balance.value = typeof balanceResponse?.balance === 'number'
      ? balanceResponse.balance
      : Number(balanceResponse ?? 0)
    balanceCacheStatus.value = balanceResponse?.cache_status ?? null
    await Promise.all([fetchJournal(), fetchTransactions()])
  } catch (error) {
    console.error('钱包数据读取失败:', error)
    errorMessage.value = extractWalletErrorMessage(error)
    message.error('无法连接到新伊甸商业储备银行')
  } finally {
    loading.value = false
  }
}

async function fetchJournal() {
  try {
    const response = await request.get<WalletJournalResponse, WalletJournalResponse>('/wallet/journal', {
      params: {
        page: journalPage.value,
        page_size: journalPageSize.value,
      },
      timeout: 30000,
    })

    journal.value = Array.isArray(response?.entries) ? response.entries : []
    journalTotal.value = typeof response?.total_count === 'number' ? response.total_count : journal.value.length
    journalIncomeTotal.value = typeof response?.income_total === 'number' ? response.income_total : 0
    journalExpenseTotal.value = typeof response?.expense_total === 'number' ? response.expense_total : 0
    journalCacheStatus.value = response?.cache_status ?? null
  } catch (error) {
    console.error('读取日记失败:', error)
    errorMessage.value = extractWalletErrorMessage(error)
    // 让上层调用感知错误的同时也显示用户提示
    message.error(errorMessage.value || '读取日记失败')
    // 抛出以便在并发调用（如 fetchWalletData 的 Promise.all）中被捕获
    throw error
  }
}

async function fetchTransactions() {
  try {
    const response = await request.get<WalletTransactionsResponse, WalletTransactionsResponse>('/wallet/transactions', {
      params: {
        page: transactionPage.value,
        page_size: transactionPageSize.value,
      },
      timeout: 30000,
    })

    transactions.value = Array.isArray(response?.transactions) ? response.transactions : []
    transactionTotal.value = typeof response?.total_count === 'number' ? response.total_count : transactions.value.length
    transactionBuyCount.value = typeof response?.buy_count === 'number' ? response.buy_count : 0
    transactionSellCount.value = typeof response?.sell_count === 'number' ? response.sell_count : 0
    transactionCacheStatus.value = response?.cache_status ?? null
  } catch (error) {
    console.error('读取交易失败:', error)
    errorMessage.value = extractWalletErrorMessage(error)
    message.error(errorMessage.value || '读取交易失败')
    throw error
  }

  const idsToResolve = new Set<number>()
  for (const item of transactions.value) {
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
}

async function handleTransactionPageChange(page: number) {
  transactionPage.value = page
  loading.value = true
  try {
    await fetchTransactions()
  } finally {
    loading.value = false
  }
}

async function handleTransactionPageSizeChange(pageSize: number) {
  transactionPageSize.value = pageSize
  transactionPage.value = 1
  loading.value = true
  try {
    await fetchTransactions()
  } finally {
    loading.value = false
  }
}

const filteredJournal = computed(() => {
  const keyword = walletKeyword.value.trim().toLowerCase()

  const byType = journalRefType.value === 'all'
    ? journal.value
    : journal.value.filter((entry) => entry.ref_type === journalRefType.value)

  if (!keyword) {
    return byType
  }

  return byType.filter((entry) =>
    [entry.ref_type, translateRefType(entry.ref_type).label, entry.reason, entry.first_party_name, entry.second_party_name]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(keyword)),
  )
})

const journalRefTypeOptions = computed(() => {
  const values = Array.from(new Set(journal.value.map((entry) => entry.ref_type).filter(Boolean) as string[]))
  values.sort((a, b) => translateRefType(a).label.localeCompare(translateRefType(b).label, 'zh-CN'))
  return [
    { label: '全部流水类型', value: 'all' },
    ...values.map((value) => ({
      label: translateRefType(value).label,
      value,
    })),
  ]
})

const filteredTransactions = computed(() => {
  const keyword = walletKeyword.value.trim().toLowerCase()
  return transactions.value.filter((entry) => {
    const matchesKeyword = !keyword || [
      entry.type_name,
      entry.location_name,
      typeof entry.type_id === 'number' ? universeStore.getName(entry.type_id) : '',
      typeof entry.location_id === 'number' ? universeStore.getName(entry.location_id) : '',
    ].some((value) => String(value).toLowerCase().includes(keyword))

    const matchesDirection = transactionDirection.value === 'all'
      || (transactionDirection.value === 'buy' && entry.is_buy)
      || (transactionDirection.value === 'sell' && entry.is_buy === false)

    return matchesKeyword && matchesDirection
  })
})

const cacheStatusItems = computed(() => {
  return [
    getCacheStatusMeta('钱包余额', balanceCacheStatus.value),
    getCacheStatusMeta('财务日记', journalCacheStatus.value),
    getCacheStatusMeta('市场交易', transactionCacheStatus.value),
  ].filter(Boolean)
})

const cacheStatusAlertType = computed(() => {
  if (cacheStatusItems.value.some((item) => item?.type === 'warning')) {
    return 'warning' as const
  }

  if (cacheStatusItems.value.some((item) => item?.type === 'info')) {
    return 'info' as const
  }

  return 'success' as const
})

const cacheStatusTitle = computed(() => {
  if (cacheStatusAlertType.value === 'warning') {
    return '当前页面包含缓存回退数据'
  }

  if (cacheStatusAlertType.value === 'info') {
    return '当前页面已完成一次冷启动刷新'
  }

  return '当前页面命中新鲜缓存'
})

const journalColumns: DataTableColumns<WalletJournalEntry> = [
  {
    title: '时间',
    key: 'date',
    render: (row) => formatDate(row.date),
  },
  {
    title: '类型',
    key: 'ref_type',
    minWidth: 180,
    render: (row) => {
      const mapped = translateRefType(row.ref_type)
      return h(NTag, { size: 'small', bordered: false, type: mapped.type }, { default: () => mapped.label })
    },
  },
  {
    title: '对手方',
    key: 'parties',
    minWidth: 220,
    render: (row) => formatJournalParties(row),
  },
  {
    title: '金额 (ISK)',
    key: 'amount',
    align: 'right',
    render: (row) =>
      h(
        'span',
        { class: (row.amount ?? 0) > 0 ? 'text-income' : 'text-expense' },
        `${(row.amount ?? 0) > 0 ? '+' : ''}${formatIsk(row.amount)}`,
      ),
  },
  {
    title: '余额',
    key: 'balance',
    align: 'right',
    render: (row) => formatIsk(row.balance),
  },
  {
    title: '描述',
    key: 'description',
    minWidth: 280,
    render: (row) => row.description || '--',
  },
]

const transactionColumns: DataTableColumns<WalletTransactionEntry> = [
  {
    title: '时间',
    key: 'date',
    render: (row) => formatDate(row.date),
  },
  {
    title: '物品',
    key: 'type_id',
    render: (row) => row.type_name || (typeof row.type_id === 'number' ? universeStore.getName(row.type_id) : '--'),
  },
  {
    title: '单价',
    key: 'unit_price',
    align: 'right',
    render: (row) => formatIsk(row.unit_price),
  },
  {
    title: '数量',
    key: 'quantity',
    align: 'right',
    render: (row) => new Intl.NumberFormat('en-US').format(row.quantity ?? 0),
  },
  {
    title: '收支',
    key: 'is_buy',
    render: (row) =>
      h(
        NTag,
        { type: row.is_buy ? 'error' : 'success', size: 'small', bordered: false },
        { default: () => (row.is_buy ? '买入' : '卖出') },
      ),
  },
]

function rowKey(row: WalletJournalEntry) {
  return String(row.id)
}

onMounted(() => {
  fetchWalletData()
})
</script>

<template>
  <div class="wallet-container">
    <n-spin :show="loading" stroke="#00fefe">
      <n-card class="balance-card" :bordered="false">
        <div class="balance-header">当前可用克隆体资金 (ISK)</div>
        <div class="balance-amount">{{ formatIsk(balance) }}</div>
      </n-card>

      <div class="stats-grid">
        <n-card class="stat-card" :bordered="false">
          <div class="stat-label">日记收入</div>
          <div class="stat-value text-income">+ {{ formatIsk(journalIncomeTotal) }}</div>
        </n-card>
        <n-card class="stat-card" :bordered="false">
          <div class="stat-label">日记支出</div>
          <div class="stat-value text-expense">- {{ formatIsk(journalExpenseTotal) }}</div>
        </n-card>
        <n-card class="stat-card" :bordered="false">
          <div class="stat-label">买入单数</div>
          <div class="stat-value">{{ transactionBuyCount }}</div>
        </n-card>
        <n-card class="stat-card" :bordered="false">
          <div class="stat-label">卖出单数</div>
          <div class="stat-value">{{ transactionSellCount }}</div>
        </n-card>
      </div>

      <n-card class="detail-card" :bordered="false">
        <div class="toolbar">
          <n-input v-model:value="walletKeyword" placeholder="搜索类型、备注、对手方或物品" clearable />
          <n-select
            v-model:value="journalRefType"
            :options="journalRefTypeOptions"
            class="direction-select"
            placeholder="筛选流水类型"
          />
          <n-select v-model:value="transactionDirection" :options="directionOptions" class="direction-select" />
        </div>

        <n-alert v-if="errorMessage" type="warning" :show-icon="false" class="warn-box">
          {{ errorMessage }}
        </n-alert>

        <n-alert v-if="cacheStatusItems.length > 0" :type="cacheStatusAlertType" class="cache-box">
          <template #header>
            {{ cacheStatusTitle }}
          </template>
          <div class="cache-status-list">
            <div v-for="item in cacheStatusItems" :key="item.scope" class="cache-status-item">
              <n-tag size="small" :bordered="false" :type="item.type">
                {{ item.scope }}
              </n-tag>
              <span class="cache-status-text">{{ item.text }}</span>
            </div>
          </div>
        </n-alert>

        <n-tabs type="line" animated>
          <n-tab-pane name="journal" tab="财务日记 (Journal)">
            <div class="section-meta">当前筛选命中 {{ filteredJournal.length }} 条，本接口总量 {{ journalTotal }} 条</div>
            
            <div v-if="filteredJournal.length > 0" style="margin-top: 12px;">
              <n-data-table
                :columns="journalColumns"
                :data="filteredJournal"
                :row-key="rowKey"
                :bordered="false"
                :single-line="false"
                striped
                :scroll-x="1400"
              />
            </div>
            <n-empty v-else description="当前没有可展示的财务日记记录" class="empty-box" />
          </n-tab-pane>
          <n-tab-pane name="transactions" tab="市场交易 (Transactions)">
            <div class="section-meta">当前筛选命中 {{ filteredTransactions.length }} 条，本接口总量 {{ transactionTotal }} 条</div>
            <n-data-table
              v-if="filteredTransactions.length > 0"
              :columns="transactionColumns"
              :data="filteredTransactions"
              :bordered="false"
              striped
              :scroll-x="900"
              :remote="true"
              :pagination="{
                page: transactionPage,
                pageSize: transactionPageSize,
                itemCount: transactionTotal,
                showSizePicker: true,
                pageSizes: [20, 50, 100, 200],
                onUpdatePage: handleTransactionPageChange,
                onUpdatePageSize: handleTransactionPageSizeChange,
              }"
            />
            <n-empty v-else description="当前没有可展示的市场成交记录" class="empty-box" />
          </n-tab-pane>
        </n-tabs>
      </n-card>
    </n-spin>
  </div>
</template>

<style lang="scss" scoped>
@import '@/assets/styles/variables.scss';

.wallet-container {
  max-width: 1200px;
  margin: 0 auto;
}

.balance-card {
  background: linear-gradient(135deg, rgba(0, 254, 254, 0.12) 0%, $eve-bg-card 100%);
  border: 1px solid $eve-cyan;
  text-align: center;
  padding: 20px 0;
}

.balance-header {
  margin-bottom: 8px;
  color: #888;
  font-size: 16px;
  letter-spacing: 0.16em;
}

.balance-amount {
  color: $eve-cyan;
  font-size: clamp(36px, 5vw, 52px);
  font-weight: 700;
  font-family: monospace;
  text-shadow: 0 0 10px rgba(0, 254, 254, 0.3);
}

.detail-card {
  margin-top: 24px;
  background-color: $eve-bg-card;
  border: 1px solid $eve-border;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.stat-card {
  background-color: $eve-bg-card;
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

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.direction-select {
  width: 180px;
}

.warn-box {
  margin-bottom: 16px;
}

.cache-box {
  margin-bottom: 16px;
}

.cache-status-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cache-status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.cache-status-text {
  color: #c6d0e1;
  font-size: 13px;
}

.section-meta {
  margin-bottom: 12px;
  color: #96a2b8;
  font-size: 13px;
}

.empty-box {
  padding: 32px 0;
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.text-income {
  color: #00ff85;
  font-weight: 700;
}

.text-expense {
  color: $eve-hull-red;
  font-weight: 700;
}

:deep(.n-data-table) {
  --n-th-color: #0a0c10 !important;
  --n-td-color: #14181f !important;
  --n-border-color: #2a2f3a !important;
}

:deep(.n-tabs-nav) {
  margin-bottom: 12px;
}
</style>