<script setup lang="ts">
definePageMeta({
  layout: 'landing',
  title: 'Download Extension – Purifyt'
})

interface ReleaseAsset {
  name: string
  browser_download_url: string
  size: number
}

interface Release {
  id: number
  tag_name: string
  name: string
  body: string
  published_at: string
  prerelease: boolean
  html_url: string
  assets: ReleaseAsset[]
}

const GITHUB_OWNER = 'RanggaCasper'
const GITHUB_REPO = 'Purifyt-FE'

const { data: releases, status, error, refresh } = await useFetch<Release[]>(
  `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/releases`,
  {
    headers: { Accept: 'application/vnd.github+json' },
    default: () => []
  }
)

const latestRelease = computed(() => releases.value?.find(r => !r.prerelease) ?? releases.value?.[0] ?? null)
const olderReleases = computed(() => (releases.value ?? []).filter(r => r.id !== latestRelease.value?.id))

function formatSize(bytes: number): string {
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`
  if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(0)} KB`
  return `${bytes} B`
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

function getExtAsset(release: Release): ReleaseAsset | undefined {
  return release.assets.find(a => a.name.endsWith('.zip'))
}

function renderMarkdown(text: string): string {
  if (!text) return ''
  return text
    .replace(/### (.+)/g, '<h3 class="text-base font-semibold mt-3 mb-1">$1</h3>')
    .replace(/## (.+)/g, '<h2 class="text-lg font-bold mt-4 mb-2">$1</h2>')
    .replace(/# (.+)/g, '<h1 class="text-xl font-bold mt-4 mb-2">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="bg-elevated px-1.5 py-0.5 rounded text-sm">$1</code>')
    .replace(/^- (.+)/gm, '<li class="ml-4 list-disc text-sm text-muted">$1</li>')
    .replace(/^(\d+)\. (.+)/gm, '<li class="ml-4 list-decimal text-sm text-muted">$2</li>')
    .replace(/\n/g, '<br>')
}
</script>

<template>
  <div class="min-h-screen">
    <!-- Hero -->
    <section class="py-16 sm:py-20 relative overflow-hidden">
      <div class="absolute -top-32 -left-32 w-96 h-96 bg-blue-500/5 dark:bg-blue-500/10 rounded-full blur-3xl" />
      <div class="absolute -bottom-32 -right-32 w-96 h-96 bg-blue-400/5 dark:bg-blue-400/10 rounded-full blur-3xl" />

      <div class="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <span class="inline-block text-xs font-semibold tracking-widest uppercase text-blue-500 dark:text-blue-400 mb-3">
          {{ $t('download.label') }}
        </span>
        <h1 class="text-3xl sm:text-4xl font-bold text-highlighted">
          {{ $t('download.title') }}
        </h1>
        <p class="mt-4 text-lg text-muted max-w-2xl mx-auto">
          {{ $t('download.desc') }}
        </p>
      </div>
    </section>

    <!-- Content -->
    <section class="pb-20 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Loading -->
      <div
        v-if="status === 'pending'"
        class="text-center py-16"
      >
        <UIcon
          name="i-lucide-loader-2"
          class="text-3xl text-blue-500 animate-spin"
        />
        <p class="mt-3 text-muted">
          {{ $t('download.loading') }}
        </p>
      </div>

      <!-- Error -->
      <div
        v-else-if="error"
        class="text-center py-16"
      >
        <UIcon
          name="i-lucide-alert-triangle"
          class="text-3xl text-red-500"
        />
        <p class="mt-3 text-muted">
          {{ $t('download.errorFetch') }}
        </p>
        <UButton
          class="mt-4"
          variant="outline"
          icon="i-lucide-refresh-cw"
          @click="refresh()"
        >
          {{ $t('download.retry') }}
        </UButton>
      </div>

      <!-- No releases -->
      <div
        v-else-if="!releases || releases.length === 0"
        class="text-center py-16"
      >
        <UIcon
          name="i-lucide-package-x"
          class="text-4xl text-muted"
        />
        <p class="mt-3 text-muted">
          {{ $t('download.noReleases') }}
        </p>
      </div>

      <!-- Releases list -->
      <template v-else>
        <!-- Latest release (highlighted) -->
        <div
          v-if="latestRelease"
          class="mb-12"
        >
          <h2 class="text-sm font-semibold tracking-widest uppercase text-blue-500 dark:text-blue-400 mb-4">
            {{ $t('download.latestRelease') }}
          </h2>
          <div class="bg-default border border-blue-200 dark:border-blue-800 rounded-2xl overflow-hidden shadow-sm">
            <!-- Banner -->
            <div class="bg-linear-to-r from-blue-600 to-blue-400 px-6 py-5 text-white">
              <div class="flex items-center justify-between flex-wrap gap-3">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-white/15 backdrop-blur rounded-xl flex items-center justify-center">
                    <UIcon
                      name="i-lucide-package"
                      class="text-2xl"
                    />
                  </div>
                  <div>
                    <h3 class="text-lg font-bold">
                      {{ latestRelease.name || latestRelease.tag_name }}
                    </h3>
                    <p class="text-blue-100 text-sm">
                      {{ formatDate(latestRelease.published_at) }}
                    </p>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <span
                    v-if="latestRelease.prerelease"
                    class="text-xs px-2.5 py-1 rounded-full bg-yellow-500/20 text-yellow-100 border border-yellow-400/30 font-medium"
                  >
                    Pre-release
                  </span>
                  <span class="text-xs px-2.5 py-1 rounded-full bg-white/15 backdrop-blur-sm border border-white/20 font-medium">
                    {{ latestRelease.tag_name }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Body -->
            <div class="px-6 py-5">
              <!-- Release notes -->
              <div
                v-if="latestRelease.body"
                class="prose-sm mb-5"
                v-html="renderMarkdown(latestRelease.body)"
              />

              <!-- Assets -->
              <div
                v-if="getExtAsset(latestRelease)"
                class="flex flex-col sm:flex-row items-start sm:items-center gap-3"
              >
                <UButton
                  :to="getExtAsset(latestRelease)!.browser_download_url"
                  external
                  target="_blank"
                  icon="i-lucide-download"
                  size="lg"
                >
                  {{ $t('download.downloadZip') }} ({{ formatSize(getExtAsset(latestRelease)!.size) }})
                </UButton>
                <span class="text-xs text-muted">
                  {{ $t('download.installNote') }}
                </span>
              </div>
              <div
                v-else
                class="text-sm text-muted"
              >
                <UButton
                  :to="latestRelease.html_url"
                  external
                  target="_blank"
                  variant="outline"
                  icon="i-lucide-external-link"
                >
                  {{ $t('download.viewOnGithub') }}
                </UButton>
              </div>
            </div>
          </div>
        </div>

        <!-- Installation guide -->
        <div class="mb-12 bg-default border border-default rounded-2xl px-6 py-5">
          <h2 class="text-lg font-bold text-highlighted mb-4 flex items-center gap-2">
            <UIcon
              name="i-lucide-book-open"
              class="text-blue-500"
            />
            {{ $t('download.installTitle') }}
          </h2>
          <ol class="space-y-3 text-sm text-muted">
            <li class="flex gap-3">
              <span class="w-6 h-6 shrink-0 rounded-full bg-blue-500 text-white text-xs font-bold flex items-center justify-center">1</span>
              <span>{{ $t('download.step1') }}</span>
            </li>
            <li class="flex gap-3">
              <span class="w-6 h-6 shrink-0 rounded-full bg-blue-500 text-white text-xs font-bold flex items-center justify-center">2</span>
              <span>{{ $t('download.step2') }}</span>
            </li>
            <li class="flex gap-3">
              <span class="w-6 h-6 shrink-0 rounded-full bg-blue-500 text-white text-xs font-bold flex items-center justify-center">3</span>
              <span>{{ $t('download.step3') }}</span>
            </li>
            <li class="flex gap-3">
              <span class="w-6 h-6 shrink-0 rounded-full bg-blue-500 text-white text-xs font-bold flex items-center justify-center">4</span>
              <span>{{ $t('download.step4') }}</span>
            </li>
            <li class="flex gap-3">
              <span class="w-6 h-6 shrink-0 rounded-full bg-blue-500 text-white text-xs font-bold flex items-center justify-center">5</span>
              <span>{{ $t('download.step5') }}</span>
            </li>
          </ol>
        </div>

        <!-- Older releases -->
        <div v-if="olderReleases.length > 0">
          <h2 class="text-sm font-semibold tracking-widest uppercase text-muted mb-4">
            {{ $t('download.olderReleases') }}
          </h2>
          <div class="space-y-3">
            <div
              v-for="rel in olderReleases"
              :key="rel.id"
              class="bg-default border border-default rounded-xl px-5 py-4 flex items-center justify-between flex-wrap gap-3"
            >
              <div>
                <h3 class="font-semibold text-highlighted text-sm">
                  {{ rel.name || rel.tag_name }}
                </h3>
                <p class="text-xs text-muted mt-0.5">
                  {{ formatDate(rel.published_at) }}
                  <span
                    v-if="rel.prerelease"
                    class="ml-2 text-yellow-500 font-medium"
                  >Pre-release</span>
                </p>
              </div>
              <div class="flex items-center gap-2">
                <UButton
                  v-if="getExtAsset(rel)"
                  :to="getExtAsset(rel)!.browser_download_url"
                  external
                  target="_blank"
                  variant="outline"
                  size="xs"
                  icon="i-lucide-download"
                >
                  .zip ({{ formatSize(getExtAsset(rel)!.size) }})
                </UButton>
                <UButton
                  :to="rel.html_url"
                  external
                  target="_blank"
                  variant="ghost"
                  size="xs"
                  icon="i-lucide-external-link"
                >
                  GitHub
                </UButton>
              </div>
            </div>
          </div>
        </div>
      </template>
    </section>
  </div>
</template>
