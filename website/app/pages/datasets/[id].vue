<script setup lang="ts">
definePageMeta({
  title: 'Dataset Detail'
})

const route = useRoute()
const datasetStore = useDatasetStore()
const labelingStore = useLabelingStore()
const toast = useToast()
const { t } = useI18n()
const { effectiveLabel } = useCommentHelpers()

const datasetId = computed(() => Number(route.params.id))
const loading = ref(true)
const commentsLoading = ref(false)
const autoLabelLoading = ref(false)
const searchQuery = ref('')
const labelFilter = ref<'all' | 'judi' | 'normal' | 'unlabeled'>('all')
const showManualCommentForm = ref(false)
const manualCommentLoading = ref(false)
const manualCommentForm = reactive({
  comment: ''
})

const commentPage = ref(1)
const commentPerPage = ref(50)

const commentPerPageOptions = computed(() => [
  { label: t('datasets.perPage10'), value: 10 },
  { label: '25 / ' + t('common.page').toLowerCase(), value: 25 },
  { label: t('datasets.perPage50'), value: 50 },
  { label: t('datasets.perPage100'), value: 100 },
  { label: '250 / ' + t('common.page').toLowerCase(), value: 250 }
])

const selectedIds = shallowRef<Set<number>>(new Set())
const bulkLabelLoading = ref(false)
const inlineLabelLoading = ref<number | null>(null)

const selectedCount = computed(() => selectedIds.value.size)
const allOnPageSelected = computed(
  () =>
    pagedComments.value.length > 0
    && pagedComments.value.every(c => selectedIds.value.has(c.id))
)

function toggleSelectAll() {
  const next = new Set(selectedIds.value)
  if (allOnPageSelected.value) {
    pagedComments.value.forEach(c => next.delete(c.id))
  } else {
    pagedComments.value.forEach(c => next.add(c.id))
  }
  selectedIds.value = next
}

function toggleSelect(id: number) {
  const next = new Set(selectedIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  selectedIds.value = next
}

function clearSelection() {
  selectedIds.value = new Set()
}

// Single-pass stats
const stats = computed(() => {
  let judi = 0
  let normal = 0
  let unlabeled = 0
  const all = datasetStore.comments
  for (const c of all) {
    const lbl = effectiveLabel(c)
    if (lbl === 1) judi++
    else if (lbl === 0) normal++
    if (c.label === null || c.label === undefined) unlabeled++
  }
  return {
    total: datasetStore.commentTotal || all.length,
    judi,
    normal,
    unlabeled
  }
})

// Client-side text search + label filter
const filteredComments = computed(() => {
  let list = datasetStore.comments
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(
      c => c.comment.toLowerCase().includes(q) || (c.author ?? '').toLowerCase().includes(q)
    )
  }
  if (labelFilter.value === 'judi') return list.filter(c => effectiveLabel(c) === 1)
  if (labelFilter.value === 'normal') return list.filter(c => effectiveLabel(c) === 0)
  if (labelFilter.value === 'unlabeled')
    return list.filter(c => c.label === null || c.label === undefined)
  return list
})

const totalCommentPages = computed(() =>
  Math.max(1, Math.ceil(filteredComments.value.length / commentPerPage.value))
)

const pagedComments = computed(() => {
  const start = (commentPage.value - 1) * commentPerPage.value
  return filteredComments.value.slice(start, start + commentPerPage.value)
})

// Actions
async function handleInlineLabel(commentId: number, label: 0 | 1) {
  inlineLabelLoading.value = commentId
  try {
    await labelingStore.labelComment(commentId, label)
    const c = datasetStore.comments.find(c => c.id === commentId)
    if (c) c.label = label
    toast.add({ title: t('datasetDetail.labelUpdated'), color: 'success' })
  } catch {
    toast.add({ title: t('datasetDetail.labelFailed'), color: 'error' })
  } finally {
    inlineLabelLoading.value = null
  }
}

async function handleBulkLabel(label: 0 | 1) {
  if (selectedIds.value.size === 0) return
  bulkLabelLoading.value = true
  try {
    const labels = Array.from(selectedIds.value).map(comment_id => ({
      comment_id,
      label
    }))
    await labelingStore.bulkLabelComments(datasetId.value, labels)
    for (const id of selectedIds.value) {
      const c = datasetStore.comments.find(c => c.id === id)
      if (c) c.label = label
    }
    toast.add({
      title:
        label === 1
          ? t('datasetDetail.bulkLabeledJudi', { n: labels.length })
          : t('datasetDetail.bulkLabeledNormal', { n: labels.length }),
      color: 'success'
    })
    clearSelection()
  } catch {
    toast.add({ title: t('datasetDetail.bulkFailed'), color: 'error' })
  } finally {
    bulkLabelLoading.value = false
  }
}

