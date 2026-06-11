// SSE Event Payloads

export interface AutoDeleteStatusEvent {
  type: 'status'
  step: string
  message: string
  total_comments?: number
}

export interface AutoDeleteCommentEvent {
  type: 'comment'
  index: number
  total: number
  comment_id: string
  text: string
  author: string
  label: 0 | 1
  confidence: number
}

export interface AutoDeleteJudiEvent {
  type: 'judi_detected'
  index: number
  total: number
  comment_id: string
  text: string
  author: string
  label: 1
  confidence: number
}

export interface AutoDeleteDeleteEvent {
  type: 'delete'
  deleted: number
  requested: number
  message: string
}

export interface AutoDeleteLoginDoneEvent {
  type: 'done'
  logged_in: boolean
  email: string
  channel_name: string
  cookies_saved: boolean
  cookie_count: number
  cookie_path: string
  message: string
}

export interface AutoDeleteScanDoneEvent {
  type: 'done'
  scanned: number
  detected: number
  deleted: number
  errors: number
  judi_comments: AutoDeleteCommentEvent[]
}

export interface AutoDeleteErrorEvent {
  type: 'error'
  message: string
}

export type AutoDeleteEvent
  = | AutoDeleteStatusEvent
    | AutoDeleteCommentEvent
    | AutoDeleteJudiEvent
    | AutoDeleteDeleteEvent
    | AutoDeleteLoginDoneEvent
    | AutoDeleteScanDoneEvent
    | AutoDeleteErrorEvent

// Cookie / Account

export interface CookieAccount {
  id: number
  email: string
  channel_name: string
  cookie_path: string
  cookie_count: number
  is_active: boolean
  file_exists: boolean
  created_at: string
  updated_at: string
}

export interface CookieAccountDetail extends CookieAccount {
  file_info: {
    exists: boolean
    path: string
    cookie_count: number
  }
}

// Request Payloads

export interface LoginPayload {
  email: string
  password: string
  headless?: boolean
  timeout?: number
}

export interface ScanPayload {
  video_id: string
  email: string
  threshold?: number
  headless?: boolean
}

export interface DeletePayload {
  video_id: string
  email: string
  comment_ids: string[]
  headless?: boolean
}

export interface FetchCommentsPayload {
  video_id: string
  email: string
  headless?: boolean
}

// Scan result (accumulated from SSE)

export interface ScannedComment {
  comment_id: string
  text: string
  author: string
  label: 0 | 1
  confidence: number
}

export interface ScanResult {
  scanned: number
  detected: number
  deleted: number
  errors: number
  judiComments: ScannedComment[]
}
