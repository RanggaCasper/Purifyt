<script setup lang="ts">
import { useColorMode } from '#imports'

definePageMeta({
  title: 'Settings'
})

const { isAuthenticated, user: authUser, logout } = useAuth()
const { baseURL } = useApi()
const _toast = useToast()
const colorMode = useColorMode()
const { t } = useI18n()

const apiStatus = ref<'checking' | 'online' | 'offline'>('checking')

onMounted(async () => {
  try {
    await $fetch(`${baseURL}/docs`, { method: 'HEAD' })
    apiStatus.value = 'online'
  } catch {
    apiStatus.value = 'offline'
  }
})

const themeOptions = computed(() => [
  { label: t('settings.light'), value: 'light', icon: 'i-lucide-sun' },
  { label: t('settings.dark'), value: 'dark', icon: 'i-lucide-moon' },
  { label: t('settings.system'), value: 'system', icon: 'i-lucide-monitor' }
])
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
                  {{ authUser.email }}
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
