<template>
  <section class="relative overflow-hidden">
    <!-- Background pattern -->
    <div
      class="absolute inset-0 pointer-events-none select-none"
      aria-hidden="true"
    >
      <svg
        class="absolute inset-0 w-full h-full opacity-[0.04] dark:opacity-[0.07]"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern
            id="hero-dots"
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
              fill="currentColor"
            />
          </pattern>
        </defs>
        <rect
          width="100%"
          height="100%"
          fill="url(#hero-dots)"
        />
      </svg>
      <div class="absolute inset-0 bg-linear-to-b from-transparent via-transparent to-default" />
    </div>

    <!-- Blobs -->
    <div class="absolute -top-32 -right-32 w-md h-112 bg-blue-500/10 dark:bg-blue-500/20 rounded-full blur-3xl" />
    <div class="absolute top-24 -left-24 w-64 h-64 bg-blue-400/10 dark:bg-blue-400/15 rounded-full blur-3xl" />

    <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32 lg:py-44">
      <div class="text-center max-w-3xl mx-auto">
        <!-- Badge -->
        <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 mb-8">
          <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <span class="text-sm font-medium text-blue-700 dark:text-blue-300">{{ $t('landing.badge') }}</span>
        </div>

        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold text-highlighted leading-tight tracking-tight">
          {{ $t('landing.heroTitle1') }}
          <span class="text-transparent bg-clip-text bg-linear-to-r from-blue-600 to-blue-400">{{ $t('landing.heroTitle2') }}</span>
        </h1>

        <p class="mt-6 text-lg sm:text-xl text-muted max-w-2xl mx-auto leading-relaxed">
          {{ $t('landing.heroDesc') }}
        </p>

        <!-- CTA -->
        <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10">
          <UButton
            to="/register"
            :label="$t('landing.ctaStart')"
            size="xl"
            icon="i-lucide-shield-check"
          />
          <UButton
            to="/login"
            :label="$t('landing.ctaLogin')"
            variant="outline"
            color="neutral"
            size="xl"
          />
        </div>
      </div>
    </div>
  </section>
</template>
