<script setup lang="ts">
const _props = defineProps<{
  text: string
  cleanText?: string
  author?: string
  label?: number | null
  confidence?: { normal: number, judi: number }
  showBadge?: boolean
}>()
</script>

<template>
  <div class="px-4 py-3 hover:bg-elevated/50 transition-colors">
    <div class="flex items-start justify-between gap-3 min-w-0">
      <div class="flex-1 min-w-0 overflow-hidden">
        <div
          v-if="author"
          class="flex items-center gap-1.5 mb-1"
        >
          <UIcon
            name="i-lucide-user"
            class="text-xs text-muted shrink-0"
          />
          <span class="text-xs font-medium text-muted truncate">{{
            author
          }}</span>
        </div>
        <p
          class="text-sm text-highlighted"
          style="overflow-wrap: anywhere; word-break: break-word"
        >
          {{ text }}
        </p>
        <div
          v-if="confidence"
          class="flex items-center gap-3 mt-1.5 text-xs text-muted"
        >
          <span>{{ $t('common.normal') }}: {{ (confidence.normal * 100).toFixed(1) }}%</span>
          <span>{{ $t('common.judi') }}: {{ (confidence.judi * 100).toFixed(1) }}%</span>
        </div>
      </div>
      <LabelBadge
        v-if="showBadge && label !== null && label !== undefined"
        :label="label"
        class="shrink-0 mt-0.5"
      />
    </div>
  </div>
</template>
