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
const importLoading = ref(false)
const manualLoading = ref(false)
const showKaggleImport = ref(false)
const showManualCreate = ref(false)
const manualForm = reactive({
  name: '',
  description: '',
  comment: ''
})
const kaggleForm = reactive({
  datasetSlug: '',
  datasetName: '',
  mapping: {
    video_id: '',
    title: '',
    channel_name: '',
    date: '',
    author: '',
    comment: '',
    label: '',
    clean_comment: '',
    predicted_label: ''
  } as Record<string, string>
})

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
  { label: t('datasets.manual'), value: 'manual' }
])

const kaggleMappingFields = computed(() => [
  { key: 'comment', label: t('datasets.kaggleFieldComment'), placeholder: 'comment_text' },
  { key: 'author', label: t('datasets.kaggleFieldAuthor'), placeholder: 'username' },
  { key: 'label', label: t('datasets.kaggleFieldLabel'), placeholder: 'sentiment' },
  { key: 'clean_comment', label: t('datasets.kaggleFieldCleanComment'), placeholder: 'clean_text' },
  { key: 'predicted_label', label: t('datasets.kaggleFieldPredictedLabel'), placeholder: 'prediction' },
  { key: 'video_id', label: t('datasets.kaggleFieldVideoId'), placeholder: 'video_id' },
  { key: 'title', label: t('datasets.kaggleFieldTitle'), placeholder: 'video_title' },
  { key: 'channel_name', label: t('datasets.kaggleFieldChannelName'), placeholder: 'channel' },
  { key: 'date', label: t('datasets.kaggleFieldDate'), placeholder: 'created_at' }
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

async function handleKaggleImport() {
  const datasetSlug = kaggleForm.datasetSlug.trim()
  if (!datasetSlug) {
    toast.add({ title: t('datasets.kaggleSlugRequired'), color: 'warning' })
    return
  }

  const columnMapping = Object.fromEntries(
    Object.entries(kaggleForm.mapping)
      .map(([key, value]) => [key, value.trim()])
      .filter(([, value]) => value)
  )

  importLoading.value = true
  try {
    const dataset = await datasetStore.importKaggleDataset({
      dataset_slug: datasetSlug,
      dataset_name: kaggleForm.datasetName.trim() || undefined,
      column_mapping: Object.keys(columnMapping).length ? columnMapping : undefined
    })
    toast.add({ title: t('datasets.kaggleImportSuccess', { name: dataset.name }), color: 'success' })
    kaggleForm.datasetSlug = ''
    kaggleForm.datasetName = ''
    for (const key of Object.keys(kaggleForm.mapping)) kaggleForm.mapping[key] = ''
    showKaggleImport.value = false
    await loadDatasets(1)
  } catch (error: unknown) {
    const err = error as { message?: string }
    toast.add({ title: err.message || t('datasets.kaggleImportFailed'), color: 'error' })
  } finally {
    importLoading.value = false
  }
}

async function handleManualCreate() {
  const name = manualForm.name.trim()
  if (!name) {
    toast.add({ title: t('datasets.manualNameRequired'), color: 'warning' })
    return
  }

  manualLoading.value = true
  try {
    const dataset = await datasetStore.createManualDataset({
      name,
      description: manualForm.description.trim() || undefined,
      comment: manualForm.comment.trim() || undefined
    })
    toast.add({ title: t('datasets.manualCreateSuccess', { name: dataset.name }), color: 'success' })
    manualForm.name = ''
    manualForm.description = ''
    manualForm.comment = ''
    showManualCreate.value = false
    await loadDatasets(1)
  } catch (error: unknown) {
    const err = error as { message?: string }
    toast.add({ title: err.message || t('datasets.manualCreateFailed'), color: 'error' })
  } finally {
    manualLoading.value = false
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
      <div class="flex flex-col sm:flex-row gap-2">
        <UButton
          icon="i-lucide-plus"
          :label="showManualCreate ? $t('datasets.hideManualCreate') : $t('datasets.showManualCreate')"
          :variant="showManualCreate ? 'outline' : 'solid'"
          @click="showManualCreate = !showManualCreate"
        />
        <UButton
          icon="i-lucide-download-cloud"
          :label="showKaggleImport ? $t('datasets.hideKaggleImport') : $t('datasets.showKaggleImport')"
          :variant="showKaggleImport ? 'outline' : 'solid'"
          @click="showKaggleImport = !showKaggleImport"
        />
      </div>
    </div>

    <DataCard
      v-if="showManualCreate"
      class="mb-6"
    >
      <div class="p-5 space-y-5">
        <div>
          <h2 class="text-base font-semibold text-highlighted">
            {{ $t('datasets.manualCreateTitle') }}
          </h2>
          <p class="text-sm text-muted mt-1">
            {{ $t('datasets.manualCreateDesc') }}
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <UFormField :label="$t('datasets.manualDatasetName')" required>
            <UInput
              v-model="manualForm.name"
              class="w-full"
              :placeholder="$t('datasets.manualDatasetNamePlaceholder')"
            />
          </UFormField>
          <UFormField :label="$t('datasets.manualDatasetDescription')" :hint="$t('common.optional')">
            <UInput
              v-model="manualForm.description"
              class="w-full"
              :placeholder="$t('datasets.manualDatasetDescriptionPlaceholder')"
            />
          </UFormField>
        </div>

        <UFormField :label="$t('datasets.manualComment')" :hint="$t('common.optional')">
          <UTextarea
            v-model="manualForm.comment"
            class="w-full"
            :placeholder="$t('datasets.manualCommentPlaceholder')"
            :rows="4"
          />
        </UFormField>

        <div class="flex justify-end gap-2">
          <UButton
            variant="outline"
            color="neutral"
            :label="$t('common.cancel')"
            :disabled="manualLoading"
            @click="showManualCreate = false"
          />
          <UButton
            icon="i-lucide-save"
            :label="$t('datasets.manualCreateButton')"
            :loading="manualLoading"
            @click="handleManualCreate"
          />
        </div>
      </div>
    </DataCard>

    <DataCard
      v-if="showKaggleImport"
      class="mb-6"
    >
      <div class="p-5 space-y-5">
        <div>
          <h2 class="text-base font-semibold text-highlighted">
            {{ $t('datasets.kaggleImportTitle') }}
          </h2>
          <p class="text-sm text-muted mt-1">
            {{ $t('datasets.kaggleImportDesc') }}
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <UFormField :label="$t('datasets.kaggleSlug')" required>
            <UInput
              v-model="kaggleForm.datasetSlug"
              class="w-full"
              :placeholder="$t('datasets.kaggleSlugPlaceholder')"
            />
          </UFormField>
          <UFormField :label="$t('datasets.kaggleDatasetName')" :hint="$t('common.optional')">
            <UInput
              v-model="kaggleForm.datasetName"
              class="w-full"
              :placeholder="$t('datasets.kaggleDatasetNamePlaceholder')"
            />
          </UFormField>
        </div>

        <div>
          <p class="text-sm font-medium text-highlighted mb-3">
            {{ $t('datasets.kaggleManualMapping') }}
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <UFormField
              v-for="field in kaggleMappingFields"
              :key="field.key"
              :label="field.label"
            >
              <UInput
                v-model="kaggleForm.mapping[field.key]"
                class="w-full"
                :placeholder="field.placeholder"
              />
            </UFormField>
          </div>
        </div>

        <div class="flex justify-end gap-2">
          <UButton
            variant="outline"
            color="neutral"
            :label="$t('common.cancel')"
            :disabled="importLoading"
            @click="showKaggleImport = false"
          />
          <UButton
            icon="i-lucide-upload"
            :label="$t('datasets.kaggleImportButton')"
            :loading="importLoading"
            @click="handleKaggleImport"
          />
        </div>
      </div>
    </DataCard>

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
