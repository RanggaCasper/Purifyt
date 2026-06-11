<script setup lang="ts">
definePageMeta({
  layout: 'landing',
  title: 'Terms of Service – Purifyt'
})
</script>

<template>
  <div class="min-h-screen">
    <!-- Hero -->
    <section class="py-16 sm:py-20 relative overflow-hidden">
      <div class="absolute -top-32 -right-32 w-96 h-96 bg-blue-400/5 dark:bg-blue-400/10 rounded-full blur-3xl" />
      <div class="relative max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <span class="inline-block text-xs font-semibold tracking-widest uppercase text-blue-500 dark:text-blue-400 mb-3">
          {{ $t('terms.label') }}
        </span>
        <h1 class="text-3xl sm:text-4xl font-bold text-highlighted">
          {{ $t('terms.title') }}
        </h1>
        <p class="mt-4 text-muted">
          {{ $t('privacy.lastUpdated') }}: 4 March 2026
        </p>
      </div>
    </section>

    <!-- Content -->
    <section class="pb-20 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('terms.acceptTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('terms.acceptDesc') }}
        </p>
      </div>

      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('terms.serviceTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('terms.serviceDesc') }}
        </p>
      </div>

      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('terms.accountTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('terms.accountDesc') }}
        </p>
      </div>

      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('terms.useTitle') }}
        </h2>
        <ul class="space-y-2 text-sm text-muted">
          <li class="flex gap-2">
            <UIcon
              name="i-lucide-check"
              class="text-emerald-500 mt-0.5 shrink-0"
            /> {{ $t('terms.useAllowed1') }}
          </li>
          <li class="flex gap-2">
            <UIcon
              name="i-lucide-check"
              class="text-emerald-500 mt-0.5 shrink-0"
            /> {{ $t('terms.useAllowed2') }}
          </li>
          <li class="flex gap-2">
            <UIcon
              name="i-lucide-x"
              class="text-red-500 mt-0.5 shrink-0"
            /> {{ $t('terms.useNotAllowed1') }}
          </li>
          <li class="flex gap-2">
            <UIcon
              name="i-lucide-x"
              class="text-red-500 mt-0.5 shrink-0"
            /> {{ $t('terms.useNotAllowed2') }}
          </li>
        </ul>
      </div>

      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('terms.disclaimerTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('terms.disclaimerDesc') }}
        </p>
      </div>

      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('terms.changesTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('terms.changesDesc') }}
        </p>
      </div>
    </section>
  </div>
</template>
