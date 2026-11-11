import type { ExecutionEvent, RunDetail, RunSummary } from './types'
import { getWorkspaceKey } from './workspace'

export class ApiError extends Error {
  constructor(message: string, public status: number, public details?: unknown) {
    super(message)
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-Workspace-Key': getWorkspaceKey(), ...(init?.headers ?? {}) },
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new ApiError(data.detail ?? 'Request failed', response.status, data.errors)
  return data as T
}

export const api = {
  dashboard: () => request<{ total_runs: number; completed_runs: number; average_score: number | null; privacy_warnings: number; recent: RunSummary[] }>('/api/dashboard'),
  listRuns: () => request<{ items: RunSummary[]; total: number }>('/api/evaluations'),
  getRun: (id: string) => request<RunDetail>(`/api/evaluations/${id}`),
  getEvents: (id: string) => request<{ items: ExecutionEvent[] }>(`/api/evaluations/${id}/events`),
  createRun: (payload: unknown, idempotencyKey: string) => request<{ run: RunDetail; duplicate: boolean }>('/api/evaluations', {
    method: 'POST', body: JSON.stringify(payload), headers: { 'Idempotency-Key': idempotencyKey },
  }),
}
