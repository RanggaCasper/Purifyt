<script setup lang="ts">
definePageMeta({
  title: 'Datasets'
})

const datasetStore = useDatasetStore()
const toast = useToast()
const { t } = useI18n()

const loading = ref(true)
const sourceFilter = ref('')
const deleteLoading = ref<number | null>(null)
const currentPage = ref(1)
const perPage = ref(20)

const perPageOptions = computed(() => [
  { label: t('datasets.perPage10'), value: 10 },
  { label: t('datasets.perPage20'), value: 20 },
  { label: t('datasets.perPage50'), value: 50 },
  { label: t('datasets.perPage100'), value: 100 }
])

const sources = computed(() => [
  { label: t('datasets.allSources'), value: '' },
  { label: t('datasets.youtubeApi'), value: 'youtube_api' },
  { label: t('datasets.kaggle'), value: 'kaggle' },
  { label: 'Manual', value: 'manual' }
])

async function loadDatasets(page = currentPage.value) {
  loading.value = true
  try {
    await datasetStore.fetchDatasets(page, perPage.value, sourceFilter.value || undefined)
    currentPage.value = datasetStore.datasetPage
  } catch {
    toast.add({ title: t('datasets.loadFailed'), color: 'error' })
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: number) {
  deleteLoading.value = id
  try {
    await datasetStore.deleteDataset(id)
    toast.add({ title: t('datasets.datasetDeleted'), color: 'success' })
    await loadDatasets(1)
  } catch {
    toast.add({ title: t('datasets.deleteFailed'), color: 'error' })
  } finally {
    deleteLoading.value = null
  }
}

function goToPage(page: number) {
  if (page < 1 || page > datasetStore.datasetTotalPages) return
  loadDatasets(page)
}

watch(sourceFilter, () => {
  currentPage.value = 1
  loadDatasets(1)
})

watch(perPage, () => {
  currentPage.value = 1
  loadDatasets(1)
})

onMounted(() => loadDatasets())

const sourceLabel = (source: string) => {
  const s = sources.value.find(s => s.value === source)
  return s ? s.label : source
}

const sourceColor = (source: string) => {
  const map: Record<string, string> = {
    youtube_api: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400',
    kaggle: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400',
    manual: 'bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-400'
  }
  return map[source] ?? 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400'
}
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <PageHeader
        :title="$t('datasets.title')"
        :description="$t('datasets.desc')"
      />
    </div>

    <!-- Filters + per-page -->
    <DatasetFilterBar
      :source-filter="sourceFilter"
      :sources="sources"
      :per-page="perPage"
      :per-page-options="perPageOptions"
      @update:source-filter="sourceFilter = $event"
      @update:per-page="perPage = $event"
    />

    <!-- Dataset table -->
    <DataCard
      :loading="loading"
      :empty="datasetStore.datasets.length === 0"
      :empty-title="$t('datasets.noDatasets')"
      :empty-description="$t('datasets.startExploring')"
      empty-icon="i-lucide-database"
    >
      <DatasetTable
        :datasets="datasetStore.datasets"
        :page="datasetStore.datasetPage"
        :per-page="perPage"
        :delete-loading="deleteLoading"
        :source-label="sourceLabel"
        :source-color="sourceColor"
        @delete="handleDelete"
      />

      <!-- Pagination footer -->
      <PaginationFooter
        v-if="!loading && datasetStore.datasetTotal > 0"
        :current-page="datasetStore.datasetPage"
        :total-pages="datasetStore.datasetTotalPages"
        :total="datasetStore.datasetTotal"
        :per-page="perPage"
        :label="$t('datasets.title').toLowerCase()"
        @update:current-page="goToPage"
      />
    </DataCard>
  </div>
</template>
