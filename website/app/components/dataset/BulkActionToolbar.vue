<script setup lang="ts">
defineProps<{
  selectedCount: number
  bulkLabelLoading: boolean
}>()

const emit = defineEmits<{
  bulkLabel: [label: 0 | 1]
  clearSelection: []
}>()
</script>

<template>
  <Transition
    enter-active-class="transition-all duration-200"
    enter-from-class="opacity-0 -translate-y-2"
    enter-to-class="opacity-100 translate-y-0"
    leave-active-class="transition-all duration-150"
    leave-from-class="opacity-100 translate-y-0"
    leave-to-class="opacity-0 -translate-y-2"
  >
    <div
      v-if="selectedCount > 0"
      class="mx-4 mb-2 px-4 py-2.5 bg-primary-50 dark:bg-primary-950 border border-primary-200 dark:border-primary-800 rounded-lg flex flex-wrap items-center justify-between gap-3"
    >
      <span class="text-sm font-medium text-primary-700 dark:text-primary-300">
        {{ $t('datasetDetail.commentsSelected', { n: selectedCount }) }}
      </span>
      <div class="flex items-center gap-2">
        <UButton
          :label="$t('datasetDetail.labelJudi')"
          color="error"
          variant="soft"
          size="xs"
          icon="i-lucide-alert-triangle"
          :loading="bulkLabelLoading"
          @click="emit('bulkLabel', 1)"
        />
        <UButton
          :label="$t('datasetDetail.labelNormal')"
          color="success"
          variant="soft"
          size="xs"
          icon="i-lucide-check-circle"
          :loading="bulkLabelLoading"
          @click="emit('bulkLabel', 0)"
        />
        <UButton
          :label="$t('common.clear')"
          color="neutral"
          variant="ghost"
          size="xs"
          icon="i-lucide-x"
          @click="emit('clearSelection')"
        />
      </div>
    </div>
  </Transition>
</template>
