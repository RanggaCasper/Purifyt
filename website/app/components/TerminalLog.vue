<script setup lang="ts">
import type { LogMeta } from '~/composables/useLogMeta'

export interface TerminalLogEntry {
  type: string
  step?: string
  message: string
}

export interface TerminalProgress {
  current: number
  total: number
  label?: string
}

const props = defineProps<{
  title: string
  logs: TerminalLogEntry[]
  running?: boolean
  progress?: TerminalProgress | null
  logMeta: (type: string, step?: string) => LogMeta
  maxHeight?: string
}>()

const logContainer = ref<HTMLElement | null>(null)

watch(
  () => props.logs.length,
  async () => {
    await nextTick()
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }
)

const progressPercentage = computed(() => {
  if (!props.progress || props.progress.total === 0) return 0
  return (props.progress.current / props.progress.total) * 100
})
</script>

<template>
  <div class="bg-default border border-default rounded-xl overflow-hidden">
    <!-- Terminal header (macOS chrome) -->
    <div class="flex items-center gap-2 px-4 py-2.5 bg-elevated border-b border-default">
      <div class="flex gap-1.5">
        <span class="w-2.5 h-2.5 rounded-full bg-red-500/70" />
        <span class="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
        <span class="w-2.5 h-2.5 rounded-full bg-green-500/70" />
      </div>
      <span class="text-xs font-mono text-muted ml-1">{{ title }}</span>
      <UIcon
        v-if="running"
        name="i-lucide-loader-circle"
        class="ml-auto animate-spin text-blue-400 text-sm"
      />
    </div>

    <!-- Log entries -->
    <div
      ref="logContainer"
      :class="['font-mono text-xs p-4 space-y-1.5 overflow-y-auto bg-slate-100 dark:bg-neutral-950/80', maxHeight ?? 'max-h-64']"
    >
      <div
        v-for="(entry, i) in logs"
        :key="i"
        class="flex items-start gap-2"
      >
        <UIcon
          :name="logMeta(entry.type, entry.step).icon"
          :class="['mt-0.5 shrink-0 text-sm', logMeta(entry.type, entry.step).colorClass]"
        />
        <span class="text-slate-700 dark:text-neutral-300 leading-relaxed">{{ entry.message }}</span>
      </div>

      <!-- Blinking cursor while running -->
      <div
        v-if="running"
        class="flex items-center gap-2 text-slate-400 dark:text-neutral-500"
      >
        <span class="inline-block w-2 h-3.5 bg-slate-400 dark:bg-neutral-500 animate-pulse rounded-sm" />
      </div>
    </div>

    <!-- Optional progress bar footer -->
    <div
      v-if="progress && progress.total > 0"
      class="px-4 py-3 border-t border-default bg-elevated"
    >
      <div class="flex justify-between text-xs text-muted mb-1.5">
        <span>{{ progress.label }}</span>
        <span class="font-medium tabular-nums">
          {{ progress.current }}/{{ progress.total }}
          ({{ progressPercentage.toFixed(1) }}%)
        </span>
      </div>
      <div class="h-1.5 bg-border rounded-full overflow-hidden">
        <div
          class="h-full bg-primary-500 rounded-full transition-all duration-300"
          :style="{ width: `${progressPercentage}%` }"
        />
      </div>
    </div>
  </div>
</template>
