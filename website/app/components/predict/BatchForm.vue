<script setup lang="ts">
const labelingStore = useLabelingStore()
const toast = useToast()
const { t } = useI18n()

const batchText = ref('')

async function predictBatch() {
  const lines = batchText.value.split('\n').map(l => l.trim()).filter(Boolean)
  if (lines.length === 0) {
    toast.add({ title: t('predict.enterAtLeast'), color: 'warning' })
    return
  }
  try {
    await labelingStore.predictBatch(lines)
    toast.add({
      title: t('predict.commentsPredicted', { n: labelingStore.batchResults.length }),
      color: 'success'
    })
  } catch {
    toast.add({ title: t('predict.batchFailed'), color: 'error' })
  }
}

function reset() {
  labelingStore.reset()
  batchText.value = ''
}
</script>

<template>
  <div>
    <h3 class="font-medium text-sm text-highlighted mb-3">
      {{ $t('predict.batchPrediction') }}
    </h3>
    <form
      class="space-y-4"
      @submit.prevent="predictBatch"
    >
      <UFormField :label="$t('predict.commentsPerLine')">
        <UTextarea
          v-model="batchText"
          :placeholder="$t('predict.batchPlaceholder') + '\nslot gacor\nnice video!'"
          :rows="8"
          autoresize
          class="w-full"
        />
      </UFormField>
      <div class="flex gap-2">
        <UButton
          type="submit"
          :label="$t('predict.predictBatch')"
          icon="i-lucide-sparkles"
          :loading="labelingStore.loading"
        />
        <UButton
          v-if="labelingStore.batchResults.length > 0"
          :label="$t('common.clear')"
          variant="outline"
          color="neutral"
          icon="i-lucide-x"
          @click="reset"
        />
      </div>
    </form>
  </div>
</template>
