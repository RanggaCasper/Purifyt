<script setup lang="ts">
definePageMeta({
  title: 'Dashboard'
})

const datasetStore = useDatasetStore()
const { user: authUser } = useAuth()
const { t } = useI18n()
const loading = ref(true)

const totalComments = computed(() =>
  datasetStore.allDatasets.reduce((sum, d) => sum + (d.comment_count || 0), 0)
)

const recentDatasets = computed(() => datasetStore.allDatasets.slice(0, 5))

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return t('dashboard.goodMorning')
  if (h < 18) return t('dashboard.goodAfternoon')
  return t('dashboard.goodEvening')
})

const quickActions = computed(() => [
  {
    to: '/explorer',
    icon: 'i-lucide-search',
    title: t('dashboard.videoExplorer'),
    description: t('dashboard.videoExplorerDesc'),
    iconBg: 'bg-blue-100 dark:bg-blue-950',
    iconColor: 'text-blue-600 dark:text-blue-400',
    hoverBorder: 'hover:border-blue-300',
    hoverText: 'group-hover:text-blue-600'
  },
  {
    to: '/auto-delete',
    icon: 'i-lucide-shield-off',
    title: t('dashboard.autoDelete'),
    description: t('dashboard.autoDeleteDesc'),
    iconBg: 'bg-red-100 dark:bg-red-950',
    iconColor: 'text-red-600 dark:text-red-400',
    hoverBorder: 'hover:border-red-300',
    hoverText: 'group-hover:text-red-600'
  },
  {
    to: '/predict',
    icon: 'i-lucide-sparkles',
    title: t('dashboard.quickPredict'),
    description: t('dashboard.quickPredictDesc'),
    iconBg: 'bg-yellow-100 dark:bg-yellow-950',
    iconColor: 'text-yellow-600 dark:text-yellow-400',
    hoverBorder: 'hover:border-yellow-300',
    hoverText: 'group-hover:text-yellow-600'
  },
  {
    to: '/datasets',
    icon: 'i-lucide-database',
    title: t('dashboard.manageDatasets'),
    description: t('dashboard.manageDatasetsDesc'),
    iconBg: 'bg-green-100 dark:bg-green-950',
    iconColor: 'text-green-600 dark:text-green-400',
    hoverBorder: 'hover:border-green-300',
    hoverText: 'group-hover:text-green-600'
  }
])

onMounted(async () => {
  try {
    await datasetStore.fetchAllDatasets()
  } catch {
    // API may not be available
  } finally {
    loading.value = false
  }
})

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('id-ID', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}
</script>

<template>
  <div>
    <!-- Greeting -->
    <div class="mb-6">
      <h1 class="text-2xl font-semibold text-highlighted">
        {{ greeting }}, {{ authUser?.username || $t('dashboard.there') }} 👋
      </h1>
      <p class="text-sm text-muted mt-1">
        {{ $t('dashboard.overview') }}
      </p>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
      <StatCard
        :title="$t('dashboard.totalDatasets')"
        :value="datasetStore.allDatasets.length"
        icon="i-lucide-database"
        color="blue"
      />
      <StatCard
        :title="$t('dashboard.totalComments')"
        :value="totalComments"
        icon="i-lucide-message-square"
        color="neutral"
      />
    </div>

    <!-- Quick Actions -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <QuickActionCard
        v-for="action in quickActions"
        :key="action.to"
        v-bind="action"
      />
    </div>

    <!-- Recent Datasets -->
    <DataCard
      :loading="loading"
      :empty="recentDatasets.length === 0 && !loading"
      :empty-title="$t('dashboard.noDatasets')"
      :empty-description="$t('dashboard.startExploring')"
      empty-icon="i-lucide-database"
    >
      <div class="px-5 py-3 border-b border-default flex items-center justify-between">
        <h3 class="font-medium text-sm text-highlighted">
          {{ $t('dashboard.recentDatasets') }}
        </h3>
        <UButton
          to="/datasets"
          variant="link"
          size="xs"
          :label="$t('common.viewAll')"
          trailing-icon="i-lucide-arrow-right"
        />
      </div>
      <div class="divide-y divide-default">
        <NuxtLink
          v-for="dataset in recentDatasets"
          :key="dataset.id"
          :to="`/datasets/${dataset.id}`"
          class="px-5 py-3 flex items-center justify-between hover:bg-elevated/50 transition-colors group"
        >
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-highlighted truncate">{{ dataset.name }}</p>
            <p class="text-xs text-muted mt-0.5 flex items-center gap-2">
              <span class="capitalize">{{ dataset.source.replace('_', ' ') }}</span>
              <span>·</span>
              <span>{{ dataset.comment_count || 0 }} {{ $t('common.comments') }}</span>
              <span>·</span>
              <span>{{ formatDate(dataset.created_at) }}</span>
            </p>
          </div>
          <UIcon
            name="i-lucide-chevron-right"
            class="text-muted shrink-0 ml-3 group-hover:text-default"
          />
        </NuxtLink>
      </div>
    </DataCard>
  </div>
</template>
