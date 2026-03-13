<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    iconName?: string | null
    alt?: string
    size?: number
  }>(),
  {
    iconName: '',
    alt: '',
    size: 20,
  },
)

const src = computed(() => {
  if (!props.iconName) {
    return ''
  }

  const cleanIconName = props.iconName.includes('/') ? props.iconName.split('/').pop() ?? '' : props.iconName
  return cleanIconName ? `/eve-icons/${cleanIconName}` : ''
})
</script>

<template>
  <img
    v-if="src"
    :src="src"
    :alt="alt"
    :title="alt"
    :style="{ width: `${size}px`, height: `${size}px` }"
    class="tree-icon-source"
    loading="lazy"
  />
</template>

<style scoped lang="scss">
.tree-icon-source {
  display: inline-block;
  margin-right: 8px;
  vertical-align: middle;
  border-radius: 2px;
  object-fit: contain;
  filter: drop-shadow(0 0 2px rgba(0, 0, 0, 0.5));
}
</style>