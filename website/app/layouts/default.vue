<script setup lang="ts">
import { useColorMode } from '#imports'

const { isAuthenticated, user: authUser, logout } = useAuth()
const route = useRoute()
const colorMode = useColorMode()
const { t, locale, setLocale } = useI18n()

const toggleLocale = () => {
  setLocale(locale.value === 'id' ? 'en' : 'id')
}

const sidebarOpen = ref(true)
const mobileSidebarOpen = ref(false)

const navigation = computed(() => [
  { label: t('nav.dashboard'), icon: 'i-lucide-home', to: '/dashboard' },
  { label: t('nav.explorer'), icon: 'i-lucide-search', to: '/explorer' },
  { label: t('nav.autoDelete'), icon: 'i-lucide-shield-off', to: '/auto-delete' },
  { label: t('nav.datasets'), icon: 'i-lucide-database', to: '/datasets' },
  { label: t('nav.predict'), icon: 'i-lucide-sparkles', to: '/predict' },
  { label: t('nav.settings'), icon: 'i-lucide-settings', to: '/settings' }
])

const isActive = (to: string) => {
  if (to === '/dashboard') return route.path === '/dashboard'
  return route.path.startsWith(to)
}

const toggleDarkMode = () => {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}
</script>

<template>
  <div class="min-h-screen bg-default">
    <!-- Mobile sidebar overlay -->
    <div
      v-if="mobileSidebarOpen"
      class="fixed inset-0 bg-black/50 z-40 lg:hidden"
      @click="mobileSidebarOpen = false"
    />

    <!-- Sidebar -->
    <aside
      :class="[
        'fixed inset-y-0 left-0 z-50 flex flex-col bg-default border-r border-default transition-all duration-300',
        sidebarOpen ? 'w-60' : 'w-60 lg:w-16',
        mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      ]"
    >
      <!-- Collapse toggle + Logo -->
      <div
        :class="[
          'flex items-center h-14 px-3 border-b border-default transition-all duration-300',
          sidebarOpen || mobileSidebarOpen ? 'justify-between' : 'justify-center'
        ]"
      >
        <NuxtLink
          v-if="sidebarOpen || mobileSidebarOpen"
          to="/"
          class="flex items-center gap-2 overflow-hidden min-w-0"
        >
          <img
            src="/logo.png"
            alt="Purifyt"
            class="h-8 w-auto shrink-0"
          >
          <span class="font-semibold text-highlighted whitespace-nowrap truncate">
            Purifyt
          </span>
        </NuxtLink>
        <button
          class="hidden lg:flex items-center justify-center w-8 h-8 rounded-md text-muted hover:bg-elevated hover:text-highlighted transition-colors shrink-0"
          :title="sidebarOpen ? $t('nav.collapseSidebar') : $t('nav.expandSidebar')"
          @click="sidebarOpen = !sidebarOpen"
        >
          <UIcon
            :name="sidebarOpen ? 'i-lucide-panel-left-close' : 'i-lucide-panel-left-open'"
            class="text-base"
          />
        </button>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-2.5 py-3 space-y-0.5 overflow-y-auto">
        <NuxtLink
          v-for="item in navigation"
          :key="item.to"
          :to="item.to"
          :title="!sidebarOpen && !mobileSidebarOpen ? item.label : undefined"
          :class="[
            'flex items-center gap-3 rounded-lg text-sm font-medium transition-colors',
            sidebarOpen || mobileSidebarOpen ? 'px-2.5 py-2' : 'justify-center p-2',
            isActive(item.to)
              ? 'bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400'
              : 'text-muted hover:bg-elevated hover:text-highlighted'
          ]"
          @click="mobileSidebarOpen = false"
        >
          <UIcon
            :name="item.icon"
            class="text-lg shrink-0"
          />
          <span
            v-show="sidebarOpen || mobileSidebarOpen"
            class="whitespace-nowrap"
          >{{
            item.label
          }}</span>
        </NuxtLink>
      </nav>
    </aside>

    <!-- Main content area -->
    <div
      :class="[
        'flex flex-col min-h-screen transition-all duration-300',
        sidebarOpen ? 'lg:ml-60' : 'lg:ml-16'
      ]"
    >
      <!-- Top navbar -->
      <header
        :class="[
          'sticky top-0 z-30 h-14 bg-default/80 backdrop-blur-md border-b border-default flex items-center justify-between px-4 lg:px-6 transition-all duration-300'
        ]"
      >
        <div class="flex items-center gap-3">
          <!-- Mobile hamburger -->
          <button
            class="lg:hidden w-10 h-10 flex items-center justify-center rounded-xl bg-elevated hover:bg-slate-200 dark:hover:bg-slate-700 text-highlighted transition-all duration-200"
            @click="mobileSidebarOpen = !mobileSidebarOpen"
          >
            <UIcon
              name="lucide:menu"
              class="w-5 h-5"
            />
          </button>

          <!-- Breadcrumb -->
          <UBreadcrumb
            :items="[
              { label: 'Purifyt', to: '/dashboard' },
              { label: (route.meta.title as string) || 'Dashboard' }
            ]"
          />
        </div>

        <div class="flex items-center gap-2">
          <button
            class="w-9 h-9 flex items-center justify-center rounded-lg text-muted hover:bg-elevated hover:text-highlighted transition-colors text-xs font-semibold"
            :title="locale === 'id' ? 'Switch to English' : 'Ganti ke Bahasa Indonesia'"
            @click="toggleLocale"
          >
            {{ locale === "id" ? "EN" : "ID" }}
          </button>
          <button
            class="w-9 h-9 flex items-center justify-center rounded-lg text-muted hover:bg-elevated hover:text-highlighted transition-colors"
            :title="colorMode.value === 'dark' ? $t('nav.lightMode') : $t('nav.darkMode')"
            @click="toggleDarkMode"
          >
            <UIcon
              :name="colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon'"
              class="text-lg"
            />
          </button>
          <UDropdownMenu
            v-if="isAuthenticated"
            :items="[
              [{ label: authUser?.username || $t('nav.user'), type: 'label' as const }],
              [
                { label: $t('common.settings'), icon: 'i-lucide-settings', onSelect: () => navigateTo('/settings') },
                { label: $t('common.logout'), icon: 'i-lucide-log-out', onSelect: () => logout() }
              ]
            ]"
          >
            <UButton
              color="neutral"
              variant="ghost"
              icon="i-lucide-user"
              size="sm"
            />
          </UDropdownMenu>
          <UButton
            v-else
            to="/login"
            :label="$t('common.login')"
            size="sm"
          />
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 p-4 lg:p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
