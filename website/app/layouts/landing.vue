<script setup lang="ts">
import { useColorMode } from '#imports'

const colorMode = useColorMode()
const { isAuthenticated } = useAuth()
const { locale, setLocale } = useI18n()

const toggleDarkMode = () => {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}

const toggleLocale = () => {
  setLocale(locale.value === 'id' ? 'en' : 'id')
}
</script>

<template>
  <div class="min-h-screen bg-default">
    <!-- Navbar -->
    <header
      class="sticky top-0 z-50 bg-default/80 backdrop-blur-md border-b border-default"
    >
      <div
        class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between"
      >
        <NuxtLink
          to="/"
          class="flex items-center gap-2"
        >
          <img
            src="/logo.png"
            alt="Purifyt"
            class="h-9 w-auto"
          >
          <span class="text-xl font-semibold text-highlighted">Purifyt</span>
        </NuxtLink>

        <div class="flex items-center gap-3">
          <button
            class="w-9 h-9 rounded-lg flex items-center justify-center text-muted hover:bg-elevated hover:text-highlighted transition-colors text-xs font-semibold"
            :title="locale === 'id' ? 'Switch to English' : 'Ganti ke Bahasa Indonesia'"
            @click="toggleLocale"
          >
            {{ locale === "id" ? "EN" : "ID" }}
          </button>
          <button
            class="w-9 h-9 rounded-lg flex items-center justify-center text-muted hover:bg-elevated hover:text-highlighted transition-colors"
            @click="toggleDarkMode"
          >
            <UIcon
              :name="colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon'"
              class="text-lg"
            />
          </button>
          <template v-if="isAuthenticated">
            <UButton
              to="/dashboard"
              :label="$t('common.dashboard')"
              variant="outline"
              color="neutral"
              size="sm"
            />
          </template>
          <template v-else>
            <UButton
              to="/login"
              :label="$t('common.login')"
              variant="ghost"
              color="neutral"
              size="sm"
            />
            <UButton
              to="/register"
              :label="$t('common.getStarted')"
              size="sm"
            />
          </template>
        </div>
      </div>
    </header>

    <slot />

    <!-- Footer -->
    <footer class="border-t border-default bg-default">
      <!-- Upper footer -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-14 pb-10">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-10">
          <!-- Brand -->
          <div class="lg:col-span-2">
            <div class="flex items-center gap-2 mb-4">
              <img
                src="/logo.png"
                alt="Purifyt"
                class="h-9 w-auto shrink-0"
              >
              <span class="text-xl font-bold text-highlighted">Purifyt</span>
            </div>
            <p class="text-sm text-muted leading-relaxed max-w-xs">
              {{ $t("footer.desc") }}
            </p>
            <div class="flex items-center gap-1.5 mt-5">
              <span class="inline-block w-2 h-2 rounded-full bg-emerald-500" />
              <span class="text-xs text-muted">{{ $t("footer.modelActive") }}</span>
            </div>
          </div>

          <!-- Fitur -->
          <div>
            <h4 class="text-sm font-semibold text-highlighted mb-4">
              {{ $t("footer.features") }}
            </h4>
            <ul class="space-y-2.5">
              <li>
                <NuxtLink
                  to="/register"
                  class="text-sm text-muted hover:text-highlighted transition-colors flex items-center gap-1.5"
                >
                  <UIcon
                    name="i-lucide-shield-off"
                    class="text-xs text-blue-400"
                  />
                  {{ $t("landing.featureAutoDelete") }}
                </NuxtLink>
              </li>
              <li>
                <NuxtLink
                  to="/predict"
                  class="text-sm text-muted hover:text-highlighted transition-colors flex items-center gap-1.5"
                >
                  <UIcon
                    name="i-lucide-sparkles"
                    class="text-xs text-blue-400"
                  />
                  {{ $t("landing.featurePredict") }}
                </NuxtLink>
              </li>
              <li>
                <NuxtLink
                  to="/download"
                  class="text-sm text-muted hover:text-highlighted transition-colors flex items-center gap-1.5"
                >
                  <UIcon
                    name="i-lucide-download"
                    class="text-xs text-blue-400"
                  />
                  {{ $t("footer.extension") }}
                </NuxtLink>
              </li>
            </ul>
          </div>

          <!-- Akun -->
          <div>
            <h4 class="text-sm font-semibold text-highlighted mb-4">
              {{ $t("footer.account") }}
            </h4>
            <ul class="space-y-2.5">
              <li>
                <NuxtLink
                  to="/login"
                  class="text-sm text-muted hover:text-highlighted transition-colors"
                >{{ $t("common.login") }}</NuxtLink>
              </li>
              <li>
                <NuxtLink
                  to="/register"
                  class="text-sm text-muted hover:text-highlighted transition-colors"
                >{{ $t("footer.register") }}</NuxtLink>
              </li>
              <li v-if="isAuthenticated">
                <NuxtLink
                  to="/dashboard"
                  class="text-sm text-muted hover:text-highlighted transition-colors"
                >{{ $t("common.dashboard") }}</NuxtLink>
              </li>
            </ul>
          </div>

          <!-- Legal & Info -->
          <div>
            <h4 class="text-sm font-semibold text-highlighted mb-4">
              {{ $t("footer.legal") }}
            </h4>
            <ul class="space-y-2.5">
              <li>
                <NuxtLink
                  to="/about"
                  class="text-sm text-muted hover:text-highlighted transition-colors"
                >{{ $t("footer.about") }}</NuxtLink>
              </li>
              <li>
                <NuxtLink
                  to="/privacy"
                  class="text-sm text-muted hover:text-highlighted transition-colors"
                >{{ $t("footer.privacy") }}</NuxtLink>
              </li>
              <li>
                <NuxtLink
                  to="/terms"
                  class="text-sm text-muted hover:text-highlighted transition-colors"
                >{{ $t("footer.terms") }}</NuxtLink>
              </li>
              <li>
                <NuxtLink
                  to="/license"
                  class="text-sm text-muted hover:text-highlighted transition-colors"
                >{{ $t("footer.license") }}</NuxtLink>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Bottom bar -->
      <div class="border-t border-default">
        <div
          class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex flex-col sm:flex-row items-center justify-between gap-3"
        >
          <p class="text-xs text-muted">
            &copy; {{ new Date().getFullYear() }} Purifyt &mdash;
            {{ $t("footer.copyright") }}
          </p>
          <div class="flex items-center gap-4">
            <span class="inline-flex items-center gap-1.5 text-xs text-muted">
              <UIcon
                name="i-lucide-shield-check"
                class="text-blue-500 text-sm"
              />
              {{ $t("footer.aiAccuracy") }}
            </span>
            <span class="inline-flex items-center gap-1.5 text-xs text-muted">
              <UIcon
                name="i-lucide-bot"
                class="text-emerald-500 text-sm"
              />
              {{ $t("footer.seleniumAuto") }}
            </span>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>
