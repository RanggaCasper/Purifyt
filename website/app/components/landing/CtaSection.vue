<template>
  <section class="bg-linear-to-br from-blue-700 via-blue-600 to-blue-500 relative overflow-hidden">
    <!-- Pattern -->
    <div
      class="absolute inset-0 pointer-events-none"
      aria-hidden="true"
    >
      <svg
        class="w-full h-full opacity-10"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern
            id="cta-dots"
            x="0"
            y="0"
            width="24"
            height="24"
            patternUnits="userSpaceOnUse"
          >
            <circle
              cx="2"
              cy="2"
              r="1.5"
              fill="white"
            />
          </pattern>
        </defs>
        <rect
          width="100%"
          height="100%"
          fill="url(#cta-dots)"
        />
      </svg>
      <div class="absolute inset-0 bg-linear-to-b from-transparent to-blue-900/30" />
    </div>

    <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/15 border border-white/20 mb-6">
        <UIcon
          name="i-lucide-zap"
          class="text-yellow-300 text-sm"
        />
        <span class="text-sm font-medium text-white">{{ $t('landing.ctaFree') }}</span>
      </div>
      <h2 class="text-3xl sm:text-4xl font-bold text-white mb-4">
        {{ $t('landing.ctaTitle') }}
      </h2>
      <p class="text-lg text-blue-100 max-w-xl mx-auto mb-10">
        {{ $t('landing.ctaDesc') }}
      </p>
      <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
        <UButton
          to="/register"
          :label="$t('landing.ctaRegister')"
          color="neutral"
          variant="solid"
          size="xl"
        />
        <UButton
          to="/predict"
          :label="$t('landing.ctaTryPredict')"
          variant="ghost"
          size="xl"
          class="text-white hover:bg-white/15 border border-white/30"
        />
      </div>
    </div>
  </section>
</template>
