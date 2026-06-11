import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'
import type {
  CookieAccount,
  CookieAccountDetail,
  LoginPayload,
  ScanPayload,
  DeletePayload,
  FetchCommentsPayload,
  ScannedComment,
  ScanResult
} from '~/types/autoDelete'

export interface AutoDeleteLogEntry {
  type: string
  step?: string
  message: string
  timestamp: Date
}

interface AutoDeleteState {
  // Accounts / cookies
  accounts: CookieAccount[]
  accountsLoading: boolean

  // Login
  loginRunning: boolean
  loginLogs: AutoDeleteLogEntry[]
  loginResult: { email: string, channelName: string } | null
  loginError: string | null

  // Scan
  scanRunning: boolean
  scanLogs: AutoDeleteLogEntry[]
  scanProgress: { current: number, total: number } | null
  scannedComments: ScannedComment[]
  judiComments: ScannedComment[]
  scanResult: ScanResult | null
  scanError: string | null

  // Delete
  deleteRunning: boolean
  deleteLogs: AutoDeleteLogEntry[]
  deleteError: string | null

  // Fetch comments
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fetchedComments: Array<Record<string, any>>
  fetchRunning: boolean
  fetchError: string | null
}

export const useAutoDeleteStore = defineStore('autoDelete', {
  state: (): AutoDeleteState => ({
    accounts: [],
    accountsLoading: false,

    loginRunning: false,
    loginLogs: [],
    loginResult: null,
    loginError: null,

    scanRunning: false,
    scanLogs: [],
    scanProgress: null,
    scannedComments: [],
    judiComments: [],
    scanResult: null,
    scanError: null,

    deleteRunning: false,
    deleteLogs: [],
    deleteError: null,

    fetchedComments: [],
    fetchRunning: false,
    fetchError: null
  }),

  getters: {
    activeAccounts: state => state.accounts.filter(a => a.is_active),
    accountEmails: state => state.accounts.map(a => a.email)
  },

  actions: {
    // Cookie / Account Management

    async fetchAccounts() {
      const { apiFetch } = useApi()
      this.accountsLoading = true
      try {
        const result = await apiFetch<{ accounts: CookieAccount[], total: number }>(
          '/api/v1/auto-delete/cookies'
        )
        this.accounts = result.accounts
      } catch (error: unknown) {
        this.accounts = []
        throw error
      } finally {
        this.accountsLoading = false
      }
    },

    async fetchAccountDetail(email: string): Promise<CookieAccountDetail> {
      const { apiFetch } = useApi()
      return await apiFetch<CookieAccountDetail>(`/api/v1/auto-delete/cookies/${encodeURIComponent(email)}`)
    },

    async deleteAccount(email: string) {
      const { apiFetch } = useApi()
      await apiFetch(`/api/v1/auto-delete/cookies/${encodeURIComponent(email)}`, {
        method: 'DELETE'
      })
      this.accounts = this.accounts.filter(a => a.email !== email)
    },

    // Login (SSE)

    async login(payload: LoginPayload) {
      const { apiStream } = useApi()
      this.loginRunning = true
      this.loginLogs = []
      this.loginResult = null
      this.loginError = null

      await apiStream(
        '/api/v1/auto-delete/login',
        payload,
        (event) => {
          const type: string = event.type ?? 'status'

          if (type === 'status') {
            this.loginLogs.push({
              type,
              step: event.step,
              message: event.message ?? '',
              timestamp: new Date()
            })
          } else if (type === 'done') {
            const { $i18n } = useNuxtApp()
            this.loginLogs.push({
              type,
              message: event.message ?? $i18n.t('autoDelete.loginSuccess'),
              timestamp: new Date()
            })
            this.loginResult = {
              email: event.email,
              channelName: event.channel_name
            }
          } else if (type === 'error') {
            const { $i18n } = useNuxtApp()
            this.loginError = event.message ?? $i18n.t('autoDelete.loginFailed')
            this.loginLogs.push({
              type,
              message: event.message ?? $i18n.t('autoDelete.loginFailed'),
              timestamp: new Date()
            })
          }
        },
        (error) => {
          const { $i18n } = useNuxtApp()
          this.loginError = (error instanceof Error ? error.message : null) || $i18n.t('autoDelete.loginFailed')
          this.loginRunning = false
        }
      )
      this.loginRunning = false
    },

    // Scan (SSE)

    async scan(payload: ScanPayload, preview = false) {
      const { apiStream } = useApi()
      const url = preview
        ? '/api/v1/auto-delete/scan/preview'
        : '/api/v1/auto-delete/scan'

      this.scanRunning = true
      this.scanLogs = []
      this.scanProgress = null
      this.scannedComments = []
      this.judiComments = []
      this.scanResult = null
      this.scanError = null

      await apiStream(
        url,
        payload,
        (event) => {
          const type: string = event.type ?? 'status'

          if (type === 'status') {
            this.scanLogs.push({
              type,
              step: event.step,
              message: event.message ?? '',
              timestamp: new Date()
            })
            if (event.total_comments) {
              this.scanProgress = { current: 0, total: event.total_comments }
            }
          } else if (type === 'comment') {
            const comment: ScannedComment = {
              comment_id: event.comment_id,
              text: event.text,
              author: event.author,
              label: event.label,
              confidence: event.confidence
            }
            this.scannedComments.push(comment)
            this.scanProgress = { current: event.index, total: event.total }
          } else if (type === 'judi_detected') {
            const comment: ScannedComment = {
              comment_id: event.comment_id,
              text: event.text,
              author: event.author,
              label: 1,
              confidence: event.confidence
            }
            this.scannedComments.push(comment)
            this.judiComments.push(comment)
            this.scanProgress = { current: event.index, total: event.total }
          } else if (type === 'delete') {
            const { $i18n } = useNuxtApp()
            this.scanLogs.push({
              type,
              message: event.message ?? $i18n.t('autoDelete.commentsDeletedLog', { deleted: event.deleted, requested: event.requested }),
              timestamp: new Date()
            })
          } else if (type === 'done') {
            const { $i18n } = useNuxtApp()
            this.scanResult = {
              scanned: event.scanned ?? this.scannedComments.length,
              detected: event.detected ?? this.judiComments.length,
              deleted: event.deleted ?? 0,
              errors: event.errors ?? 0,
              judiComments: this.judiComments
            }
            this.scanLogs.push({
              type,
              message: $i18n.t('autoDelete.scanDoneSummary', { scanned: event.scanned ?? 0, detected: event.detected ?? 0, deleted: event.deleted ?? 0 }),
              timestamp: new Date()
            })
          } else if (type === 'error') {
            const { $i18n } = useNuxtApp()
            this.scanError = event.message ?? $i18n.t('autoDelete.scanFailed')
            this.scanLogs.push({
              type,
              message: event.message ?? $i18n.t('autoDelete.scanFailed'),
              timestamp: new Date()
            })
          }
        },
        (error) => {
          const { $i18n } = useNuxtApp()
          this.scanError = (error instanceof Error ? error.message : null) || $i18n.t('autoDelete.scanFailed')
          this.scanRunning = false
        }
      )
      this.scanRunning = false
    },

    // Delete Specific Comments (SSE)

    async deleteComments(payload: DeletePayload) {
      const { apiStream } = useApi()
      this.deleteRunning = true
      this.deleteLogs = []
      this.deleteError = null

      await apiStream(
        '/api/v1/auto-delete/delete',
        payload,
        (event) => {
          const type: string = event.type ?? 'status'

          this.deleteLogs.push({
            type,
            message: event.message ?? '',
            timestamp: new Date()
          })

          if (type === 'error') {
            const { $i18n } = useNuxtApp()
            this.deleteError = event.message ?? $i18n.t('autoDelete.deleteFailed')
          }
        },
        (error) => {
          const { $i18n } = useNuxtApp()
          this.deleteError = (error instanceof Error ? error.message : null) || $i18n.t('autoDelete.deleteFailed')
          this.deleteRunning = false
        }
      )
      this.deleteRunning = false
    },

    // Fetch All Comments (SSE)

    async fetchComments(payload: FetchCommentsPayload) {
      const { apiStream } = useApi()
      this.fetchRunning = true
      this.fetchedComments = []
      this.fetchError = null

      await apiStream(
        '/api/v1/auto-delete/comments',
        payload,
        (event) => {
          const type: string = event.type ?? 'status'

          if (type === 'done') {
            this.fetchedComments = event.comments ?? []
          } else if (type === 'error') {
            const { $i18n } = useNuxtApp()
            this.fetchError = event.message ?? $i18n.t('autoDelete.fetchFailed')
          }
        },
        (error) => {
          const { $i18n } = useNuxtApp()
          this.fetchError = (error instanceof Error ? error.message : null) || $i18n.t('autoDelete.fetchFailed')
          this.fetchRunning = false
        }
      )
      this.fetchRunning = false
    },

    // Resets

    resetLogin() {
      this.loginRunning = false
      this.loginLogs = []
      this.loginResult = null
      this.loginError = null
    },

    resetScan() {
      this.scanRunning = false
      this.scanLogs = []
      this.scanProgress = null
      this.scannedComments = []
      this.judiComments = []
      this.scanResult = null
      this.scanError = null
    },

    resetAll() {
      this.resetLogin()
      this.resetScan()
      this.deleteRunning = false
      this.deleteLogs = []
      this.deleteError = null
      this.fetchedComments = []
      this.fetchRunning = false
      this.fetchError = null
    }
  }
})
