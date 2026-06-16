<script setup lang="ts">
import { useColorMode } from '#imports'

definePageMeta({
  title: 'Settings'
})

const { isAuthenticated, user: authUser, logout } = useAuth()
const { baseURL, resolveApiBase } = useApi()
const { apiFetch } = useApi()
const toast = useToast()
const colorMode = useColorMode()
const { t } = useI18n()

const apiStatus = ref<'checking' | 'online' | 'offline'>('checking')
const credentialLoading = ref(false)
const credentialSaving = ref(false)
const credentials = reactive({
  youtube_api_key: '',
  kaggle_username: '',
  kaggle_key: ''
})

interface CredentialSettings {
  youtube_api_key: string
  kaggle_username: string
  kaggle_key: string
  youtube_api_key_set: boolean
  kaggle_username_set: boolean
  kaggle_key_set: boolean
}

onMounted(async () => {
  try {
    const apiURL = await resolveApiBase()
    await $fetch(`${apiURL}/docs`, { method: 'HEAD' })
    apiStatus.value = 'online'
  } catch {
    apiStatus.value = 'offline'
  }

  await loadCredentials()
})

const themeOptions = computed(() => [
  { label: t('settings.light'), value: 'light', icon: 'i-lucide-sun' },
  { label: t('settings.dark'), value: 'dark', icon: 'i-lucide-moon' },
  { label: t('settings.system'), value: 'system', icon: 'i-lucide-monitor' }
])

async function loadCredentials() {
  if (!isAuthenticated.value) return
  credentialLoading.value = true
  try {
    const data = await apiFetch<CredentialSettings>('/api/v1/settings/credentials')
    credentials.youtube_api_key = data.youtube_api_key || ''
    credentials.kaggle_username = data.kaggle_username || ''
    credentials.kaggle_key = data.kaggle_key || ''
  } catch (error: unknown) {
    const err = error as { message?: string }
    toast.add({ title: err.message || t('settings.credentialsLoadFailed'), color: 'error' })
  } finally {
    credentialLoading.value = false
  }
}

