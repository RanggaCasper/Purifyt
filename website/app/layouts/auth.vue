<template>
  <div class="min-h-screen bg-default flex flex-col">
    <!-- Back to landing -->
    <header class="px-6 py-4 flex items-center">
      <NuxtLink
        to="/"
        class="flex items-center gap-2 text-muted hover:text-highlighted transition-colors"
      >
        <UIcon
          name="i-lucide-arrow-left"
          class="text-base"
        />
        <span class="text-sm font-medium">{{ $t('common.backToHome') }}</span>
      </NuxtLink>
    </header>

    <div class="flex-1 flex items-center justify-center px-4 py-10">
      <div class="w-full max-w-sm bg-default border border-default rounded-2xl shadow-sm p-8">
        <slot />
      </div>
    </div>
  </div>
</template>
