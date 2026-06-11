<script setup lang="ts">
const features = [
  { icon: 'i-lucide-shield-check', text: 'extensionFeature1' },
  { icon: 'i-lucide-eye-off', text: 'extensionFeature2' },
  { icon: 'i-lucide-zap', text: 'extensionFeature3' },
  { icon: 'i-lucide-lock', text: 'extensionFeature4' }
]

const platforms = [
  { name: 'YouTube', icon: 'i-simple-icons-youtube', active: true },
  { name: 'Facebook', icon: 'i-simple-icons-facebook', active: false },
  { name: 'Instagram', icon: 'i-simple-icons-instagram', active: false },
  { name: 'TikTok', icon: 'i-simple-icons-tiktok', active: false }
]
</script>

<template>
  <section class="py-20 sm:py-28 relative overflow-hidden">
    <!-- Background accent -->
    <div class="absolute -top-32 -left-32 w-96 h-96 bg-blue-500/5 dark:bg-blue-500/10 rounded-full blur-3xl" />
    <div class="absolute -bottom-32 -right-32 w-96 h-96 bg-blue-400/5 dark:bg-blue-400/10 rounded-full blur-3xl" />

    <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="text-center max-w-2xl mx-auto mb-16">
        <span class="inline-block text-xs font-semibold tracking-widest uppercase text-blue-500 dark:text-blue-400 mb-3">
          {{ $t('landing.extensionLabel') }}
        </span>
        <h2 class="text-3xl sm:text-4xl font-bold text-highlighted">
          {{ $t('landing.extensionTitle') }}
        </h2>
        <p class="mt-4 text-lg text-muted">
          {{ $t('landing.extensionDesc') }}
        </p>
      </div>

      <!-- Card -->
      <div class="max-w-3xl mx-auto bg-default border border-default rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-shadow">
        <!-- Top: gradient banner -->
        <div class="bg-linear-to-r from-blue-600 to-blue-400 px-8 py-8 text-white relative">
          <div class="flex items-start justify-between gap-4 flex-wrap">
            <div class="flex items-center gap-4">
              <div class="w-16 h-16 bg-white/15 backdrop-blur rounded-2xl flex items-center justify-center shrink-0">
                <img
                  src="/logo.png"
                  alt="Purifyt Extension"
                  class="w-10 h-10 rounded-lg"
                >
              </div>
              <div>
                <h3 class="text-xl font-bold">
                  Purifyt Browser Extension
                </h3>
                <p class="text-blue-100 text-sm mt-1">
                  {{ $t('landing.extensionTagline') }}
                </p>
              </div>
            </div>
            <!-- Badges -->
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/40 text-emerald-100">
                Manifest V3
              </span>
              <span class="text-xs font-semibold px-2.5 py-1 rounded-full bg-white/15 border border-white/20">
                Chrome · Edge · Brave
              </span>
            </div>
          </div>

          <!-- Platform tags -->
          <div class="flex flex-wrap gap-2 mt-5">
            <span
              v-for="p in platforms"
              :key="p.name"
              class="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border transition-all"
              :class="p.active
                ? 'bg-white/20 border-white/30 text-white'
                : 'bg-white/5 border-white/10 text-white/40'"
            >
              <UIcon
                :name="p.icon"
                class="text-sm"
              />
              {{ p.name }}
              <span
                v-if="!p.active"
                class="text-[10px] font-normal opacity-70"
              >soon</span>
            </span>
          </div>
        </div>

        <!-- Bottom: features + download button -->
        <div class="px-8 py-7">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
            <div
              v-for="f in features"
              :key="f.text"
              class="flex items-start gap-3"
            >
              <div class="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-950 flex items-center justify-center shrink-0 mt-0.5">
                <UIcon
                  :name="f.icon"
                  class="text-blue-500 text-base"
                />
              </div>
              <p class="text-sm text-muted leading-relaxed">
                {{ $t(`landing.${f.text}`) }}
              </p>
            </div>
          </div>

          <div class="flex flex-col sm:flex-row items-center gap-3">
            <UButton
              :label="$t('landing.extensionDownload')"
              icon="i-lucide-download"
              size="lg"
              class="w-full sm:w-auto"
              to="/download"
            />
            <UButton
              :label="$t('landing.extensionChangelog')"
              icon="i-lucide-history"
              size="lg"
              variant="ghost"
              color="neutral"
              class="w-full sm:w-auto"
              to="/download"
            />
          </div>
          <p class="text-xs text-muted mt-3">
            {{ $t('landing.extensionNote') }}
          </p>
        </div>
      </div>
    </div>
  </section>
</template>
