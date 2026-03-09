<script setup lang="ts">
withDefaults(
  defineProps<{
    typeId: number | string
    category?: string
    size?: number
  }>(),
  {
    category: 'icon',
    size: 32,
  },
)
</script>

<template>
  <div :class="$style.wrapper" :style="{ width: `${size}px`, height: `${size}px` }">
    <img
      :src="`https://images.evetech.net/types/${typeId}/${category}?size=${size}`"
      :class="$style.image"
      :alt="`EVE asset ${typeId}`"
      loading="lazy"
    />
  </div>
</template>

<style module lang="scss">
.wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid var(--eve-border);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.5);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;

  &:hover {
    border-color: var(--eve-cyan);
    box-shadow: 0 0 8px rgba(0, 254, 254, 0.3);
    transform: translateY(-1px);
  }
}

.image {
  max-width: 100%;
  height: auto;
  display: block;
}
</style>