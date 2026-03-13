<script setup lang="ts">
import { computed, h } from 'vue'
import { NSpin, NTree, type TreeOption } from 'naive-ui'

import EveTreeIconSource from './EveTreeIconSource.vue'

const props = withDefaults(
  defineProps<{
    title: string
    data: TreeOption[]
    loading?: boolean
    keyField?: string
    labelField?: string
    childrenField?: string
    iconField?: string
    selectable?: boolean
    blockNode?: boolean
    expandOnClick?: boolean
    expandAll?: boolean
  }>(),
  {
    loading: false,
    keyField: 'id',
    labelField: 'name',
    childrenField: 'children',
    iconField: 'iconname',
    selectable: true,
    blockNode: true,
    expandOnClick: true,
    expandAll: false,
  },
)

const emit = defineEmits<{
  (e: 'update:selectedKeys', keys: Array<string | number>, options: Array<TreeOption | null>): void
}>()

const normalizedData = computed<TreeOption[]>(() => {
  function normalize(nodes: TreeOption[]): TreeOption[] {
    return nodes.map((node) => {
      const rawNode = node as Record<string, unknown>
      const normalizedNode: Record<string, unknown> = { ...rawNode }
      const children = rawNode[props.childrenField]

      if (Array.isArray(children) && children.length > 0) {
        normalizedNode[props.childrenField] = normalize(children as TreeOption[])
      } else {
        delete normalizedNode[props.childrenField]
      }

      return normalizedNode as TreeOption
    })
  }

  return normalize(props.data)
})

const expandedKeys = computed<Array<string | number>>(() => {
  if (!props.expandAll) {
    return []
  }

  const keys: Array<string | number> = []

  function walk(nodes: TreeOption[]) {
    for (const node of nodes) {
      const children = (node as Record<string, unknown>)[props.childrenField]
      if (!Array.isArray(children) || children.length === 0) {
        continue
      }

      const key = (node as Record<string, unknown>)[props.keyField]
      if (typeof key === 'string' || typeof key === 'number') {
        keys.push(key)
      }

      walk(children as TreeOption[])
    }
  }

  walk(normalizedData.value)
  return keys
})

function renderTreeIcon({ option }: { option: TreeOption }) {
  const iconValue = (option as Record<string, unknown>)[props.iconField]
  if (typeof iconValue !== 'string' || !iconValue) {
    return null
  }

  const labelValue = (option as Record<string, unknown>)[props.labelField]
  const alt = typeof labelValue === 'string' ? labelValue : ''

  return h(EveTreeIconSource, {
    iconName: iconValue,
    alt,
  })
}

function handleSelectedKeys(keys: Array<string | number>, options: Array<TreeOption | null>) {
  emit('update:selectedKeys', keys, options)
}
</script>

<template>
  <div class="tree-panel">
    <div class="tree-panel__header">{{ title }}</div>
    <n-spin :show="loading" class="tree-panel__spin">
      <n-tree
        :data="normalizedData"
        :key-field="keyField"
        :label-field="labelField"
        :children-field="childrenField"
        :selectable="selectable"
        :block-node="blockNode"
        :expand-on-click="expandOnClick"
        :expanded-keys="expandAll ? expandedKeys : undefined"
        :render-prefix="renderTreeIcon"
        class="tree-panel__tree"
        @update:selected-keys="handleSelectedKeys"
      />
    </n-spin>
  </div>
</template>

<style scoped lang="scss">
@use '../../assets/styles/variables.scss' as *;

.tree-panel {
  height: 100%;
  background-color: rgba(20, 24, 31, 0.94);
  border-right: 1px solid rgba(42, 47, 58, 0.9);
}

.tree-panel__header {
  padding: 16px 18px;
  font-size: 15px;
  font-weight: 700;
  color: $eve-cyan;
  border-bottom: 1px solid $eve-border;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.tree-panel__spin {
  height: calc(100% - 58px);
}

.tree-panel__tree {
  height: 100%;
  padding: 10px 8px 16px;
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

</style>