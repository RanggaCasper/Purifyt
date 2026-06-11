<script setup lang="ts">
const explorerStore = useExplorerStore()
const { getLogMeta } = useLogMeta()
</script>

<template>
  <div class="space-y-4">
    <!-- Live activity log -->
    <TerminalLog
      v-if="explorerStore.logs.length > 0 || explorerStore.isRunning"
      :title="$t('explorer.terminalLabel')"
      :logs="explorerStore.logs"
      :running="explorerStore.isRunning"
      :progress="
        explorerStore.labelProgress
          ? {
            current: explorerStore.labelProgress.labeled,
            total: explorerStore.labelProgress.total,
            label: $t('explorer.labelingProgress')
          }
          : null
      "
      :log-meta="(type: string) => getLogMeta(type)"
    />

    <!-- Waiting (no logs yet) -->
    <div
      v-if="explorerStore.isRunning && explorerStore.logs.length === 0"
      class="bg-default border border-default rounded-xl p-8 flex flex-col items-center gap-3"
    >
      <UIcon
        name="i-lucide-loader-circle"
        class="text-2xl text-blue-500 animate-spin"
      />
      <p class="text-sm text-muted">
        {{ $t('explorer.startingAnalysis') }}
      </p>
    </div>

    <!-- Final result stats -->
    <div
      v-if="explorerStore.result"
      class="bg-default border border-default rounded-xl p-5"
    >
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-medium text-sm text-highlighted">
          {{ $t('explorer.result') }}
        </h3>
        <UButton
          v-if="explorerStore.datasetId"
          :to="`/datasets/${explorerStore.datasetId}`"
          :label="$t('explorer.viewDataset')"
          icon="i-lucide-arrow-right"
          trailing
          size="xs"
          variant="outline"
        />
      </div>

      <div class="flex items-center gap-2 text-sm mb-4">
        <UIcon
          name="i-lucide-video"
          class="text-blue-500 shrink-0"
        />
        <span class="font-medium text-highlighted truncate">{{ explorerStore.result.title }}</span>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <StatCard
          :title="$t('explorer.totalFetched')"
          :value="explorerStore.result.total_fetched"
          icon="i-lucide-message-square"
          color="blue"
        />
        <StatCard
          :title="$t('explorer.saved')"
          :value="explorerStore.result.total_saved"
          icon="i-lucide-database"
          color="blue"
        />
        <StatCard
          :title="$t('common.gambling')"
          :value="explorerStore.result.total_judi"
          icon="i-lucide-alert-triangle"
          color="red"
        />
        <StatCard
          :title="$t('common.normal')"
          :value="explorerStore.result.total_normal"
          icon="i-lucide-check-circle"
          color="green"
        />
      </div>

      <!-- Judi percentage bar -->
      <div class="mt-4">
        <div class="flex justify-between text-xs text-muted mb-1">
          <span>{{ $t('explorer.gamblingRatio') }}</span>
          <span class="font-medium">{{ explorerStore.result.judi_percentage.toFixed(1) }}%</span>
        </div>
        <div class="h-2 bg-border rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="explorerStore.result.judi_percentage > 20 ? 'bg-red-500' : 'bg-green-500'"
            :style="{ width: `${Math.min(explorerStore.result.judi_percentage, 100)}%` }"
          />
        </div>
      </div>
    </div>

    <!-- Error -->
    <UAlert
      v-if="explorerStore.error"
      color="error"
      :title="explorerStore.error"
      icon="i-lucide-alert-circle"
    />
  </div>
</template>
