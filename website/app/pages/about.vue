<script setup lang="ts">
definePageMeta({
  layout: 'landing',
  title: 'About Us – Purifyt'
})

const team = [
  {
    name: 'Rangga Casper',
    role: 'Creator & Lead Developer',
    avatar: 'RC',
    github: 'https://github.com/RanggaCasper'
  }
]
</script>

<template>
  <div class="min-h-screen">
    <!-- Hero -->
    <section class="py-16 sm:py-20 relative overflow-hidden">
      <div class="absolute -top-32 -left-32 w-96 h-96 bg-blue-500/5 dark:bg-blue-500/10 rounded-full blur-3xl" />
      <div class="relative max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <span class="inline-block text-xs font-semibold tracking-widest uppercase text-blue-500 dark:text-blue-400 mb-3">
          {{ $t('about.label') }}
        </span>
        <h1 class="text-3xl sm:text-4xl font-bold text-highlighted">
          {{ $t('about.title') }}
        </h1>
        <p class="mt-4 text-lg text-muted max-w-2xl mx-auto">
          {{ $t('about.desc') }}
        </p>
      </div>
    </section>

    <!-- Content -->
    <section class="pb-20 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
      <!-- Mission -->
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3 flex items-center gap-2">
          <UIcon
            name="i-lucide-target"
            class="text-blue-500"
          />
          {{ $t('about.missionTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('about.missionDesc') }}
        </p>
      </div>

      <!-- What is Purifyt -->
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3 flex items-center gap-2">
          <UIcon
            name="i-lucide-info"
            class="text-blue-500"
          />
          {{ $t('about.whatTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('about.whatDesc') }}
        </p>
      </div>

      <!-- Tech -->
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-4 flex items-center gap-2">
          <UIcon
            name="i-lucide-cpu"
            class="text-blue-500"
          />
          {{ $t('about.techTitle') }}
        </h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <div
            v-for="tech in ['Nuxt 4', 'Tailwind CSS', 'FastAPI', 'Scikit-learn', 'Selenium', 'Chrome Extension MV3']"
            :key="tech"
            class="bg-elevated rounded-xl px-4 py-3 text-center text-sm font-medium text-highlighted"
          >
            {{ tech }}
          </div>
        </div>
      </div>

      <!-- Team -->
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-4 flex items-center gap-2">
          <UIcon
            name="i-lucide-users"
            class="text-blue-500"
          />
          {{ $t('about.teamTitle') }}
        </h2>
        <div class="space-y-3">
          <div
            v-for="m in team"
            :key="m.name"
            class="flex items-center gap-4 bg-elevated rounded-xl px-5 py-4"
          >
            <div class="w-12 h-12 rounded-full bg-blue-500 text-white flex items-center justify-center text-lg font-bold shrink-0">
              {{ m.avatar }}
            </div>
            <div class="flex-1">
              <p class="font-semibold text-highlighted">
                {{ m.name }}
              </p>
              <p class="text-sm text-muted">
                {{ m.role }}
              </p>
            </div>
            <UButton
              v-if="m.github"
              :to="m.github"
              external
              target="_blank"
              variant="ghost"
              size="xs"
              icon="i-simple-icons-github"
            />
          </div>
        </div>
      </div>

      <!-- Contact -->
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <h2 class="text-lg font-bold text-highlighted mb-3 flex items-center gap-2">
          <UIcon
            name="i-lucide-mail"
            class="text-blue-500"
          />
          {{ $t('about.contactTitle') }}
        </h2>
        <p class="text-sm text-muted leading-relaxed">
          {{ $t('about.contactDesc') }}
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
