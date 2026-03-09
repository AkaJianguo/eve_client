<script setup lang="ts">
import { computed, h, onMounted, ref, useCssModule } from 'vue'
import { NAlert, NButton, NCard, NDataTable, NInput, NSelect, NSkeleton, NTag, type DataTableColumns } from 'naive-ui'

import EveImage from '@/components/EveImage.vue'
import request from '@/utils/request'

const styles = useCssModule()

type IndustryRow = {
  key: string
  activityId?: number
  blueprintTypeId: number
  blueprintName: string
  productTypeId: number
  productName: string
  facilityName: string
  runs: number
  endDate: string
  installerName?: string
  status: 'active' | 'ready' | 'paused' | 'delivered' | 'cancelled' | 'unknown'
}

type IndustryJobApiItem = {
  job_id?: number
  activity_id?: number
  blueprint_type_id?: number
  blueprint_name?: string
  product_type_id?: number
  product_name?: string
  facility_name?: string
  runs?: number
  end_date?: string
  installer_name?: string
  status?: string
}

type IndustryJobsResponse = {
  jobs?: IndustryJobApiItem[]
}

const filterText = ref('')
const statusFilter = ref('all')
const loading = ref(false)
const errorMessage = ref('')

const statusOptions = [
  { label: '全部状态', value: 'all' },
  { label: '进行中', value: 'active' },
  { label: '可交付', value: 'ready' },
  { label: '已暂停', value: 'paused' },
  { label: '已交付', value: 'delivered' },
]

const jobs = ref<IndustryRow[]>([])

function formatEta(value?: string) {
  if (!value) {
    return '--'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function normalizeStatus(status?: string): IndustryRow['status'] {
  if (status === 'active' || status === 'ready' || status === 'paused' || status === 'delivered' || status === 'cancelled') {
    return status
  }
  return 'unknown'
}

async function fetchIndustryJobs() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await request.get<IndustryJobsResponse, IndustryJobsResponse>('/industry/jobs/me', {
      params: {
        include_completed: statusFilter.value !== 'active',
      },
    })

    jobs.value = (response.jobs ?? []).map((job) => ({
      key: String(job.job_id ?? crypto.randomUUID()),
      activityId: typeof job.activity_id === 'number' ? job.activity_id : undefined,
      blueprintTypeId: typeof job.blueprint_type_id === 'number' ? job.blueprint_type_id : 0,
      blueprintName: typeof job.blueprint_name === 'string' ? job.blueprint_name : '未知蓝图',
      productTypeId: typeof job.product_type_id === 'number' ? job.product_type_id : 0,
      productName: typeof job.product_name === 'string' ? job.product_name : '未知产物',
      facilityName: typeof job.facility_name === 'string' ? job.facility_name : '未知设施',
      runs: typeof job.runs === 'number' ? job.runs : 0,
      endDate: formatEta(typeof job.end_date === 'string' ? job.end_date : undefined),
      installerName: typeof job.installer_name === 'string' ? job.installer_name : undefined,
      status: normalizeStatus(typeof job.status === 'string' ? job.status : undefined),
    }))
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.message || '工业工单读取失败，请确认已完成 SSO 授权并且后端服务正常。'
    jobs.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchIndustryJobs)

const filteredJobs = computed(() =>
  jobs.value.filter((job) => {
    const keyword = filterText.value.trim().toLowerCase()
    const matchesKeyword =
      keyword.length === 0 ||
      job.blueprintName.toLowerCase().includes(keyword) ||
      job.productName.toLowerCase().includes(keyword) ||
      job.facilityName.toLowerCase().includes(keyword)

    const matchesStatus = statusFilter.value === 'all' || job.status === statusFilter.value
    return matchesKeyword && matchesStatus
  }),
)

const columns: DataTableColumns<IndustryRow> = [
  {
    title: '蓝图',
    key: 'blueprint',
    render: (row) =>
      h('div', { class: styles.assetCell }, [
        h(EveImage, { typeId: row.blueprintTypeId, size: 40 }),
        h('div', { class: styles.assetMeta }, [
          h('strong', row.blueprintName),
          h('span', `Type ID ${row.blueprintTypeId}`),
        ]),
      ]),
  },
  {
    title: '产出物',
    key: 'product',
    render: (row) =>
      h('div', { class: styles.assetCell }, [
        h(EveImage, { typeId: row.productTypeId, size: 40 }),
        h('div', { class: styles.assetMeta }, [
          h('strong', row.productName),
          h('span', `Type ID ${row.productTypeId}`),
        ]),
      ]),
  },
  { title: '设施', key: 'facilityName' },
  { title: '执行人', key: 'installerName', render: (row) => row.installerName || '--' },
  { title: '批次', key: 'runs' },
  { title: 'ETA', key: 'endDate' },
  {
    title: '状态',
    key: 'status',
    render: (row) => {
      const type = row.status === 'active'
        ? 'info'
        : row.status === 'ready'
          ? 'success'
          : row.status === 'paused'
            ? 'warning'
            : row.status === 'delivered'
              ? 'default'
              : 'error'
      const labelMap: Record<IndustryRow['status'], string> = {
        active: '进行中',
        ready: '可交付',
        paused: '已暂停',
        delivered: '已交付',
        cancelled: '已取消',
        unknown: '未知',
      }
      const label = labelMap[row.status]
      return h(NTag, { type, bordered: false }, { default: () => label })
    },
  },
]
</script>

<template>
  <div :class="$style.page">
    <div :class="$style.header">
      <div>
        <div :class="$style.kicker">Industrial Operations</div>
        <h1 :class="$style.title">工业监控</h1>
      </div>
      <div :class="$style.controls">
        <n-input v-model:value="filterText" placeholder="搜索蓝图 / 产出物 / 设施" clearable />
        <n-select v-model:value="statusFilter" :options="statusOptions" :class="$style.select" />
        <n-button tertiary type="primary" @click="fetchIndustryJobs">刷新工单</n-button>
      </div>
    </div>

    <n-card title="工业蓝图队列">
      <n-alert v-if="errorMessage" type="error" :show-icon="false" :class="$style.error">
        {{ errorMessage }}
      </n-alert>
      <n-skeleton v-if="loading" text :repeat="6" />
      <n-data-table v-else :columns="columns" :data="filteredJobs" :pagination="false" />
    </n-card>
  </div>
</template>

<style module lang="scss">
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
  flex-wrap: wrap;
}

.kicker {
  margin-bottom: 8px;
  color: var(--eve-cyan);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.title {
  margin: 0;
  font-size: clamp(28px, 4vw, 40px);
}

.controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.select {
  width: 180px;
}

.error {
  margin-bottom: 12px;
}

.assetCell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.assetMeta {
  display: flex;
  flex-direction: column;
  gap: 4px;

  strong {
    font-size: 13px;
    font-weight: 600;
  }

  span {
    color: rgba(224, 224, 224, 0.56);
    font-size: 11px;
  }
}
</style>