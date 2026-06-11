<script setup lang="ts">
const autoDeleteStore = useAutoDeleteStore()
const toast = useToast()
const { t } = useI18n()

const loginForm = reactive({
  email: '',
  password: '',
  headless: true,
  timeout: 120
})

async function handleLogin() {
  if (!loginForm.email || !loginForm.password) {
    toast.add({ title: t('autoDelete.enterEmailPass'), color: 'warning' })
    return
  }
  await autoDeleteStore.login({
    email: loginForm.email,
    password: loginForm.password,
    headless: loginForm.headless,
    timeout: loginForm.timeout
  })
  if (autoDeleteStore.loginError) {
    toast.add({ title: autoDeleteStore.loginError, color: 'error' })
  } else if (autoDeleteStore.loginResult) {
    toast.add({
      title: t('autoDelete.loginSuccessToast', {
        name: autoDeleteStore.loginResult.channelName
      }),
      color: 'success'
    })
    autoDeleteStore.fetchAccounts().catch(() => {})
  }
}
</script>

<template>
  <div class="bg-default border border-default rounded-xl p-5">
    <h3 class="font-medium text-sm text-highlighted mb-4">
      {{ $t('autoDelete.googleLoginTitle') }}
    </h3>

    <UAlert
      class="mb-4"
      color="warning"
      :title="$t('autoDelete.noticeTitle')"
      :description="$t('autoDelete.noticeDesc')"
      icon="i-lucide-alert-triangle"
    />

    <form
      class="space-y-4"
      @submit.prevent="handleLogin"
    >
      <UFormField :label="$t('autoDelete.googleEmail')">
        <UInput
          v-model="loginForm.email"
          type="email"
          :placeholder="$t('autoDelete.emailPlaceholder')"
          icon="i-lucide-mail"
          size="lg"
          required
          class="w-full"
        />
      </UFormField>

      <UFormField :label="$t('common.password')">
        <UInput
          v-model="loginForm.password"
          type="password"
          :placeholder="$t('autoDelete.passwordPlaceholder')"
          icon="i-lucide-lock"
          size="lg"
          required
          class="w-full"
        />
      </UFormField>

      <UFormField :label="$t('autoDelete.timeout')">
        <UInput
          v-model.number="loginForm.timeout"
          type="number"
          :min="30"
          :max="600"
          icon="i-lucide-timer"
          size="lg"
          class="w-full"
        />
      </UFormField>

      <UFormField :label="$t('autoDelete.browserMode')">
        <div class="flex gap-2">
          <UButton
            :label="$t('autoDelete.headless')"
            icon="i-lucide-monitor-off"
            size="sm"
            :color="loginForm.headless ? 'primary' : 'neutral'"
            :variant="loginForm.headless ? 'solid' : 'outline'"
            @click="loginForm.headless = true"
          />
          <UButton
            :label="$t('autoDelete.showBrowser')"
            icon="i-lucide-monitor"
            size="sm"
            :color="!loginForm.headless ? 'primary' : 'neutral'"
            :variant="!loginForm.headless ? 'solid' : 'outline'"
            @click="loginForm.headless = false"
          />
        </div>
        <p class="text-xs text-muted mt-1">
          {{
            loginForm.headless
              ? $t('autoDelete.headlessHelp')
              : $t('autoDelete.showBrowserCaptcha')
          }}
        </p>
      </UFormField>

      <div class="flex gap-2">
        <UButton
          type="submit"
          :label="$t('autoDelete.loginBtn')"
          icon="i-lucide-log-in"
          :loading="autoDeleteStore.loginRunning"
          :disabled="autoDeleteStore.loginRunning"
        />
        <UButton
          v-if="
            autoDeleteStore.loginResult
              || autoDeleteStore.loginError
              || autoDeleteStore.loginLogs.length > 0
          "
          :label="$t('common.reset')"
          variant="outline"
          color="neutral"
          icon="i-lucide-rotate-ccw"
          @click="autoDeleteStore.resetLogin()"
        />
      </div>
    </form>
  </div>
</template>
