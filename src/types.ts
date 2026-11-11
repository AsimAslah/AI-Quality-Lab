export type RunStatus = 'queued' | 'running' | 'completed' | 'completed_with_warnings' | 'failed'
export type StageStatus = 'pending' | 'running' | 'completed' | 'failed' | 'retrying' | 'recovered' | 'skipped'

export interface RubricCriterion {
  id: string
  name: string
  description: string
  weight: number
  mode: 'keywords' | 'structure' | 'length' | 'reference' | 'instruction'
  required_phrases: string[]
}

export interface RunSummary {
  id: string
  title: string
  status: RunStatus
  overall_score: number | null
  warning_count: number
  current_stage: string | null
  created_at: string
  completed_at: string | null
}

export interface CriterionResult {
  criterion_id: string
  name: string
  weight: number
  score: number
  method: string
  evidence: string[]
  limitations: string[]
}

export interface EvaluationReport {
  overall_score: number
  capability: string
  rubric_results: CriterionResult[]
  analysis: Record<string, number>
  privacy: {
    finding_count: number
    categories: string[]
    findings: Array<{ category: string; count: number; severity: string; note: string }>
  }
  model_evaluation: null | Record<string, unknown>
  limitations: string[]
  generated_at: string
}

export interface RunDetail extends RunSummary {
  prompt: string
  response: string
  reference: string | null
  rubric: RubricCriterion[]
  preferences: Record<string, unknown>
  report: EvaluationReport | null
  error_code: string | null
}

export interface ExecutionEvent {
  id: string
  run_id: string
  sequence: number
  stage_id: string
  event_type: string
  status: StageStatus
  occurred_at: string
  duration_ms: number | null
  message: string
  metadata: Record<string, unknown>
  error_code: string | null
  error_message: string | null
}

export const STAGES = [
  { id: 'validate_input', name: 'Receive & validate', layer: 'Browser → API' },
  { id: 'persist_request', name: 'Save request', layer: 'Database' },
  { id: 'analyze_response', name: 'Analyze response', layer: 'Evaluation engine' },
  { id: 'privacy_scan', name: 'Scan potential PII', layer: 'Privacy engine' },
  { id: 'rubric_evaluation', name: 'Evaluate rubric', layer: 'Evaluation engine' },
  { id: 'ai_evaluation', name: 'Optional AI review', layer: 'External provider' },
  { id: 'aggregate_results', name: 'Aggregate results', layer: 'Evaluation engine' },
  { id: 'persist_report', name: 'Store report', layer: 'Database → Browser' },
] as const
