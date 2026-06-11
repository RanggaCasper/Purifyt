export interface LogMeta {
  icon: string
  colorClass: string
}

const defaultMeta: LogMeta = { icon: 'i-lucide-info', colorClass: 'text-slate-400' }

// Auto-delete & login events (keyed by step or type)
const autoDeleteMap: Record<string, LogMeta> = {
  browser: { icon: 'i-lucide-globe', colorClass: 'text-blue-400' },
  navigate: { icon: 'i-lucide-compass', colorClass: 'text-sky-400' },
  input_email: { icon: 'i-lucide-mail', colorClass: 'text-violet-400' },
  input_password: { icon: 'i-lucide-lock', colorClass: 'text-amber-400' },
  verify: { icon: 'i-lucide-shield-check', colorClass: 'text-green-400' },
  save_cookies: { icon: 'i-lucide-cookie', colorClass: 'text-orange-400' },
  save_db: { icon: 'i-lucide-database', colorClass: 'text-emerald-400' },
  login: { icon: 'i-lucide-log-in', colorClass: 'text-blue-400' },
  fetch_comments: { icon: 'i-lucide-message-square', colorClass: 'text-violet-400' },
  predict: { icon: 'i-lucide-sparkles', colorClass: 'text-yellow-400' },
  delete: { icon: 'i-lucide-trash-2', colorClass: 'text-red-400' },
  fetch: { icon: 'i-lucide-download', colorClass: 'text-blue-400' },
  done: { icon: 'i-lucide-circle-check-big', colorClass: 'text-emerald-400' },
  error: { icon: 'i-lucide-alert-circle', colorClass: 'text-red-400' }
}

// Explorer events (keyed by type)
const explorerMap: Record<string, LogMeta> = {
  fetch_info: { icon: 'i-lucide-search', colorClass: 'text-blue-400' },
  video_info: { icon: 'i-lucide-video', colorClass: 'text-sky-400' },
  fetch_comments: { icon: 'i-lucide-message-square', colorClass: 'text-violet-400' },
  fetch_comments_done: { icon: 'i-lucide-check-circle', colorClass: 'text-green-400' },
  label_start: { icon: 'i-lucide-tag', colorClass: 'text-amber-400' },
  label_done: { icon: 'i-lucide-sparkles', colorClass: 'text-yellow-400' },
  sample: { icon: 'i-lucide-filter', colorClass: 'text-cyan-400' },
  saving: { icon: 'i-lucide-save', colorClass: 'text-orange-400' },
  complete: { icon: 'i-lucide-circle-check-big', colorClass: 'text-emerald-400' },
  channel_info_fetch: { icon: 'i-lucide-tv-minimal', colorClass: 'text-blue-400' },
  channel_info: { icon: 'i-lucide-tv', colorClass: 'text-sky-400' },
  fetch_videos: { icon: 'i-lucide-list-video', colorClass: 'text-indigo-400' },
  fetch_videos_done: { icon: 'i-lucide-clapperboard', colorClass: 'text-purple-400' },
  video_start: { icon: 'i-lucide-play-circle', colorClass: 'text-blue-300' },
  video_comments: { icon: 'i-lucide-messages-square', colorClass: 'text-violet-400' },
  video_no_judi: { icon: 'i-lucide-shield-check', colorClass: 'text-green-400' },
  video_saved: { icon: 'i-lucide-database', colorClass: 'text-emerald-400' }
}

// Merged lookup (auto-delete keys take priority, explorer keys fill in the rest)
const mergedMap: Record<string, LogMeta> = { ...explorerMap, ...autoDeleteMap }

export function useLogMeta() {
  /**
   * Resolve icon + color for a log entry.
   * For auto-delete logs, pass both `type` and `step` (step takes priority).
   * For explorer logs, pass just `type`.
  */
  function getLogMeta(type: string, step?: string): LogMeta {
    return mergedMap[step ?? type] ?? defaultMeta
  }

  return { getLogMeta }
}
