<script setup lang="ts">
const props = defineProps<{
  currentPage: number
  totalPages: number
  total: number
  perPage: number
  label?: string
}>()

const emit = defineEmits<{
  'update:currentPage': [page: number]
}>()

const showingFrom = computed(() =>
  Math.min((props.currentPage - 1) * props.perPage + 1, props.total)
)

const showingTo = computed(() =>
  Math.min(props.currentPage * props.perPage, props.total)
)

const visiblePages = computed(() => {
  const total = props.totalPages
  const current = props.currentPage
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  if (current <= 4) return [1, 2, 3, 4, 5, -1, total]
  if (current >= total - 3)
    return [1, -1, total - 4, total - 3, total - 2, total - 1, total]
  return [1, -1, current - 1, current, current + 1, -1, total]
})

function goToPage(page: number) {
  if (page < 1 || page > props.totalPages) return
  emit('update:currentPage', page)
}
</script>

<template>
  <div class="px-4 py-3 border-t border-default flex flex-col sm:flex-row items-center justify-between gap-3">
    <span class="text-xs text-muted shrink-0">
      {{ $t('common.showing') }}
      {{ showingFrom }}–{{ showingTo }}
      {{ $t('common.of') }} {{ total }} {{ label || $t('common.items') }}
    </span>
    <div
      v-if="totalPages > 1"
      class="flex items-center gap-1"
    >
      <UButton
        icon="i-lucide-chevron-first"
        variant="ghost"
        color="neutral"
        size="xs"
        :disabled="currentPage <= 1"
        @click="goToPage(1)"
      />
      <UButton
        icon="i-lucide-chevron-left"
        variant="ghost"
        color="neutral"
        size="xs"
        :disabled="currentPage <= 1"
        @click="goToPage(currentPage - 1)"
      />
      <template
        v-for="p in visiblePages"
        :key="p"
      >
        <span
          v-if="p === -1"
          class="px-1 text-muted select-none"
        >…</span>
        <UButton
          v-else
          :label="String(p)"
          size="xs"
          :color="p === currentPage ? 'primary' : 'neutral'"
          :variant="p === currentPage ? 'solid' : 'ghost'"
          @click="goToPage(p)"
        />
      </template>
      <UButton
        icon="i-lucide-chevron-right"
        variant="ghost"
        color="neutral"
        size="xs"
        :disabled="currentPage >= totalPages"
        @click="goToPage(currentPage + 1)"
      />
      <UButton
        icon="i-lucide-chevron-last"
        variant="ghost"
        color="neutral"
        size="xs"
        :disabled="currentPage >= totalPages"
        @click="goToPage(totalPages)"
      />
    </div>
  </div>
</template>
