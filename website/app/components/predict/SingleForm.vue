<script setup lang="ts">
const labelingStore = useLabelingStore()
const toast = useToast()
const { t } = useI18n()

const singleText = ref('')

async function predictSingle() {
  if (!singleText.value.trim()) {
    toast.add({ title: t('predict.enterComment'), color: 'warning' })
    return
  }
  try {
    await labelingStore.predictSingle(singleText.value)
  } catch {
    toast.add({ title: t('predict.predictionFailed'), color: 'error' })
  }
}

function reset() {
  labelingStore.reset()
  singleText.value = ''
}
</script>

<template>
  <div>
    <h3 class="font-medium text-sm text-highlighted mb-3">
      {{ $t('predict.singlePrediction') }}
    </h3>
    <form
      class="space-y-4"
      @submit.prevent="predictSingle"
    >
      <UFormField :label="$t('predict.commentLabel')">
        <UTextarea
          v-model="singleText"
          :placeholder="$t('predict.commentPlaceholder')"
          :rows="4"
          autoresize
          class="w-full"
        />
      </UFormField>
      <div class="flex gap-2">
        <UButton
          type="submit"
          :label="$t('predict.predictBtn')"
          icon="i-lucide-sparkles"
          :loading="labelingStore.loading"
        />
        <UButton
          v-if="labelingStore.singleResult"
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
