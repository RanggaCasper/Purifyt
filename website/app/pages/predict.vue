<script setup lang="ts">
definePageMeta({
  title: 'Predict'
})

const labelingStore = useLabelingStore()
const mode = ref<'single' | 'batch'>('single')
</script>

<template>
  <div>
    <PageHeader
      :title="$t('predict.title')"
      :description="$t('predict.desc')"
    />

    <!-- Mode toggle -->
    <div class="flex gap-2 mb-6">
      <UButton
        :color="mode === 'single' ? 'primary' : 'neutral'"
        :variant="mode === 'single' ? 'solid' : 'outline'"
        :label="$t('predict.single')"
        icon="i-lucide-message-square"
        @click="mode = 'single'; labelingStore.reset()"
      />
      <UButton
        :color="mode === 'batch' ? 'primary' : 'neutral'"
        :variant="mode === 'batch' ? 'solid' : 'outline'"
        :label="$t('predict.batch')"
        icon="i-lucide-list"
        @click="mode = 'batch'; labelingStore.reset()"
      />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Input -->
      <div class="bg-default border border-default rounded-xl p-5">
        <PredictSingleForm v-if="mode === 'single'" />
        <PredictBatchForm v-else />
      </div>

      <!-- Results -->
      <div class="space-y-4">
        <PredictSingleResult v-if="mode === 'single'" />
        <PredictBatchResult v-if="mode === 'batch'" />

        <!-- Empty state -->
        <div
          v-if="
            (mode === 'single' && !labelingStore.singleResult && !labelingStore.loading)
              || (mode === 'batch' && labelingStore.batchResults.length === 0 && !labelingStore.loading)
          "
          class="bg-default border border-default rounded-xl p-12 flex flex-col items-center gap-3 text-center"
        >
          <UIcon
            name="i-lucide-sparkles"
            class="text-4xl text-dimmed"
          />
          <h3 class="text-sm font-medium text-highlighted">
            {{ $t('predict.readyTitle') }}
          </h3>
          <p class="text-xs text-muted max-w-sm">
            {{ $t('predict.readyDesc') }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
