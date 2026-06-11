<script setup lang="ts">
const { t } = useI18n()

const features = computed(() => [
  {
    icon: 'i-lucide-shield-off',
    title: t('landing.featureAutoDelete'),
    description: t('landing.featureAutoDeleteDesc'),
    color: 'red',
    tag: t('landing.featureAutoDeleteTag')
  },
  {
    icon: 'i-lucide-sparkles',
    title: t('landing.featurePredict'),
    description: t('landing.featurePredictDesc'),
    color: 'yellow',
    tag: t('landing.featurePredictTag')
  }
])

const featureColor = (color: string) => {
  const map: Record<string, string> = {
    red: 'bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400',
    yellow: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-950 dark:text-yellow-400'
  }
  return map[color] || map.red
}

const tagColor = (color: string) => {
  const map: Record<string, string> = {
    red: 'bg-red-50 text-red-600 border border-red-200 dark:bg-red-950/50 dark:text-red-400 dark:border-red-800',
    yellow: 'bg-yellow-50 text-yellow-600 border border-yellow-200 dark:bg-yellow-950/50 dark:text-yellow-400 dark:border-yellow-800'
  }
  return map[color] || map.red
}
</script>

<template>
  <section class="py-20 sm:py-28">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center max-w-2xl mx-auto mb-16">
        <span class="inline-block text-xs font-semibold tracking-widest uppercase text-blue-500 dark:text-blue-400 mb-3">{{ $t('landing.featuresLabel') }}</span>
        <h2 class="text-3xl sm:text-4xl font-bold text-highlighted">
          {{ $t('landing.featuresTitle') }}
        </h2>
        <p class="mt-4 text-lg text-muted">
          {{ $t('landing.featuresDesc') }}
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-8 max-w-3xl mx-auto">
        <div
          v-for="feature in features"
          :key="feature.title"
          class="relative bg-default border border-default rounded-2xl p-7 hover:shadow-xl hover:border-blue-200 dark:hover:border-blue-800 transition-all group"
        >
          <div class="flex items-start justify-between mb-5">
            <div :class="['w-12 h-12 rounded-xl flex items-center justify-center', featureColor(feature.color)]">
              <UIcon
                :name="feature.icon"
                class="text-xl"
              />
            </div>
            <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', tagColor(feature.color)]">
              {{ feature.tag }}
            </span>
          </div>
          <h3 class="text-lg font-semibold text-highlighted mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            {{ feature.title }}
          </h3>
          <p class="text-sm text-muted leading-relaxed">
            {{ feature.description }}
          </p>
        </div>
      </div>
    </div>
  </section>
</template>
