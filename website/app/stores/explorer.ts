import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'

export interface SseLogEntry {
  type: string
  message: string
  timestamp: Date
}

interface LabelProgress {
  labeled: number
  total: number
  percentage: number
}

interface ExplorerResult {
  video_id?: string
  title?: string
  channel_name?: string
  total_fetched: number
  total_judi: number
  total_normal: number
  total_saved: number
  judi_percentage: number
}

interface ExplorerState {
  isRunning: boolean
  logs: SseLogEntry[]
  labelProgress: LabelProgress | null
  result: ExplorerResult | null
  error: string | null
  datasetId: number | null
}

export const useExplorerStore = defineStore('explorer', {
  state: (): ExplorerState => ({
    isRunning: false,
    logs: [],
    labelProgress: null,
    result: null,
    error: null,
    datasetId: null
  }),

  actions: {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    _handleEvent(event: any) {
      const type: string = event.type ?? 'info'

      // Always push to log (skip noisy progress entries — we show them via progress bar)
      if (type !== 'label_progress') {
        this.logs.push({ type, message: event.message ?? '', timestamp: new Date() })
      }

      if (type === 'label_progress') {
        this.labelProgress = {
          labeled: event.labeled,
          total: event.total,
          percentage: event.percentage
        }
      } else if (type === 'label_done') {
        const judiCount = event.judi_count as number
        const normalCount = event.normal_count as number
        this.labelProgress = { labeled: judiCount + normalCount, total: judiCount + normalCount, percentage: 100 }
      } else if (type === 'video_saved') {
        this.datasetId = event.dataset_id ?? this.datasetId
      } else if (type === 'complete') {
        this.isRunning = false
        this.datasetId = event.dataset?.id ?? null
        this.result = (event.stats as ExplorerResult) ?? null
      }
    },

    async runVideoExplorer(videoId: string, datasetName: string) {
      const { apiStream } = useApi()
      this.isRunning = true
      this.logs = []
      this.labelProgress = null
      this.result = null
      this.error = null
      this.datasetId = null

      await apiStream(
        '/api/v1/explorer/run',
        { video_id: videoId, dataset_name: datasetName },
        event => this._handleEvent(event),
        (error: unknown) => {
          const { $i18n } = useNuxtApp()
          this.error = (error as Error)?.message || $i18n.t('explorer.explorerFailed')
          this.isRunning = false
        }
      )
      this.isRunning = false
    },

    async runChannelExplorer(channel: string, maxVideos: number, datasetName: string) {
      const { apiStream } = useApi()
      this.isRunning = true
      this.logs = []
      this.labelProgress = null
      this.result = null
      this.error = null
      this.datasetId = null

      await apiStream(
        '/api/v1/explorer/channel/run',
        { channel, max_videos: maxVideos, dataset_name: datasetName },
        event => this._handleEvent(event),
        (error: unknown) => {
          const { $i18n } = useNuxtApp()
          this.error = (error as Error)?.message || $i18n.t('explorer.channelExplorerFailed')
          this.isRunning = false
        }
      )
      this.isRunning = false
    },

    reset() {
      this.isRunning = false
      this.logs = []
      this.labelProgress = null
      this.result = null
      this.error = null
      this.datasetId = null
    }
  }
})
