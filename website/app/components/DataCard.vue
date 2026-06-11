<script setup lang="ts">
defineProps<{
  loading?: boolean
  empty?: boolean
  emptyTitle?: string
  emptyDescription?: string
  emptyIcon?: string
}>()
</script>

<template>
  <div class="bg-default border border-default rounded-xl overflow-hidden">
    <!-- Loading state -->
    <div
      v-if="loading"
      class="p-8 flex flex-col items-center justify-center gap-3"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="text-2xl text-blue-500 animate-spin"
      />
      <p class="text-sm text-muted">
        {{ $t('common.loading') }}
      </p>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="empty"
      class="p-12 flex flex-col items-center justify-center gap-3 text-center"
    >
      <UIcon
        :name="emptyIcon || 'i-lucide-inbox'"
        class="text-4xl text-dimmed"
      />
      <h3 class="text-sm font-medium text-highlighted">
        {{ emptyTitle || $t('common.noData') }}
      </h3>
      <p
        v-if="emptyDescription"
        class="text-xs text-muted max-w-sm"
      >
        {{ emptyDescription }}
      </p>
    </div>

    <!-- Content -->
    <div v-else>
      <slot />
    </div>
  </div>
</template>