async function loadData() {
  loading.value = true
  try {
    await datasetStore.fetchDatasetDetail(datasetId.value)
    await loadComments()
  } catch {
    toast.add({ title: t('datasetDetail.loadFailed'), color: 'error' })
  } finally {
    loading.value = false
  }
}

async function loadComments() {
  commentsLoading.value = true
  clearSelection()
  try {
    await datasetStore.fetchComments(datasetId.value)
  } catch {
    toast.add({ title: t('datasetDetail.commentsFailed'), color: 'error' })
  } finally {
    commentsLoading.value = false
  }
}

async function handleAutoLabel() {
  autoLabelLoading.value = true
  try {
    await labelingStore.autoLabelDataset(datasetId.value)
    toast.add({ title: t('datasetDetail.predictingComplete'), color: 'success' })
    await loadComments()
  } catch {
    toast.add({ title: t('datasetDetail.predictingFailed'), color: 'error' })
  } finally {
    autoLabelLoading.value = false
  }
}

async function handleManualCommentCreate() {
  const comment = manualCommentForm.comment.trim()
  if (!comment) {
    toast.add({ title: t('datasetDetail.manualCommentRequired'), color: 'warning' })
    return
  }

  manualCommentLoading.value = true
  try {
    await datasetStore.createManualComment(datasetId.value, {
      comment
    })
    toast.add({ title: t('datasetDetail.manualCommentCreated'), color: 'success' })
    manualCommentForm.comment = ''
    showManualCommentForm.value = false
  } catch (error: unknown) {
    const err = error as { message?: string }
    toast.add({ title: err.message || t('datasetDetail.manualCommentFailed'), color: 'error' })
  } finally {
    manualCommentLoading.value = false
  }
}

function csvEscape(value: unknown) {
  const text = value === null || value === undefined ? '' : String(value)
  return `"${text.replace(/"/g, '""')}"`
}

function handleExportCsv() {
  const rows = filteredComments.value
  if (rows.length === 0) {
    toast.add({ title: t('datasetDetail.exportEmpty'), color: 'warning' })
    return
  }

  const columns = [
    'id',
    'dataset_id',
    'video_id',
    'title',
    'channel_name',
    'date',
    'author',
    'comment',
    'clean_comment',
    'label',
    'predicted_label',
    'source',
    'source_detail',
    'created_at'
  ] as const
  const csv = [
    columns.join(','),
    ...rows.map(row => columns.map(column => csvEscape(row[column])).join(','))
  ].join('\r\n')
  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  const datasetName = datasetStore.currentDataset?.name || `dataset-${datasetId.value}`
  const safeName = datasetName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || `dataset-${datasetId.value}`

  link.href = url
  link.download = `${safeName}-comments.csv`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
  toast.add({ title: t('datasetDetail.exportSuccess'), color: 'success' })
}

function goToCommentPage(page: number) {
  if (page < 1 || page > totalCommentPages.value) return
  commentPage.value = page
  clearSelection()
}

watch([searchQuery, labelFilter, commentPerPage], () => {
  commentPage.value = 1
  clearSelection()
})

