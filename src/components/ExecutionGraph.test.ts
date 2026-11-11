import { describe, expect, it } from 'vitest'
import { latestStageEvents } from './ExecutionGraph'
import type { ExecutionEvent } from '../types'

const event = (sequence: number, stage_id: string, status: ExecutionEvent['status']): ExecutionEvent => ({ id: `${sequence}`, run_id: 'r', sequence, stage_id, status, event_type: 'stage', occurred_at: new Date(sequence).toISOString(), duration_ms: sequence, message: '', metadata: {}, error_code: null, error_message: null })

describe('execution reconstruction', () => {
  it('keeps the latest persisted state for every stage', () => {
    const state = latestStageEvents([event(1, 'validate_input', 'pending'), event(2, 'validate_input', 'running'), event(3, 'privacy_scan', 'completed')])
    expect(state.get('validate_input')?.status).toBe('running')
    expect(state.get('privacy_scan')?.duration_ms).toBe(3)
  })
})
