<template>
  <section class="py-20 sm:py-28">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center max-w-2xl mx-auto mb-12">
        <span class="inline-block text-xs font-semibold tracking-widest uppercase text-blue-500 dark:text-blue-400 mb-3">{{ $t('landing.demoLabel') }}</span>
        <h2 class="text-3xl sm:text-4xl font-bold text-highlighted">
          {{ $t('landing.demoTitle') }}
        </h2>
        <p class="mt-4 text-lg text-muted">
          {{ $t('landing.demoDesc') }}
        </p>
      </div>

      <div class="max-w-2xl mx-auto rounded-2xl overflow-hidden shadow-2xl border border-slate-700 dark:border-neutral-800">
        <!-- Window chrome -->
        <div class="flex items-center gap-2 px-4 py-3 bg-slate-800 dark:bg-neutral-900">
          <div class="flex gap-1.5">
            <span class="w-3 h-3 rounded-full bg-red-500" />
            <span class="w-3 h-3 rounded-full bg-yellow-500" />
            <span class="w-3 h-3 rounded-full bg-green-500" />
          </div>
          <span class="text-xs font-mono text-neutral-400 ml-2">scan.log</span>
        </div>

        <!-- Log body -->
        <div class="px-4 py-4 space-y-2 bg-slate-900 dark:bg-neutral-950 font-mono text-xs">
          <div class="flex items-center gap-2.5">
            <UIcon
              name="i-lucide-info"
              class="text-sky-400 shrink-0"
            />
            <span class="text-neutral-300">{{ $t('landing.demoLog1') }}</span>
          </div>
          <div class="flex items-center gap-2.5">
            <UIcon
              name="i-lucide-info"
              class="text-sky-400 shrink-0"
            />
            <span class="text-neutral-300">{{ $t('landing.demoLog2') }} <span class="text-emerald-400">✓</span></span>
          </div>
          <div class="flex items-center gap-2.5">
            <UIcon
              name="i-lucide-message-square"
              class="text-violet-400 shrink-0"
            />
            <span class="text-neutral-300">{{ $t('landing.demoLog3') }}</span>
          </div>
          <div class="flex items-center gap-2.5">
            <UIcon
              name="i-lucide-message-square"
              class="text-violet-400 shrink-0"
            />
            <span class="text-neutral-300">{{ $t('landing.demoLog4') }} <span class="text-emerald-400">✓</span></span>
          </div>
          <div class="flex items-center gap-2.5">
            <UIcon
              name="i-lucide-sparkles"
              class="text-yellow-400 shrink-0"
            />
            <span class="text-neutral-300">{{ $t('landing.demoLog5') }}</span>
          </div>
          <div class="flex items-center gap-2.5">
            <UIcon
              name="i-lucide-sparkles"
              class="text-yellow-400 shrink-0"
            />
            <span class="text-neutral-300">{{ $t('landing.demoLog6') }} <span class="text-emerald-400">✓</span></span>
          </div>
          <div class="flex items-center gap-2.5">
            <UIcon
              name="i-lucide-info"
              class="text-sky-400 shrink-0"
            />
            <span class="text-neutral-300">{{ $t('landing.demoLog7') }}</span>
          </div>
          <div class="flex items-center gap-2.5">
            <UIcon
              name="i-lucide-circle-check-big"
              class="text-emerald-400 shrink-0"
            />
            <span class="text-emerald-300 font-semibold">{{ $t('landing.demoLog8') }}</span>
          </div>
        </div>

        <!-- Progress bar -->
        <div class="px-4 py-3 bg-slate-800/80 dark:bg-neutral-900 border-t border-slate-700 dark:border-neutral-800">
          <div class="flex items-center justify-between text-xs font-mono mb-2">
            <span class="text-slate-400 dark:text-neutral-400">{{ $t('landing.demoProgress') }}</span>
            <span class="text-slate-300 dark:text-neutral-300 font-medium">57/57 (100.0%)</span>
          </div>
          <div class="h-1.5 bg-slate-700 dark:bg-neutral-800 rounded-full overflow-hidden">
            <div class="h-full w-full bg-blue-500 rounded-full" />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
