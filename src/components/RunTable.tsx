import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import type { RunSummary } from '../types'
import { StatusBadge } from './StatusBadge'

const formatDate = (value: string) => new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))

export function RunTable({ runs, empty = 'No evaluations yet.' }: { runs: RunSummary[]; empty?: string }) {
  if (!runs.length) return <div className="empty-state"><span>◎</span><p>{empty}</p><Link className="button button-primary" to="/new">Run an evaluation</Link></div>
  return <div className="table-scroll"><table><thead><tr><th>Evaluation</th><th>Status</th><th>Score</th><th>Created</th><th><span className="sr-only">Open</span></th></tr></thead><tbody>
    {runs.map(run => <tr key={run.id}><td><b>{run.title}</b><small>{run.warning_count} warning{run.warning_count === 1 ? '' : 's'}</small></td><td><StatusBadge status={run.status} /></td><td><strong>{run.overall_score == null ? '—' : run.overall_score.toFixed(1)}</strong></td><td>{formatDate(run.created_at)}</td><td><Link className="table-link" to={`/runs/${run.id}`} aria-label={`Open ${run.title}`}><ArrowRight size={17} /></Link></td></tr>)}
  </tbody></table></div>
}
