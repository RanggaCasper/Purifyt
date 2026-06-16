<script setup lang="ts">
definePageMeta({
  title: 'Explorer'
})

const mode = ref<'video' | 'channel'>('video')
const { apiFetch } = useApi()
const { t } = useI18n()
const toast = useToast()

const credentialLoading = ref(true)
const youtubeApiKeySet = ref(false)

interface CredentialSettings {
  youtube_api_key_set: boolean
}

async function loadCredentialStatus() {
  credentialLoading.value = true
  try {
    const data = await apiFetch<CredentialSettings>('/api/v1/settings/credentials')
    youtubeApiKeySet.value = data.youtube_api_key_set
  } catch (error: unknown) {
    const err = error as { message?: string }
    toast.add({ title: err.message || t('settings.credentialsLoadFailed'), color: 'error' })
    youtubeApiKeySet.value = false
  } finally {
    credentialLoading.value = false
  }
}

onMounted(loadCredentialStatus)
</script>

<template>
  <div>
    <PageHeader
      :title="$t('explorer.title')"
      :description="$t('explorer.desc')"
    />

    <div
      v-if="credentialLoading"
      class="bg-default border border-default rounded-xl p-5 text-sm text-muted"
    >
      {{ $t('common.loading') }}
    </div>

    <div
      v-else-if="!youtubeApiKeySet"
      class="bg-default border border-default rounded-xl p-6 text-center"
    >
      <UIcon
        name="i-lucide-lock-keyhole"
        class="mx-auto mb-3 text-3xl text-warning"
      />
      <h3 class="font-semibold text-highlighted">
        {{ $t('explorer.youtubeApiKeyRequiredTitle') }}
      </h3>
      <p class="text-sm text-muted mt-2">
        {{ $t('explorer.youtubeApiKeyRequiredDesc') }}
      </p>
      <UButton
        class="mt-4"
        to="/settings"
        icon="i-lucide-settings"
        :label="$t('explorer.openSettings')"
      />
    </div>

    <template v-else>
      <!-- Mode toggle -->
      <div class="flex gap-2 mb-6">
      <UButton
        :color="mode === 'video' ? 'primary' : 'neutral'"
        :variant="mode === 'video' ? 'solid' : 'outline'"
        :label="$t('explorer.video')"
        icon="i-lucide-play"
        @click="mode = 'video'"
      />
      <UButton
        :color="mode === 'channel' ? 'primary' : 'neutral'"
        :variant="mode === 'channel' ? 'solid' : 'outline'"
        :label="$t('explorer.channel')"
        icon="i-lucide-tv"
        @click="mode = 'channel'"
      />
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Form -->
        <ExplorerVideoForm v-if="mode === 'video'" />
        <ExplorerChannelForm v-else />

        <!-- Results -->
        <ExplorerResultPanel />
      </div>
    </template>
  </div>
</template>
