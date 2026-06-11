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
      c => c.comment.toLowerCase().includes(q) || c.author.toLowerCase().includes(q)
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
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
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

      <UButton
        :label="$t('datasetDetail.predictBtn')"
        icon="i-lucide-sparkles"
        :loading="autoLabelLoading"
        @click="handleAutoLabel"
      />
    </div>

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
