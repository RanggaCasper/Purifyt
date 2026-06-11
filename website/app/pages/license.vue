<script setup lang="ts">
definePageMeta({
  layout: 'landing',
  title: 'License – Purifyt'
})
</script>

<template>
  <div class="min-h-screen">
    <!-- Hero -->
    <section class="py-16 sm:py-20 relative overflow-hidden">
      <div class="absolute -top-32 -left-32 w-96 h-96 bg-blue-500/5 dark:bg-blue-500/10 rounded-full blur-3xl" />
      <div class="relative max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <span class="inline-block text-xs font-semibold tracking-widest uppercase text-blue-500 dark:text-blue-400 mb-3">
          {{ $t('license.label') }}
        </span>
        <h1 class="text-3xl sm:text-4xl font-bold text-highlighted">
          {{ $t('license.title') }}
        </h1>
        <p class="mt-4 text-muted">
          {{ $t('license.subtitle') }}
        </p>
      </div>
    </section>

    <!-- Content -->
    <section class="pb-20 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="bg-default border border-default rounded-2xl px-6 py-6">
        <pre class="whitespace-pre-wrap text-sm text-muted leading-relaxed font-mono">MIT License

Copyright (c) {{ new Date().getFullYear() }} Purifyt by RanggaCasper

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.</pre>
      </div>

      <div class="mt-6 text-center">
        <UButton
          to="https://github.com/RanggaCasper/Purifyt-FE/blob/main/LICENSE"
          external
          target="_blank"
          variant="outline"
          icon="i-simple-icons-github"
        >
          {{ $t('license.viewOnGithub') }}
        </UButton>
      </div>
    </section>
  </div>
</template>
