<script setup lang="ts">
const { t } = useI18n()

const steps = computed(() => [
  { step: '01', icon: 'i-lucide-youtube', title: t('landing.step1Title'), description: t('landing.step1Desc') },
  { step: '02', icon: 'i-lucide-brain', title: t('landing.step2Title'), description: t('landing.step2Desc') },
  { step: '03', icon: 'i-lucide-bot', title: t('landing.step3Title'), description: t('landing.step3Desc') },
  { step: '04', icon: 'i-lucide-chart-bar', title: t('landing.step4Title'), description: t('landing.step4Desc') }
])
</script>

<template>
  <section class="bg-elevated/30 border-y border-default">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28">
      <div class="text-center max-w-2xl mx-auto mb-16">
        <span class="inline-block text-xs font-semibold tracking-widest uppercase text-blue-500 dark:text-blue-400 mb-3">{{ $t('landing.howLabel') }}</span>
        <h2 class="text-3xl sm:text-4xl font-bold text-highlighted">
          {{ $t('landing.howTitle') }}
        </h2>
        <p class="mt-4 text-lg text-muted">
          {{ $t('landing.howDesc') }}
        </p>
      </div>

      <div class="flex flex-col sm:grid sm:grid-cols-2 lg:flex lg:flex-row lg:items-stretch gap-4">
        <template
          v-for="(item, idx) in steps"
          :key="item.step"
        >
          <div class="flex-1 flex flex-col bg-default border border-default rounded-2xl p-6 text-center group hover:shadow-lg transition-all">
            <div class="inline-flex items-center justify-center w-14 h-14 rounded-full bg-blue-50 dark:bg-blue-950/50 border-2 border-blue-200 dark:border-blue-800 mb-4 mx-auto">
              <UIcon
                :name="item.icon"
                class="text-xl text-blue-600 dark:text-blue-400"
              />
            </div>
            <div class="text-xs font-bold text-blue-500/70 dark:text-blue-400/70 tracking-widest mb-1.5">
              {{ item.step }}
            </div>
            <h3 class="text-base font-semibold text-highlighted mb-2">
              {{ item.title }}
            </h3>
            <p class="text-xs text-muted leading-relaxed mt-auto">
              {{ item.description }}
            </p>
          </div>

          <div
            v-if="idx < steps.length - 1"
            class="hidden lg:flex items-center justify-center shrink-0 text-muted"
          >
            <UIcon
              name="i-lucide-chevron-right"
              class="text-2xl"
            />
          </div>
        </template>
      </div>
    </div>
  </section>
</template>
