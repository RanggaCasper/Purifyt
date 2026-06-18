import { defineStore } from 'pinia'
import { useApiBase } from '~/composables/useApiBase'

type ServerCommand = 'server_status' | 'start_server' | 'stop_server'

const isDesktopRuntime = () => import.meta.client && window.location.protocol === 'tauri:'

async function invokeServer<T>(command: ServerCommand): Promise<T> {
  const { invoke } = await import('@tauri-apps/api/core')
  return await invoke<T>(command)
}

interface ServerState {
  isDesktop: boolean
  running: boolean
  loading: boolean
  error: string | null
  pollTimer: ReturnType<typeof setInterval> | null
}

export const useServerStore = defineStore('server', {
  state: (): ServerState => ({
    isDesktop: false,
    running: false,
    loading: false,
    error: null,
    pollTimer: null
  }),

  actions: {
    async checkStatus() {
      this.isDesktop = isDesktopRuntime()
      this.error = null

      try {
        if (this.isDesktop) {
          this.running = await invokeServer<boolean>('server_status')
          return this.running
        }

        const { resolveApiBase } = useApiBase()
        const apiBase = await resolveApiBase()
        await $fetch(`${apiBase}/`, { timeout: 1500 })
        this.running = true
      } catch {
        this.running = false
      }

      return this.running
    },

    async startServer() {
      if (!this.isDesktop) return await this.checkStatus()

      this.loading = true
      this.error = null
      try {
        this.running = await invokeServer<boolean>('start_server')
        if (!this.running) this.error = 'Server belum merespons setelah dinyalakan'
        return this.running
      } catch (error: unknown) {
        this.running = false
        this.error = error instanceof Error ? error.message : String(error)
        return false
      } finally {
        this.loading = false
      }
    },

    async stopServer() {
      if (!this.isDesktop) return await this.checkStatus()

      this.loading = true
      this.error = null
      try {
        const stillRunning = await invokeServer<boolean>('stop_server')
        this.running = stillRunning
        if (stillRunning) this.error = 'Server masih berjalan atau bukan proses yang dibuka aplikasi'
        return !stillRunning
      } catch (error: unknown) {
        this.error = error instanceof Error ? error.message : String(error)
        return false
      } finally {
        this.loading = false
      }
    },

    startPolling() {
      if (this.pollTimer) return
      this.checkStatus()
      this.pollTimer = setInterval(() => this.checkStatus(), 5000)
    },

    stopPolling() {
      if (!this.pollTimer) return
      clearInterval(this.pollTimer)
      this.pollTimer = null
    }
  }
})