onMounted(() => loadData())
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-6">
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 mb-1">
          <UButton
            to="/datasets"
            variant="ghost"
            color="neutral"
            icon="i-lucide-arrow-left"
            size="xs"
          />
          <h1 class="text-2xl font-semibold text-highlighted">
            {{ datasetStore.currentDataset?.name || $t('datasetDetail.loadingTitle') }}
          </h1>
        </div>
        <p class="text-sm text-muted">
          {{ datasetStore.currentDataset?.source }} · Created
          {{
            datasetStore.currentDataset
              ? new Date(datasetStore.currentDataset.created_at).toLocaleDateString()
              : ''
          }}
        </p>
      </div>

      <div class="flex flex-col sm:flex-row gap-2 lg:justify-end">
        <UButton
          class="justify-center"
          :label="$t('datasetDetail.predictBtn')"
          icon="i-lucide-sparkles"
          :loading="autoLabelLoading"
          @click="handleAutoLabel"
        />
        <UButton
          class="justify-center"
          :label="$t('datasetDetail.exportCsv')"
          icon="i-lucide-download"
          variant="outline"
          :disabled="filteredComments.length === 0"
          @click="handleExportCsv"
        />
        <UButton
          class="justify-center"
          :label="$t('datasetDetail.showManualComment')"
          icon="i-lucide-message-square-plus"
          @click="showManualCommentForm = true"
        />
      </div>
    </div>

    <UModal v-model:open="showManualCommentForm">
      <template #content>
        <div class="p-5 space-y-4 max-w-2xl w-full">
        <div>
          <h2 class="text-base font-semibold text-highlighted">
            {{ $t('datasetDetail.manualCommentTitle') }}
          </h2>
          <p class="text-sm text-muted mt-1">
            {{ $t('datasetDetail.manualCommentDesc') }}
          </p>
        </div>
        <UFormField :label="$t('datasetDetail.manualCommentField')" required>
          <UTextarea
            v-model="manualCommentForm.comment"
            class="w-full"
            :placeholder="$t('datasetDetail.manualCommentPlaceholder')"
            :rows="4"
          />
        </UFormField>
        <div class="flex justify-end gap-2">
          <UButton
            variant="outline"
            color="neutral"
            :label="$t('common.cancel')"
            :disabled="manualCommentLoading"
            @click="showManualCommentForm = false"
          />
          <UButton
            icon="i-lucide-save"
            :label="$t('datasetDetail.manualCommentSave')"
            :loading="manualCommentLoading"
            @click="handleManualCommentCreate"
          />
        </div>
      </div>
      </template>
    </UModal>

    <!-- Stats -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
      <StatCard
        :title="$t('common.total')"
        :value="stats.total"
        icon="i-lucide-message-square"
        color="blue"
      />
      <StatCard
        :title="$t('common.judi')"
        :value="stats.judi"
        icon="i-lucide-alert-triangle"
        color="red"
      />
      <StatCard
        :title="$t('common.normal')"
        :value="stats.normal"
        icon="i-lucide-check-circle"
        color="green"
      />
      <StatCard
        :title="$t('common.predict')"
        :value="stats.unlabeled"
        icon="i-lucide-help-circle"
        color="yellow"
      />
    </div>

    <!-- Search & Filter -->
    <DatasetCommentFilterBar
      :search-query="searchQuery"
      :label-filter="labelFilter"
      :comment-per-page="commentPerPage"
      :comment-per-page-options="commentPerPageOptions"
      @update:search-query="searchQuery = $event"
      @update:label-filter="labelFilter = $event"
      @update:comment-per-page="commentPerPage = $event"
    />

    <!-- Comments -->
    <DataCard
      :loading="loading"
      :empty="filteredComments.length === 0 && !commentsLoading"
      :empty-title="$t('datasetDetail.noComments')"
      :empty-description="$t('datasetDetail.noCommentsDesc')"
      empty-icon="i-lucide-message-square"
    >
      <!-- Summary bar -->
      <div class="px-4 py-3 border-b border-default flex flex-wrap items-center justify-between gap-3">
        <span class="text-sm text-muted flex items-center gap-2">
          <UIcon
            v-if="commentsLoading"
            name="i-lucide-loader-circle"
            class="animate-spin"
          />
          <template v-if="labelFilter !== 'all'">{{ filteredComments.length }} {{ $t('common.filtered') }} ·</template>
          {{ datasetStore.commentTotal }} {{ $t('datasetDetail.totalComments') }}
          <template v-if="totalCommentPages > 1">· Page {{ commentPage }}/{{ totalCommentPages }}</template>
        </span>
      </div>

      <!-- Bulk action toolbar -->
      <DatasetBulkActionToolbar
        :selected-count="selectedCount"
        :bulk-label-loading="bulkLabelLoading"
        @bulk-label="handleBulkLabel"
        @clear-selection="clearSelection"
      />

      <!-- Comment table -->
      <DatasetCommentTable
        :comments="pagedComments"
        :selected-ids="selectedIds"
        :all-on-page-selected="allOnPageSelected"
        :selected-count="selectedCount"
        :inline-label-loading="inlineLabelLoading"
        :comment-page="commentPage"
        :comment-per-page="commentPerPage"
        @toggle-select-all="toggleSelectAll"
        @toggle-select="toggleSelect"
        @inline-label="handleInlineLabel"
      />

      <!-- Pagination footer -->
      <PaginationFooter
        v-if="!loading && filteredComments.length > 0"
        :current-page="commentPage"
        :total-pages="totalCommentPages"
        :total="filteredComments.length"
        :per-page="commentPerPage"
        :label="$t('common.comments')"
        @update:current-page="goToCommentPage"
      />
    </DataCard>
  </div>
</template>
