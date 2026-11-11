import { useEffect, useState } from 'react'
import { Filter, Search } from 'lucide-react'
import { api } from '../api'
import type { RunSummary } from '../types'
import { RunTable } from '../components/RunTable'

export function HistoryPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]); const [query, setQuery] = useState(''); const [status, setStatus] = useState('all'); const [error, setError] = useState('')
  useEffect(() => { api.listRuns().then(d => setRuns(d.items)).catch(e => setError(e.message)) }, [])
  const filtered = runs.filter(run => run.title.toLowerCase().includes(query.toLowerCase()) && (status === 'all' || run.status === status))
  return <><div className="page-heading"><div><span className="eyebrow">PERSISTED WORK</span><h1>Evaluation history</h1><p>Reopen reports and replay the exact events recorded during execution.</p></div></div>{error && <div className="alert alert-error">{error}</div>}<section className="panel"><div className="filterbar"><label><Search size={17} /><input placeholder="Search evaluations" value={query} onChange={e => setQuery(e.target.value)} /></label><label><Filter size={16} /><select value={status} onChange={e => setStatus(e.target.value)}><option value="all">All statuses</option><option value="completed">Completed</option><option value="completed_with_warnings">With warnings</option><option value="running">Running</option><option value="failed">Failed</option></select></label></div><RunTable runs={filtered} empty="No matching evaluations." /></section></>
}
