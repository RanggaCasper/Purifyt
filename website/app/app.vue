<script setup lang="ts">
useHead({
  meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
  link: [
    { rel: 'icon', href: '/logo.png' },
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
    {
      rel: 'stylesheet',
      href:
        'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap'
    }
  ],
  htmlAttrs: {
    lang: 'en'
  }
})

const title = 'Purifyt – Deteksi Komentar Judi Online'
const description
  = 'Platform deteksi komentar judi online di YouTube menggunakan AI. Lindungi konten Anda dari spam judi.'

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description
})

const { authReady } = useAuth()
</script>

<template>
  <UApp>
    <div
      v-if="!authReady"
      class="fixed inset-0 z-9999 flex items-center justify-center bg-default"
    >
      <UIcon
        name="i-lucide-loader-circle"
        class="text-3xl text-blue-500 animate-spin"
      />
    </div>

    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
