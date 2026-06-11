import { defineStore } from 'pinia'
import { useApi, type PaginatedResponse } from '~/composables/useApi'

export interface Dataset {
  id: number
  name: string
  description: string | null
  source: string
  source_url: string | null
  owner_id: number
  created_at: string
  comment_count: number
}

export interface Comment {
  id: number
  dataset_id: number
  comment: string
  clean_comment: string | null
  author: string
  label: number | null
  predicted_label: string | null
  video_id: string | null
  title: string | null
  channel_name: string | null
  date: string | null
  source: string
  source_detail: string | null
  created_at: string
}

interface DatasetState {
  datasets: Dataset[]
  allDatasets: Dataset[]
  currentDataset: Dataset | null
  comments: Comment[]
  loading: boolean
  // Dataset list pagination
  datasetTotal: number
  datasetPage: number
  datasetPerPage: number
  datasetTotalPages: number
  // Comment total (all loaded at once)
  commentTotal: number
}

export const useDatasetStore = defineStore('dataset', {
  state: (): DatasetState => ({
    datasets: [],
    allDatasets: [],
    currentDataset: null,
    comments: [],
    loading: false,
    datasetTotal: 0,
    datasetPage: 1,
    datasetPerPage: 20,
    datasetTotalPages: 1,
    commentTotal: 0
  }),

  actions: {
    async fetchAllDatasets() {
      const { apiFetch } = useApi()
      const result = await apiFetch<PaginatedResponse<Dataset>>('/api/v1/datasets/?page=1&per_page=9999')
      this.allDatasets = result.items
    },

    async fetchDatasets(page = 1, perPage = 20, source?: string) {
      const { apiFetch } = useApi()
      this.loading = true

      try {
        const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
        if (source) params.append('source', source)

        const result = await apiFetch<PaginatedResponse<Dataset>>(`/api/v1/datasets/?${params}`)
        this.datasets = result.items
        this.datasetTotal = result.total
        this.datasetPage = result.page
        this.datasetPerPage = result.per_page
        this.datasetTotalPages = result.total_pages
      } finally {
        this.loading = false
      }
    },

    async fetchDatasetDetail(id: number) {
      const { apiFetch } = useApi()
      this.loading = true

      try {
        this.currentDataset = await apiFetch<Dataset>(`/api/v1/datasets/${id}`)
      } finally {
        this.loading = false
      }
    },

    async fetchComments(datasetId: number) {
      const { apiFetch } = useApi()

      // Fetch all comments at once for client-side pagination/search/filter
      const params = new URLSearchParams({ page: '1', per_page: '99999' })
      const result = await apiFetch<PaginatedResponse<Comment>>(
        `/api/v1/datasets/${datasetId}/comments?${params}`
      )
      this.comments = result.items.map(c => ({
        ...c,
        label: c.label !== null && c.label !== undefined ? Number(c.label) : null
      }))
      this.commentTotal = result.total
    },

    async deleteDataset(id: number) {
      const { apiFetch } = useApi()

      await apiFetch(`/api/v1/datasets/${id}`, { method: 'DELETE' })
      this.datasets = this.datasets.filter(d => d.id !== id)
      return true
    }
  }
})
