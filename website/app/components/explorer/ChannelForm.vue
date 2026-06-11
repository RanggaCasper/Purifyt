<script setup lang="ts">
const explorerStore = useExplorerStore()
const toast = useToast()
const { t } = useI18n()

const channelForm = reactive({
  channel: '',
  maxVideos: 5,
  datasetName: ''
})

async function runChannelExplorer() {
  if (!channelForm.channel) {
    toast.add({ title: t('explorer.fillFields'), color: 'warning' })
    return
  }
  await explorerStore.runChannelExplorer(
    channelForm.channel,
    channelForm.maxVideos,
    channelForm.datasetName
  )
  if (explorerStore.error) {
    toast.add({ title: explorerStore.error, color: 'error' })
  } else if (explorerStore.result) {
    toast.add({ title: t('explorer.channelComplete'), color: 'success' })
  }
}

function resetExplorer() {
  explorerStore.reset()
  channelForm.channel = ''
  channelForm.maxVideos = 5
  channelForm.datasetName = ''
}
</script>

<template>
  <div class="bg-default border border-default rounded-xl p-5">
    <h3 class="font-medium text-sm text-highlighted mb-4">
      {{ $t('explorer.channelExplorer') }}
    </h3>

    <form
      class="space-y-4"
      @submit.prevent="runChannelExplorer"
    >
      <UFormField :label="$t('explorer.channelNameLabel')">
        <UInput
          v-model="channelForm.channel"
          :placeholder="$t('explorer.channelNamePlaceholder')"
          icon="i-lucide-tv"
          size="lg"
          class="w-full"
        />
      </UFormField>

      <UFormField :label="$t('explorer.maxVideos')">
        <UInput
          v-model.number="channelForm.maxVideos"
          type="number"
          :min="1"
          :max="50"
          icon="i-lucide-hash"
          size="lg"
          class="w-full"
        />
      </UFormField>

      <UFormField
        :label="$t('explorer.datasetNameLabel')"
        :hint="$t('explorer.datasetNameHint')"
      >
        <UInput
          v-model="channelForm.datasetName"
          :placeholder="$t('explorer.channelDatasetPlaceholder')"
          icon="i-lucide-database"
          size="lg"
          class="w-full"
        />
      </UFormField>

      <div class="flex gap-2">
        <UButton
          type="submit"
          :label="$t('explorer.startChannelScan')"
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
