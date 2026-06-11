<script setup lang="ts">
defineProps<{
  current: number
  total: number
  message?: string
}>()

const percentage = computed(() => {
  const props = getCurrentInstance()?.props as Record<string, unknown>
  if (!props || props.total === 0) return 0
  return Math.round(((props.current as number) / (props.total as number)) * 100)
})
</script>

<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between text-sm">
      <span class="text-muted">{{ message || $t('components.processing') }}</span>
      <span class="font-medium text-highlighted">{{ percentage }}%</span>
    </div>
    <div class="w-full bg-elevated rounded-full h-2.5 overflow-hidden">
      <div
        class="bg-blue-500 h-full rounded-full transition-all duration-500 ease-out"
        :style="{ width: `${percentage}%` }"
      />
    </div>
    <p class="text-xs text-muted">
      {{ current }} / {{ total }}
    </p>
  </div>
</template>
