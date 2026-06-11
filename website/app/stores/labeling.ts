import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'

interface PredictionResult {
  text: string
  clean_comment: string
  label: number
  normal: number
  judi: number
}

interface LabelingState {
  singleResult: PredictionResult | null
  batchResults: PredictionResult[]
  loading: boolean
}

export const useLabelingStore = defineStore('labeling', {
  state: (): LabelingState => ({
    singleResult: null,
    batchResults: [],
    loading: false
  }),

  actions: {
    async predictSingle(text: string) {
      const { apiFetch } = useApi()
      this.loading = true

      try {
        this.singleResult = await apiFetch<PredictionResult>('/api/v1/labeling/predict', {
          method: 'POST',
          body: { text }
        })
      } finally {
        this.loading = false
      }
    },

    async predictBatch(texts: string[]) {
      const { apiFetch } = useApi()
      this.loading = true

      try {
        this.batchResults = await apiFetch<PredictionResult[]>('/api/v1/labeling/predict/batch', {
          method: 'POST',
          body: { texts }
        })
      } finally {
        this.loading = false
      }
    },

    async autoLabelDataset(datasetId: number) {
      const { apiFetch } = useApi()
      this.loading = true

      try {
        await apiFetch(`/api/v1/labeling/dataset/${datasetId}`, {
          method: 'POST'
        })
        return true
      } finally {
        this.loading = false
      }
    },

    async labelComment(commentId: number, label: 0 | 1) {
      const { apiFetch } = useApi()
      await apiFetch(`/api/v1/labeling/comment/${commentId}`, {
        method: 'PATCH',
        body: { label: String(label) }
      })
    },

    async bulkLabelComments(datasetId: number, labels: { comment_id: number, label: 0 | 1 }[]) {
      const { apiFetch } = useApi()
      this.loading = true
      try {
        await apiFetch(`/api/v1/labeling/dataset/${datasetId}/bulk`, {
          method: 'PATCH',
          body: { labels: labels.map(l => ({ comment_id: l.comment_id, label: String(l.label) })) }
        })
      } finally {
        this.loading = false
      }
    },

    reset() {
      this.singleResult = null
      this.batchResults = []
    }
  }
})
