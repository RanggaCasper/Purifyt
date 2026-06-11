<script setup lang="ts">
const autoDeleteStore = useAutoDeleteStore()
const toast = useToast()
const { t } = useI18n()

const scanForm = reactive({
  videoId: '',
  email: '',
  threshold: 0.7,
  headless: true
})

const accountOptions = computed(() =>
  autoDeleteStore.accounts.map(a => ({
    label: `${a.email} (${a.channel_name})`,
    value: a.email
  }))
)

function extractVideoId(input: string): string {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
    /^[a-zA-Z0-9_-]{11}$/
  ]
  for (const p of patterns) {
    const match = input.match(p)
    if (match) return match[1] || match[0]
  }
  return input
}

async function handleScan(preview = false) {
  if (!scanForm.videoId || !scanForm.email) {
    toast.add({
      title: t('autoDelete.enterVideoId'),
      color: 'warning'
    })
    return
  }
  const videoId = extractVideoId(scanForm.videoId)
  await autoDeleteStore.scan(
    {
      video_id: videoId,
      email: scanForm.email,
      threshold: scanForm.threshold,
      headless: scanForm.headless
    },
    preview
  )
  if (autoDeleteStore.scanError) {
    toast.add({ title: autoDeleteStore.scanError, color: 'error' })
  } else if (autoDeleteStore.scanResult) {
    const r = autoDeleteStore.scanResult
    if (preview) {
      toast.add({
        title: t('autoDelete.previewDone', { detected: r.detected, total: r.scanned }),
        color: 'success'
      })
    } else {
      toast.add({
        title: t('autoDelete.scanComplete', { deleted: r.deleted, total: r.scanned }),
        color: 'success'
      })
    }
  }
}
</script>

<template>
  <div class="bg-default border border-default rounded-xl p-5">
    <h3 class="font-medium text-sm text-highlighted mb-4">
      {{ $t('autoDelete.scanVideo') }}
    </h3>

    <div
      v-if="autoDeleteStore.accounts.length === 0 && !autoDeleteStore.accountsLoading"
      class="mb-4"
    >
      <UAlert
        color="warning"
        :title="$t('autoDelete.noAccountsTitle')"
        :description="$t('autoDelete.noAccountsDesc')"
        icon="i-lucide-alert-triangle"
      />
    </div>

    <form
      class="space-y-4"
      @submit.prevent="handleScan(false)"
    >
      <UFormField :label="$t('autoDelete.videoUrlLabel')">
        <UInput
          v-model="scanForm.videoId"
          placeholder="https://youtube.com/watch?v=... or video ID"
          icon="i-lucide-link"
          size="lg"
          class="w-full"
        />
      </UFormField>

      <UFormField :label="$t('autoDelete.googleAccount')">
        <select
          v-model="scanForm.email"
          :disabled="autoDeleteStore.accountsLoading || accountOptions.length === 0"
          class="w-full h-10 rounded-md border border-default bg-default text-sm px-3 text-highlighted focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <option
            value=""
            disabled
          >
            {{
              autoDeleteStore.accountsLoading
                ? $t('autoDelete.loadingAccounts')
                : accountOptions.length === 0
                  ? $t('autoDelete.noAccountsAvailable')
                  : $t('autoDelete.selectAccount')
            }}
          </option>
          <option
            v-for="opt in accountOptions"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </option>
        </select>
      </UFormField>

      <UFormField :label="$t('autoDelete.thresholdLabel')">
        <div class="flex items-center gap-3">
          <input
            v-model.number="scanForm.threshold"
            type="range"
            min="0"
            max="1"
            step="0.05"
            class="flex-1 accent-blue-500"
          >
          <span class="text-sm font-medium text-highlighted w-12 text-right tabular-nums">
            {{ scanForm.threshold.toFixed(2) }}
          </span>
        </div>
        <p class="text-xs text-muted mt-1">
          {{ $t('autoDelete.thresholdHelp') }}
        </p>
      </UFormField>

      <UFormField :label="$t('autoDelete.browserMode')">
        <div class="flex gap-2">
          <UButton
            :label="$t('autoDelete.headless')"
            icon="i-lucide-monitor-off"
            size="sm"
            :color="scanForm.headless ? 'primary' : 'neutral'"
            :variant="scanForm.headless ? 'solid' : 'outline'"
            @click="scanForm.headless = true"
          />
          <UButton
            :label="$t('autoDelete.showBrowser')"
            icon="i-lucide-monitor"
            size="sm"
            :color="!scanForm.headless ? 'primary' : 'neutral'"
            :variant="!scanForm.headless ? 'solid' : 'outline'"
            @click="scanForm.headless = false"
          />
        </div>
        <p class="text-xs text-muted mt-1">
          {{
            scanForm.headless
              ? $t('autoDelete.headlessHelp')
              : $t('autoDelete.showBrowserHelp')
          }}
        </p>
      </UFormField>

      <div class="flex gap-2 flex-wrap">
        <UButton
          type="submit"
          :label="$t('autoDelete.scanDeleteBtn')"
          icon="i-lucide-trash-2"
          color="error"
          :loading="autoDeleteStore.scanRunning"
          :disabled="autoDeleteStore.scanRunning || !scanForm.email"
        />
        <UButton
          :label="$t('autoDelete.previewBtn')"
          icon="i-lucide-eye"
          variant="outline"
          :loading="autoDeleteStore.scanRunning"
          :disabled="autoDeleteStore.scanRunning || !scanForm.email"
          @click="handleScan(true)"
        />
        <UButton
          v-if="
            autoDeleteStore.scanResult
              || autoDeleteStore.scanError
              || autoDeleteStore.scanLogs.length > 0
          "
          :label="$t('common.reset')"
          variant="outline"
          color="neutral"
          icon="i-lucide-rotate-ccw"
          @click="autoDeleteStore.resetScan()"
        />
      </div>
    </form>
  </div>
</template>
