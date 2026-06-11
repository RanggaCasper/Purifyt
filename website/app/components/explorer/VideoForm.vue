<script setup lang="ts">
const explorerStore = useExplorerStore()
const toast = useToast()
const { t } = useI18n()
const { extractVideoId } = useVideoId()

const videoForm = reactive({
  videoId: '',
  datasetName: ''
})

async function runVideoExplorer() {
  if (!videoForm.videoId) {
    toast.add({ title: t('explorer.fillFields'), color: 'warning' })
    return
  }
  const videoId = extractVideoId(videoForm.videoId)
  await explorerStore.runVideoExplorer(videoId, videoForm.datasetName)
  if (explorerStore.error) {
    toast.add({ title: explorerStore.error, color: 'error' })
  } else if (explorerStore.result) {
    toast.add({
      title: t('explorer.analysisComplete', { n: explorerStore.result.total_judi }),
      color: 'success'
    })
  }
}

function resetExplorer() {
  explorerStore.reset()
  videoForm.videoId = ''
  videoForm.datasetName = ''
}
</script>

<template>
  <div class="bg-default border border-default rounded-xl p-5">
    <h3 class="font-medium text-sm text-highlighted mb-4">
      {{ $t('explorer.videoExplorer') }}
    </h3>

    <form
      class="space-y-4"
      @submit.prevent="runVideoExplorer"
    >
      <UFormField :label="$t('explorer.videoUrlLabel')">
        <UInput
          v-model="videoForm.videoId"
          :placeholder="$t('explorer.videoUrlPlaceholder')"
          icon="i-lucide-link"
          size="lg"
          class="w-full"
        />
      </UFormField>

      <UFormField
        :label="$t('explorer.datasetNameLabel')"
        :hint="$t('explorer.datasetNameHint')"
      >
        <UInput
          v-model="videoForm.datasetName"
          :placeholder="$t('explorer.datasetNamePlaceholder')"
          icon="i-lucide-database"
          size="lg"
          class="w-full"
        />
      </UFormField>

      <div class="flex gap-2">
        <UButton
          type="submit"
          :label="$t('explorer.startAnalysis')"
          icon="i-lucide-play"
          :loading="explorerStore.isRunning"
          :disabled="explorerStore.isRunning"
        />
        <UButton
          v-if="explorerStore.result || explorerStore.error || explorerStore.logs.length > 0"
          :label="$t('common.reset')"
          variant="outline"
          color="neutral"
          icon="i-lucide-rotate-ccw"
          @click="resetExplorer"
        />
      </div>
    </form>
  </div>
</template>
