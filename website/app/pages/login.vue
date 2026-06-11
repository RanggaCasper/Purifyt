<script setup lang="ts">
definePageMeta({
  layout: 'auth',
  title: 'Login',
  middleware: ['guest']
})

const { login, loading: _authLoading } = useAuth()
const toast = useToast()
const { t } = useI18n()

const form = reactive({
  username: '',
  password: ''
})
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  loading.value = true

  try {
    await login({ username: form.username, password: form.password })
    toast.add({ title: t('auth.welcomeToast'), color: 'success' })
    navigateTo('/dashboard')
  } catch (e: unknown) {
    const err = e as Error
    error.value = err?.message || t('auth.invalidCredentials')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="w-full">
    <div class="text-center mb-8">
      <img
        src="/logo.png"
        alt="Purifyt"
        class="h-14 w-auto mx-auto mb-4"
      >
      <h1 class="text-2xl font-semibold text-highlighted">
        {{ $t('auth.welcomeBack') }}
      </h1>
      <p class="text-sm text-muted mt-1">
        {{ $t('auth.signInDesc') }}
      </p>
    </div>

    <form
      class="space-y-4"
      @submit.prevent="handleLogin"
    >
      <UAlert
        v-if="error"
        color="error"
        :title="error"
        icon="i-lucide-alert-circle"
      />

      <UFormField :label="$t('common.username')">
        <UInput
          v-model="form.username"
          :placeholder="$t('auth.enterUsername')"
          icon="i-lucide-user"
          size="lg"
          autofocus
          required
          class="w-full"
        />
      </UFormField>

      <UFormField :label="$t('common.password')">
        <UInput
          v-model="form.password"
          type="password"
          :placeholder="$t('auth.enterPassword')"
          icon="i-lucide-lock"
          size="lg"
          required
          class="w-full"
        />
      </UFormField>

      <UButton
        type="submit"
        :label="$t('auth.signIn')"
        :loading="loading"
        block
        size="lg"
        class="w-full"
      />
    </form>

    <p class="text-center text-sm text-muted mt-6">
      {{ $t('auth.noAccount') }}
      <NuxtLink
        to="/register"
        class="text-blue-500 hover:text-blue-600 font-medium"
      >
        {{ $t('common.register') }}
      </NuxtLink>
    </p>
  </div>
</template>
