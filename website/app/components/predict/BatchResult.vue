<script setup lang="ts">
const labelingStore = useLabelingStore()

const batchStats = computed(() => {
  const total = labelingStore.batchResults.length
  const judi = labelingStore.batchResults.filter(r => r.label === 1).length
  return { total, judi, normal: total - judi }
})
</script>

<template>
  <template v-if="labelingStore.batchResults.length > 0">
    <div class="grid grid-cols-3 gap-3">
      <StatCard
        :title="$t('common.total')"
        :value="batchStats.total"
        icon="i-lucide-list"
        color="blue"
      />
      <StatCard
        :title="$t('common.judi')"
        :value="batchStats.judi"
        icon="i-lucide-alert-triangle"
        color="red"
      />
      <StatCard
        :title="$t('common.normal')"
        :value="batchStats.normal"
        icon="i-lucide-check-circle"
        color="green"
      />
    </div>

    <DataCard :empty="false">
      <div class="px-5 py-3 border-b border-default">
        <span class="text-sm text-muted">
          {{ labelingStore.batchResults.length }} {{ $t('predict.predictions') }}
        </span>
      </div>
      <div class="max-h-96 overflow-y-auto">
        <CommentItem
          v-for="(result, idx) in labelingStore.batchResults"
          :key="idx"
          :text="result.text"
          :label="result.label"
          :confidence="{ normal: result.normal, judi: result.judi }"
          show-badge
        />
      </div>
    </DataCard>
  </template>
</template>
