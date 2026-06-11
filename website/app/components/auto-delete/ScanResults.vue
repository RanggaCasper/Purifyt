<script setup lang="ts">
const autoDeleteStore = useAutoDeleteStore()
const { getLogMeta } = useLogMeta()
</script>

<template>
  <div class="space-y-4">
    <!-- Live activity log -->
    <TerminalLog
      v-if="autoDeleteStore.scanLogs.length > 0 || autoDeleteStore.scanRunning"
      :title="$t('autoDelete.scanLog')"
      :logs="autoDeleteStore.scanLogs"
      :running="autoDeleteStore.scanRunning"
      :progress="
        autoDeleteStore.scanProgress && autoDeleteStore.scanProgress.total > 0
          ? {
            current: autoDeleteStore.scanProgress.current,
            total: autoDeleteStore.scanProgress.total,
            label: $t('autoDelete.scanningComments')
          }
          : null
      "
      :log-meta="getLogMeta"
      max-height="max-h-52"
    />

    <!-- Result stats -->
    <div
      v-if="autoDeleteStore.scanResult"
      class="space-y-4"
    >
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          :title="$t('autoDelete.scanned')"
          :value="autoDeleteStore.scanResult.scanned"
          icon="i-lucide-scan-search"
          color="blue"
        />
        <StatCard
          :title="$t('common.gambling')"
          :value="autoDeleteStore.scanResult.detected"
          icon="i-lucide-alert-triangle"
          color="red"
        />
        <StatCard
          :title="$t('autoDelete.deleted')"
          :value="autoDeleteStore.scanResult.deleted"
          icon="i-lucide-trash-2"
          color="green"
        />
        <StatCard
          :title="$t('autoDelete.error')"
          :value="autoDeleteStore.scanResult.errors"
          icon="i-lucide-alert-circle"
          color="yellow"
        />
      </div>

      <!-- Judi comments list -->
      <DataCard
        v-if="autoDeleteStore.judiComments.length > 0"
        :empty="false"
      >
        <div class="px-5 py-3 border-b border-default flex items-center justify-between">
          <h3 class="font-medium text-sm text-highlighted">
            {{ $t('autoDelete.gamblingDetected') }} ({{ autoDeleteStore.judiComments.length }})
          </h3>
        </div>
        <div class="max-h-80 overflow-y-auto divide-y divide-default">
          <div
            v-for="comment in autoDeleteStore.judiComments"
            :key="comment.comment_id"
            class="px-4 py-3 hover:bg-elevated/50 transition-colors"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5 mb-1">
                  <UIcon
                    name="i-lucide-user"
                    class="text-xs text-muted shrink-0"
                  />
                  <span class="text-xs font-medium text-muted truncate">{{ comment.author }}</span>
                </div>
                <p
                  class="text-sm text-highlighted"
                  style="overflow-wrap: anywhere; word-break: break-word"
                >
                  {{ comment.text }}
                </p>
                <div class="flex items-center gap-3 mt-1.5 text-xs text-muted">
                  <span>{{ $t('common.confidence') }}: {{ (comment.confidence * 100).toFixed(1) }}%</span>
                </div>
              </div>
              <LabelBadge
                :label="1"
                class="shrink-0 mt-0.5"
              />
            </div>
          </div>
        </div>
      </DataCard>
    </div>

    <!-- Scan error -->
    <UAlert
      v-if="autoDeleteStore.scanError && !autoDeleteStore.scanRunning"
      color="error"
      :title="autoDeleteStore.scanError"
      icon="i-lucide-alert-circle"
    />

    <!-- Empty state -->
    <div
      v-if="
        !autoDeleteStore.scanRunning
          && !autoDeleteStore.scanResult
          && !autoDeleteStore.scanError
          && autoDeleteStore.scanLogs.length === 0
      "
      class="bg-default border border-default rounded-xl p-12 flex flex-col items-center gap-3 text-center"
    >
      <UIcon
        name="i-lucide-scan-search"
        class="text-4xl text-dimmed"
      />
      <h3 class="text-sm font-medium text-highlighted">
        {{ $t('autoDelete.readyTitle') }}
      </h3>
      <p class="text-xs text-muted max-w-sm">
        {{ $t('autoDelete.readyDesc') }}
      </p>
    </div>
  </div>
</template>
