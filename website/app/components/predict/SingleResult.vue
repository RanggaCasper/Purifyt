<script setup lang="ts">
const labelingStore = useLabelingStore()
</script>

<template>
  <div
    v-if="labelingStore.singleResult"
    class="bg-default border border-default rounded-xl p-5"
  >
    <h3 class="font-medium text-sm text-highlighted mb-4">
      {{ $t('predict.predictionResult') }}
    </h3>

    <div class="space-y-4">
      <div class="flex items-center gap-3">
        <LabelBadge :label="labelingStore.singleResult.label" />
        <span class="text-sm text-muted">
          {{ $t('common.confidence') }}:
          {{
            (
              (labelingStore.singleResult.label === 1
                ? labelingStore.singleResult.judi
                : labelingStore.singleResult.normal) * 100
            ).toFixed(1)
          }}%
        </span>
      </div>

      <div class="space-y-2">
        <div class="flex items-center justify-between text-sm">
          <span class="text-muted">{{ $t('common.normal') }}</span>
          <span class="font-medium">{{ (labelingStore.singleResult.normal * 100).toFixed(1) }}%</span>
        </div>
        <div class="w-full bg-elevated rounded-full h-2">
          <div
            class="bg-green-500 h-full rounded-full transition-all"
            :style="{ width: `${labelingStore.singleResult.normal * 100}%` }"
          />
        </div>

        <div class="flex items-center justify-between text-sm">
          <span class="text-muted">{{ $t('common.judi') }}</span>
          <span class="font-medium">{{ (labelingStore.singleResult.judi * 100).toFixed(1) }}%</span>
        </div>
        <div class="w-full bg-elevated rounded-full h-2">
          <div
            class="bg-red-500 h-full rounded-full transition-all"
            :style="{ width: `${labelingStore.singleResult.judi * 100}%` }"
          />
        </div>
      </div>

      <div class="pt-3 border-t border-default">
        <p class="text-xs text-muted mb-1">
          {{ $t('predict.cleanedText') }}
        </p>
        <p class="text-sm text-highlighted">
          {{ labelingStore.singleResult.clean_comment }}
        </p>
      </div>
    </div>
  </div>
</template>
