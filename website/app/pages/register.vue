<script setup lang="ts">
definePageMeta({
  layout: 'auth',
  title: 'Register',
  middleware: ['guest']
})

const { register, loading: _authLoading } = useAuth()
const toast = useToast()
const { t } = useI18n()

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  error.value = ''

  if (form.password !== form.confirmPassword) {
    error.value = t('auth.passwordsMismatch')
    return
  }

  loading.value = true

  try {
    await register({
      username: form.username,
      email: form.email,
      password: form.password
    })
    toast.add({ title: t('auth.accountCreated'), color: 'success' })
    navigateTo('/login')
  } catch (e: unknown) {
    const err = e as Error
    error.value = err?.message || t('auth.registrationFailed')
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
        {{ $t("auth.createAccount") }}
      </h1>
      <p class="text-sm text-muted mt-1">
        {{ $t("auth.registerDesc") }}
      </p>
    </div>

    <form
      class="space-y-4"
      @submit.prevent="handleRegister"
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
          :placeholder="$t('auth.chooseUsername')"
          icon="i-lucide-user"
          size="lg"
          autofocus
          required
          class="w-full"
        />
      </UFormField>

      <UFormField :label="$t('common.email')">
        <UInput
          v-model="form.email"
          type="email"
          :placeholder="$t('auth.enterEmail')"
          icon="i-lucide-mail"
          size="lg"
          required
          class="w-full"
        />
      </UFormField>

      <UFormField :label="$t('common.password')">
        <UInput
          v-model="form.password"
          type="password"
          :placeholder="$t('auth.createPassword')"
          icon="i-lucide-lock"
          size="lg"
          required
          class="w-full"
        />
      </UFormField>

      <UFormField :label="$t('auth.confirmPassword')">
        <UInput
          v-model="form.confirmPassword"
          type="password"
          :placeholder="$t('auth.confirmPasswordPlaceholder')"
          icon="i-lucide-lock"
          size="lg"
          required
          class="w-full"
        />
      </UFormField>

      <UButton
        type="submit"
        :label="$t('auth.createAccount')"
        :loading="loading"
        block
        size="lg"
        class="w-full"
      />
    </form>

    <p class="text-center text-sm text-muted mt-6">
      {{ $t("auth.haveAccount") }}
      <NuxtLink
        to="/login"
        class="text-blue-500 hover:text-blue-600 font-medium"
      >
        {{ $t("auth.signIn") }}
      </NuxtLink>
    </p>
  </div>
</template>
