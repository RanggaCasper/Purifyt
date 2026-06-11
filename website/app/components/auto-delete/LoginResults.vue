<script setup lang="ts">
const autoDeleteStore = useAutoDeleteStore()
const { getLogMeta } = useLogMeta()
</script>

<template>
  <div class="space-y-4">
    <!-- Live login log -->
    <TerminalLog
      v-if="autoDeleteStore.loginLogs.length > 0 || autoDeleteStore.loginRunning"
      :title="$t('autoDelete.loginLog')"
      :logs="autoDeleteStore.loginLogs"
      :running="autoDeleteStore.loginRunning"
      :log-meta="getLogMeta"
    />

    <!-- Login result -->
    <div
      v-if="autoDeleteStore.loginResult"
      class="bg-default border border-default rounded-xl p-5"
    >
      <div class="flex items-center gap-3 mb-3">
        <div class="w-10 h-10 bg-green-100 dark:bg-green-950 rounded-lg flex items-center justify-center">
          <UIcon
            name="i-lucide-check-circle"
            class="text-green-600 dark:text-green-400 text-xl"
          />
        </div>
        <div>
          <h3 class="font-medium text-sm text-highlighted">
            {{ $t('autoDelete.loginSuccess') }}
          </h3>
          <p class="text-xs text-muted">
            {{ $t('autoDelete.cookieSaved') }}
          </p>
        </div>
      </div>
      <div class="space-y-2 text-sm">
        <div class="flex items-center justify-between">
          <span class="text-muted">{{ $t('common.email') }}</span>
          <span class="font-medium text-highlighted">{{ autoDeleteStore.loginResult.email }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-muted">{{ $t('autoDelete.channel') }}</span>
          <span class="font-medium text-highlighted">{{ autoDeleteStore.loginResult.channelName }}</span>
        </div>
      </div>
    </div>

    <!-- Login error -->
    <UAlert
      v-if="autoDeleteStore.loginError && !autoDeleteStore.loginRunning"
      color="error"
      :title="autoDeleteStore.loginError"
      icon="i-lucide-alert-circle"
    />

    <!-- Empty state -->
    <div
      v-if="
        !autoDeleteStore.loginRunning
          && !autoDeleteStore.loginResult
          && !autoDeleteStore.loginError
          && autoDeleteStore.loginLogs.length === 0
      "
      class="bg-default border border-default rounded-xl p-12 flex flex-col items-center gap-3 text-center"
    >
      <UIcon
        name="i-lucide-log-in"
        class="text-4xl text-dimmed"
      />
      <h3 class="text-sm font-medium text-highlighted">
        {{ $t('autoDelete.loginWithGoogle') }}
      </h3>
      <p class="text-xs text-muted max-w-sm">
        {{ $t('autoDelete.loginOnceDesc') }}
      </p>
    </div>
  </div>
</template>
