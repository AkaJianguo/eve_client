<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, shallowRef } from 'vue'
import { NButton, NCard, NEmpty, NSelect, NSpin, useMessage } from 'naive-ui'
import * as echarts from 'echarts'

import request from '@/utils/request'

type MarketHistoryItem = {
  date: string
  average: number
  highest: number
  lowest: number
  volume: number
  order_count: number
}

const message = useMessage()
const loading = ref(false)
const selectedTypeId = ref<number | null>(34)
const chartRef = ref<HTMLDivElement | null>(null)
const chartInstance = shallowRef<echarts.ECharts | null>(null)
const historyRows = ref<MarketHistoryItem[]>([])

const hotItems = [
  { label: '三钛合金 (Tritanium)', value: 34 },
  { label: '同位素 (Isogen)', value: 37 },
  { label: '伊什塔级 (Ishtar)', value: 12005 },
  { label: '飞行员执照 (PLEX)', value: 44992 },
  { label: '水化液体 (Aqueous Liquids)', value: 2268 },
  { label: '多米尼克斯级 (Dominix)', value: 645 },
]

function calculateMA(dayCount: number, data: MarketHistoryItem[]) {
  const result: Array<string | number> = []
  for (let index = 0; index < data.length; index += 1) {
    if (index < dayCount - 1) {
      result.push('-')
      continue
    }

    let sum = 0
    for (let offset = 0; offset < dayCount; offset += 1) {
      sum += Number(data[index - offset]?.average ?? 0)
    }
    result.push(Number((sum / dayCount).toFixed(2)))
  }
  return result
}

function ensureChart() {
  if (!chartRef.value) {
    return null
  }

  if (!chartInstance.value) {
    chartInstance.value = echarts.init(chartRef.value, 'dark')
  }

  return chartInstance.value
}

function renderChart(data: MarketHistoryItem[]) {
  const instance = ensureChart()
  if (!instance) {
    return
  }

  const dates = data.map((item) => item.date)
  const averages = data.map((item) => item.average)
  const volumes = data.map((item) => item.volume)
  const ma5 = calculateMA(5, data)

  instance.setOption({
    backgroundColor: 'transparent',
    animationDuration: 500,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(10, 12, 16, 0.92)',
      borderColor: '#2a2f3a',
      textStyle: { color: '#e0e0e0' },
    },
    legend: {
      top: 8,
      data: ['平均价格', 'MA5', '成交量'],
      textStyle: { color: '#96a2b8' },
    },
    grid: [
      { left: '8%', right: '6%', top: 56, height: '48%' },
      { left: '8%', right: '6%', top: '68%', height: '20%' },
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#3b4350' } },
        axisLabel: { color: '#96a2b8', hideOverlap: true },
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        boundaryGap: true,
        axisLine: { lineStyle: { color: '#3b4350' } },
        axisLabel: { color: '#96a2b8', showMinLabel: false, showMaxLabel: false },
      },
    ],
    yAxis: [
      {
        name: '价格 (ISK)',
        type: 'value',
        gridIndex: 0,
        scale: true,
        axisLine: { show: false },
        axisLabel: {
          color: '#96a2b8',
          formatter: (value: number) => new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value),
        },
        splitLine: { lineStyle: { color: '#2a2f3a', type: 'dashed' } },
      },
      {
        name: '成交量',
        type: 'value',
        gridIndex: 1,
        axisLine: { show: false },
        axisLabel: {
          color: '#96a2b8',
          formatter: (value: number) => `${(value / 1000000).toFixed(1)}M`,
        },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 55, end: 100 },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        bottom: 12,
        height: 22,
        borderColor: '#2a2f3a',
        fillerColor: 'rgba(0, 254, 254, 0.12)',
        handleStyle: { color: '#00fefe', borderColor: '#00fefe' },
        dataBackground: {
          lineStyle: { color: '#3b4350' },
          areaStyle: { color: 'rgba(59, 67, 80, 0.3)' },
        },
        start: 55,
        end: 100,
      },
    ],
    series: [
      {
        name: '平均价格',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: averages,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: '#00fefe' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 254, 254, 0.28)' },
            { offset: 1, color: 'rgba(0, 254, 254, 0.02)' },
          ]),
        },
      },
      {
        name: 'MA5',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ma5,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1.5, type: 'dashed', color: '#f5c542' },
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.9)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.35)' },
          ]),
        },
      },
    ],
  })
}

async function fetchHistory() {
  if (!selectedTypeId.value) {
    return
  }

  loading.value = true
  try {
    const response = await request.get<MarketHistoryItem[], MarketHistoryItem[]>(`/market/history/${selectedTypeId.value}`)
    historyRows.value = Array.isArray(response) ? response : []

    if (historyRows.value.length > 0) {
      await nextTick()
      renderChart(historyRows.value)
    } else {
      ensureChart()?.clear()
      message.warning('无可用历史数据')
    }
  } catch (error) {
    console.error('市场数据获取失败:', error)
    message.error('无法连接到新伊甸商业储备银行')
  } finally {
    loading.value = false
  }
}

function handleResize() {
  chartInstance.value?.resize()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  fetchHistory()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance.value?.dispose()
  chartInstance.value = null
})
</script>

<template>
  <div class="market-container">
    <n-card title="新伊甸市场态势感知 (Jita 4-4)" :bordered="false" class="market-card">
      <template #header-extra>
        <div class="search-bar">
          <n-select
            v-model:value="selectedTypeId"
            :options="hotItems"
            filterable
            placeholder="检索物资档案..."
            class="item-select"
            @update:value="fetchHistory"
          />
          <n-button type="primary" ghost :loading="loading" @click="fetchHistory">
            扫描信号
          </n-button>
        </div>
      </template>

      <n-spin :show="loading" stroke="#00fefe">
        <div v-show="historyRows.length > 0" class="chart-wrapper">
          <div ref="chartRef" class="echarts-container"></div>
        </div>
        <n-empty v-if="historyRows.length === 0" description="当前物资暂无可用市场历史" class="empty-box" />
      </n-spin>
    </n-card>
  </div>
</template>

<style lang="scss" scoped>
@import '@/assets/styles/variables.scss';

.market-container {
  max-width: 1400px;
  margin: 0 auto;
}

.market-card {
  background:
    radial-gradient(circle at top right, rgba(0, 254, 254, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(20, 24, 31, 0.96) 0%, rgba(10, 12, 16, 0.98) 100%);
  border: 1px solid $eve-border;
}

.search-bar {
  display: flex;
  gap: 12px;
  width: min(100%, 520px);
}

.item-select {
  flex: 1;
}

.chart-wrapper {
  width: 100%;
  height: 620px;
  margin-top: 16px;
  padding: 8px;
  background: rgba(0, 0, 0, 0.18);
  border-radius: 8px;
  border: 1px solid #2a2f3a;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
}

.echarts-container {
  width: 100%;
  height: 100%;
}

.empty-box {
  padding: 72px 0;
}

@media (max-width: 900px) {
  .search-bar {
    width: 100%;
  }

  .chart-wrapper {
    height: 520px;
  }
}

@media (max-width: 640px) {
  .search-bar {
    flex-direction: column;
  }

  .chart-wrapper {
    height: 460px;
  }
}
</style>