<script setup lang="ts">
import { h } from 'vue'
import { NCard, NDataTable, NGrid, NGridItem, NProgress, NStatistic, NTag, NThing, NTimeline, NTimelineItem, type DataTableColumns } from 'naive-ui'

type QueueRow = {
  key: string
  line: string
  status: 'RUNNING' | 'PAUSED' | 'RISK'
  efficiency: string
  eta: string
}

const queueColumns: DataTableColumns<QueueRow> = [
  { title: '生产线', key: 'line' },
  {
    title: '状态',
    key: 'status',
    render: (row) => {
      const type = row.status === 'RUNNING' ? 'success' : row.status === 'PAUSED' ? 'warning' : 'error'
      return h(NTag, { type, bordered: false }, { default: () => row.status })
    },
  },
  { title: '效率', key: 'efficiency' },
  { title: '预计完成', key: 'eta' },
]

const queueData: QueueRow[] = [
  { key: '1', line: 'Tatara Alpha - Missile Wing', status: 'RUNNING', efficiency: '97.2%', eta: '03h 24m' },
  { key: '2', line: 'Azbel Beta - Hull Replication', status: 'PAUSED', efficiency: '61.8%', eta: '12h 40m' },
  { key: '3', line: 'Raitaru Gamma - Reaction Chain', status: 'RISK', efficiency: '44.1%', eta: '01h 05m' },
]
</script>

<template>
  <div :class="$style.page">
    <div :class="$style.hero">
      <div>
        <div :class="$style.kicker">Command Overview</div>
        <h1 :class="$style.title">工业指挥控制台</h1>
        <p :class="$style.subtitle">聚合工厂产线、反应链、蓝图效率与交付风险的高信息密度总览。</p>
      </div>
      <n-card :class="$style.statusCard">
        <n-thing title="Cluster Integrity" description="Tranquility industrial relay">
          <template #header-extra>
            <n-tag type="success" :bordered="false">ONLINE</n-tag>
          </template>
          <n-progress type="line" :percentage="92" indicator-placement="inside" processing />
        </n-thing>
      </n-card>
    </div>

    <n-grid :cols="24" :x-gap="16" :y-gap="16" responsive="screen">
      <n-grid-item :span="24" :m-span="8">
        <n-card>
          <n-statistic label="激活产线" value="18">
            <template #suffix>条</template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item :span="24" :m-span="8">
        <n-card>
          <n-statistic label="日均产出" value="12.4">
            <template #suffix>B ISK</template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item :span="24" :m-span="8">
        <n-card>
          <n-statistic label="异常工单" value="3">
            <template #suffix>项</template>
          </n-statistic>
        </n-card>
      </n-grid-item>

      <n-grid-item :span="24" :l-span="16">
        <n-card title="产线队列快照">
          <n-data-table :columns="queueColumns" :data="queueData" :pagination="false" />
        </n-card>
      </n-grid-item>

      <n-grid-item :span="24" :l-span="8">
        <n-card title="指挥事件流">
          <n-timeline>
            <n-timeline-item type="info" title="Jita 工厂节点上线" content="工业工单镜像恢复，吞吐稳定。" time="00:14" />
            <n-timeline-item type="warning" title="反应炉库存低于阈值" content="Moongoo 输入材料预计 4 小时内耗尽。" time="01:27" />
            <n-timeline-item type="error" title="Hull 生产线效率异常" content="Beta 线 ME/TE 参数失配，建议复查蓝图库。" time="02:41" />
          </n-timeline>
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<style module lang="scss">
.page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;

  @media (max-width: 960px) {
    grid-template-columns: 1fr;
  }
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
  font-size: clamp(30px, 4vw, 46px);
  line-height: 1.02;
}

.subtitle {
  max-width: 760px;
  margin: 12px 0 0;
  color: rgba(224, 224, 224, 0.68);
  line-height: 1.7;
}

.statusCard {
  backdrop-filter: blur(8px);
}
</style>