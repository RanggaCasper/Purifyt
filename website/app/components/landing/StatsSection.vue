<template>
  <section class="border-y border-default bg-elevated/40">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
        <div>
          <p class="text-4xl font-bold text-highlighted tracking-tight">
            {{ $t('landing.stat99') }}
          </p>
          <p class="text-sm text-muted mt-1.5 font-medium">
            {{ $t('landing.statAccuracy') }}
          </p>
        </div>
        <div>
          <p class="text-4xl font-bold text-highlighted tracking-tight">
            {{ $t('landing.stat100k') }}
          </p>
          <p class="text-sm text-muted mt-1.5 font-medium">
            {{ $t('landing.statAnalyzed') }}
          </p>
        </div>
        <div>
          <p class="text-4xl font-bold text-highlighted tracking-tight">
            {{ $t('landing.statAuto') }}
          </p>
          <p class="text-sm text-muted mt-1.5 font-medium">
            {{ $t('landing.statSelenium') }}
          </p>
        </div>
      </div>
    </div>
  </section>
</template>