async function saveCredentials() {
  credentialSaving.value = true
  try {
    await apiFetch<CredentialSettings>('/api/v1/settings/credentials', {
      method: 'PUT',
      body: credentials
    })
    toast.add({ title: t('settings.credentialsSaved'), color: 'success' })
  } catch (error: unknown) {
    const err = error as { message?: string }
    toast.add({ title: err.message || t('settings.credentialsSaveFailed'), color: 'error' })
  } finally {
    credentialSaving.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader
      :title="$t('settings.title')"
      :description="$t('settings.desc')"
    />

    <div class="max-w-2xl space-y-6">
      <!-- Account -->
      <div class="bg-default border border-default rounded-xl overflow-hidden">
        <div class="px-5 py-3 border-b border-default">
          <h3 class="font-medium text-sm text-highlighted">
            {{ $t('settings.account') }}
          </h3>
        </div>
        <div class="p-5 space-y-4">
          <div v-if="isAuthenticated && authUser">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 bg-blue-100 dark:bg-blue-950 rounded-full flex items-center justify-center">
                <UIcon
                  name="i-lucide-user"
                  class="text-xl text-blue-600 dark:text-blue-400"
                />
              </div>
              <div>
                <p class="font-medium text-highlighted">
                  {{ authUser.username }}
                </p>
                <p class="text-sm text-muted">
                  ID: {{ authUser.id }}
                </p>
              </div>
            </div>

            <div class="mt-4 pt-4 border-t border-default">
              <UButton
                :label="$t('settings.signOut')"
                icon="i-lucide-log-out"
                color="error"
                variant="outline"
                @click="logout()"
              />
            </div>
          </div>
          <div
            v-else
            class="text-sm text-muted"
          >
            <p>{{ $t('settings.notSignedIn') }}</p>
            <UButton
              :label="$t('settings.signIn')"
              to="/login"
              size="sm"
              class="mt-2"
            />
          </div>
        </div>
      </div>

      <!-- Credentials -->
      <div class="bg-default border border-default rounded-xl overflow-hidden">
        <div class="px-5 py-3 border-b border-default">
          <h3 class="font-medium text-sm text-highlighted">
            {{ $t('settings.apiCredentials') }}
          </h3>
        </div>
        <div class="p-5 space-y-4">
          <p class="text-sm text-muted">
            {{ $t('settings.apiCredentialsDesc') }}
          </p>

          <UFormField :label="$t('settings.youtubeApiKey')">
            <UInput
              v-model="credentials.youtube_api_key"
              type="password"
              placeholder="AIza..."
              icon="i-lucide-key-round"
              :loading="credentialLoading"
              class="w-full"
            />
          </UFormField>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <UFormField :label="$t('settings.kaggleUsername')">
              <UInput
                v-model="credentials.kaggle_username"
                placeholder="kaggle_username"
                icon="i-lucide-user"
                :loading="credentialLoading"
                class="w-full"
              />
            </UFormField>
            <UFormField :label="$t('settings.kaggleKey')">
              <UInput
                v-model="credentials.kaggle_key"
                type="password"
                :placeholder="$t('settings.kaggleKeyPlaceholder')"
                icon="i-lucide-key-round"
                :loading="credentialLoading"
                class="w-full"
              />
            </UFormField>
          </div>

          <div class="flex justify-end gap-2">
            <UButton
              :label="$t('common.reload')"
              variant="outline"
              color="neutral"
              :loading="credentialLoading"
              @click="loadCredentials"
            />
            <UButton
              :label="$t('settings.saveCredentials')"
              icon="i-lucide-save"
              :loading="credentialSaving"
              @click="saveCredentials"
            />
          </div>
        </div>
      </div>

      <!-- Appearance -->
      <div class="bg-default border border-default rounded-xl overflow-hidden">
        <div class="px-5 py-3 border-b border-default">
          <h3 class="font-medium text-sm text-highlighted">
            {{ $t('settings.appearance') }}
          </h3>
        </div>
        <div class="p-5">
          <p class="text-sm text-muted mb-3">
            {{ $t('settings.themeDesc') }}
          </p>
          <div class="flex gap-2">
            <UButton
              v-for="option in themeOptions"
              :key="option.value"
              :label="option.label"
              :icon="option.icon"
              :color="colorMode.preference === option.value ? 'primary' : 'neutral'"
              :variant="colorMode.preference === option.value ? 'solid' : 'outline'"
              size="sm"
              @click="colorMode.preference = option.value"
            />
          </div>
        </div>
      </div>

      <!-- API Status -->
      <div class="bg-default border border-default rounded-xl overflow-hidden">
        <div class="px-5 py-3 border-b border-default">
          <h3 class="font-medium text-sm text-highlighted">
            {{ $t('settings.apiConnection') }}
          </h3>
        </div>
        <div class="p-5 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-muted">{{ $t('settings.baseUrl') }}</span>
            <code class="text-xs px-2 py-1 bg-elevated rounded text-highlighted">
              {{ baseURL }}
            </code>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-muted">{{ $t('common.status') }}</span>
            <span class="flex items-center gap-2 text-sm">
              <span
                :class="[
                  'w-2 h-2 rounded-full',
                  apiStatus === 'online' ? 'bg-green-500'
                  : apiStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse'
                ]"
              />
              {{ apiStatus === 'checking' ? $t('settings.checking') : apiStatus === 'online' ? $t('settings.online') : $t('settings.offline') }}
            </span>
          </div>
        </div>
      </div>

      <!-- About -->
      <div class="bg-default border border-default rounded-xl overflow-hidden">
        <div class="px-5 py-3 border-b border-default">
          <h3 class="font-medium text-sm text-highlighted">
            {{ $t('settings.about') }}
          </h3>
        </div>
        <div class="p-5 space-y-2 text-sm text-muted">
          <p><strong class="text-highlighted">Purifyt</strong> – {{ $t('settings.aboutDesc') }}</p>
          <p>{{ $t('settings.poweredBy') }}</p>
          <p class="text-xs">
            {{ $t('settings.version') }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
