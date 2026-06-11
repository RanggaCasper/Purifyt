<script setup lang="ts">
definePageMeta({
  layout: 'landing',
  title: 'Privacy Policy – Purifyt'
})
</script>

<template>
  <div class="min-h-screen">
    <!-- Hero -->
    <section class="py-16 sm:py-20 relative overflow-hidden">
      <div class="absolute -top-32 -right-32 w-96 h-96 bg-blue-400/5 dark:bg-blue-400/10 rounded-full blur-3xl" />
      <div class="relative max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <span class="inline-block text-xs font-semibold tracking-widest uppercase text-blue-500 dark:text-blue-400 mb-3">
          {{ $t('privacy.label') }}
        </span>
        <h1 class="text-3xl sm:text-4xl font-bold text-highlighted">
          {{ $t('privacy.title') }}
        </h1>
        <p class="mt-4 text-muted">
          {{ $t('privacy.lastUpdated') }}: 4 March 2026
        </p>
      </div>
    </section>

    <!-- Content -->
    <section class="pb-20 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      <!-- Overview -->
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('privacy.overviewTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('privacy.overviewDesc') }}
        </p>
      </div>

      <!-- Data we collect -->
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('privacy.collectTitle') }}
        </h2>
        <ul class="space-y-2 text-sm text-muted">
          <li class="flex gap-2">
            <UIcon
              name="i-lucide-user"
              class="text-blue-500 mt-0.5 shrink-0"
            /> {{ $t('privacy.collectAccount') }}
          </li>
          <li class="flex gap-2">
            <UIcon
              name="i-lucide-message-square"
              class="text-blue-500 mt-0.5 shrink-0"
            /> {{ $t('privacy.collectComments') }}
          </li>
          <li class="flex gap-2">
            <UIcon
              name="i-lucide-activity"
              class="text-blue-500 mt-0.5 shrink-0"
            /> {{ $t('privacy.collectUsage') }}
          </li>
        </ul>
      </div>

      <!-- How we use -->
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('privacy.useTitle') }}
        </h2>
        <ul class="space-y-2 text-sm text-muted">
          <li class="flex gap-2">
            <UIcon
              name="i-lucide-shield-check"
              class="text-blue-500 mt-0.5 shrink-0"
            /> {{ $t('privacy.useDetect') }}
          </li>
          <li class="flex gap-2">
            <UIcon
              name="i-lucide-bar-chart-3"
              class="text-blue-500 mt-0.5 shrink-0"
            /> {{ $t('privacy.useImprove') }}
          </li>
          <li class="flex gap-2">
            <UIcon
              name="i-lucide-lock"
              class="text-blue-500 mt-0.5 shrink-0"
            /> {{ $t('privacy.useAuth') }}
          </li>
        </ul>
      </div>

      <!-- Extension data -->
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('privacy.extensionTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('privacy.extensionDesc') }}
        </p>
      </div>

      <!-- Third party -->
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('privacy.thirdPartyTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('privacy.thirdPartyDesc') }}
        </p>
      </div>

      <!-- Contact -->
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3">
          {{ $t('privacy.contactTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('privacy.contactDesc') }}
        </p>
        <UButton
          to="https://github.com/RanggaCasper/Purifyt-FE/issues"
          external
          target="_blank"
          variant="outline"
          size="sm"
          icon="i-simple-icons-github"
          class="mt-4"
        >
          {{ $t('about.openIssue') }}
        </UButton>
      </div>
    </section>
  </div>
</template>
