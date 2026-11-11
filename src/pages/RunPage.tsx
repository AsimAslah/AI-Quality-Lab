import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AlertTriangle, ArrowLeft, CheckCircle2, Clock3, Download, Eye, FileJson, Radio, ShieldAlert } from 'lucide-react'
import { api } from '../api'
import type { ExecutionEvent, RunDetail } from '../types'
import { STAGES } from '../types'
import { ExecutionGraph } from '../components/ExecutionGraph'
import { ReplayControls, useReplay } from '../components/ReplayControls'
import { ScoreRing } from '../components/ScoreRing'
import { StatusBadge } from '../components/StatusBadge'

function download(name: string, content: string, type: string) { const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = name; a.click(); URL.revokeObjectURL(url) }

export function RunPage() {
  const { id = '' } = useParams(); const [run, setRun] = useState<RunDetail | null>(null); const [events, setEvents] = useState<ExecutionEvent[]>([]); const [selected, setSelected] = useState<string | null>(null); const [replayMode, setReplayMode] = useState(false); const [error, setError] = useState(''); const [streamState, setStreamState] = useState<'connecting' | 'live' | 'reconnecting' | 'complete'>('connecting')
  const replay = useReplay(events)
  const displayed = replayMode ? replay.visible : events
  useEffect(() => {
    let source: EventSource | null = null; let cancelled = false
    Promise.all([api.getRun(id), api.getEvents(id)]).then(([r, e]) => {
      if (cancelled) return; setRun(r); setEvents(e.items)
      if (!['completed', 'completed_with_warnings', 'failed'].includes(r.status)) {
        const last = e.items.at(-1)?.sequence ?? 0
        source = new EventSource(`/api/evaluations/${id}/stream?after=${last}`)
        source.onopen = () => setStreamState('live')
        source.addEventListener('execution', event => { const next = JSON.parse((event as MessageEvent).data) as ExecutionEvent; setEvents(items => items.some(item => item.id === next.id) ? items : [...items, next]); api.getRun(id).then(setRun) })
        source.addEventListener('complete', () => { setStreamState('complete'); source?.close(); api.getRun(id).then(setRun) })
        source.onerror = () => { if (!cancelled) setStreamState('reconnecting') }
      }
    }).catch(e => setError(e.message))
    return () => { cancelled = true; source?.close() }
  }, [id])
  const selectedEvents = useMemo(() => displayed.filter(e => e.stage_id === selected), [displayed, selected])
  const latestSelected = selectedEvents.at(-1)
  const terminal = run && ['completed', 'completed_with_warnings', 'failed'].includes(run.status)
  if (error) return <div className="alert alert-error">{error}</div>
  if (!run) return <div className="loading-page"><span className="spinner" />Loading evaluation…</div>
  const exportJson = () => download(`${run.title.replace(/\W+/g, '-').toLowerCase()}.json`, JSON.stringify({ run, events }, null, 2), 'application/json')
  const exportMarkdown = () => { if (!run.report) return; const lines = [`# ${run.title}`, ``, `**Score:** ${run.report.overall_score}/100`, ``, `## Criteria`, ...run.report.rubric_results.flatMap(r => [`### ${r.name} — ${r.score}/100`, ...r.evidence.map(e => `- ${e}`), ``]), `## Limitations`, ...run.report.limitations.map(l => `- ${l}`)]; download(`${run.title.replace(/\W+/g, '-').toLowerCase()}.md`, lines.join('\n'), 'text/markdown') }
  return <div className="run-page">
    <div className="run-header"><div><Link className="back-link" to="/history"><ArrowLeft size={15} />History</Link><div className="run-title"><h1>{run.title}</h1><StatusBadge status={run.status} /></div><p>{terminal ? 'Execution recorded and ready to inspect.' : 'The diagram is following persisted backend events in real time.'}</p></div><div className="run-actions"><button className="button button-secondary" onClick={exportJson}><FileJson size={16} />JSON</button>{run.report && <button className="button button-secondary" onClick={exportMarkdown}><Download size={16} />Markdown</button>}</div></div>
    <section className="execution-panel panel"><div className="execution-toolbar"><div><span className={`live-indicator ${terminal ? 'done' : ''}`}><Radio size={14} />{terminal ? 'Execution complete' : streamState === 'reconnecting' ? 'Reconnecting to event stream' : streamState === 'live' ? 'Live backend events' : 'Connecting to backend events'}</span><small>{events.length} recorded events</small></div>{terminal && <button className={`button ${replayMode ? 'button-primary' : 'button-secondary'}`} onClick={() => setReplayMode(v => !v)}><Eye size={16} />{replayMode ? 'Exit replay' : 'Replay execution'}</button>}</div>{replayMode && <ReplayControls replay={replay} />}<ExecutionGraph events={displayed} selected={selected} onSelect={setSelected} />
      <div className="execution-footer"><span><i className="legend running" />Running</span><span><i className="legend completed" />Completed</span><span><i className="legend recovered" />Recovered</span><span><i className="legend failed" />Failed</span><span><Clock3 size={14} />Actual server durations</span></div>
    </section>
    {selected && <section className="panel inspector"><div className="section-heading"><div><span className="eyebrow">STAGE INSPECTOR</span><h2>{STAGES.find(s => s.id === selected)?.name}</h2></div><button className="icon-btn" onClick={() => setSelected(null)}>×</button></div>{latestSelected ? <><div className="inspector-meta"><StatusBadge status={latestSelected.status} /><span>{new Date(latestSelected.occurred_at).toLocaleTimeString()}</span><strong>{latestSelected.duration_ms == null ? '—' : `${latestSelected.duration_ms.toFixed(3)} ms`}</strong></div><p>{latestSelected.message}</p><pre>{JSON.stringify(latestSelected.metadata, null, 2)}</pre>{latestSelected.error_message && <div className="alert alert-error">{latestSelected.error_message}</div>}</> : <p>Waiting for this stage.</p>}</section>}
    {run.status === 'failed' && <div className="alert alert-error"><AlertTriangle /><div><b>Evaluation stopped</b><span>The failure is recorded in the event timeline. Your original submission remains saved.</span></div></div>}
    {run.report && <Results report={run.report} />}
  </div>
}

function Results({ report }: { report: NonNullable<RunDetail['report']> }) {
  return <div className="results"><section className="panel result-overview"><ScoreRing score={report.overall_score} /><div><span className="eyebrow">EVALUATION REPORT</span><h2>{report.overall_score >= 80 ? 'Strong response, with review points' : report.overall_score >= 60 ? 'Promising, but needs revision' : 'Substantial revision recommended'}</h2><p>This score combines the configured weights. Evidence and method labels below show what each result can—and cannot—establish.</p><span className="capability"><CheckCircle2 size={15} />{report.capability.replaceAll('_', ' ')}</span></div><div className="analysis-chips"><span><b>{report.analysis.word_count}</b> words</span><span><b>{report.analysis.paragraph_count}</b> paragraphs</span><span><b>{report.privacy.finding_count}</b> privacy matches</span></div></section>
    <section className="panel"><div className="section-heading"><div><span className="eyebrow">WEIGHTED RUBRIC</span><h2>Criterion breakdown</h2></div></div><div className="result-list">{report.rubric_results.map(result => <article key={result.criterion_id}><div className="result-score"><strong>{result.score.toFixed(1)}</strong><span>/100</span></div><div><div className="result-title"><h3>{result.name}</h3><span className={`method method-${result.method}`}>{result.method}</span><small>Weight {result.weight}</small></div>{result.evidence.map((item, i) => <p key={i}><CheckCircle2 size={15} />{item}</p>)}{result.limitations.map((item, i) => <p className="limitation" key={`l-${i}`}><AlertTriangle size={15} />{item}</p>)}</div></article>)}</div></section>
    <div className="content-grid two"><section className="panel"><span className="feature-icon amber"><ShieldAlert /></span><h2>Privacy scan</h2><p>{report.privacy.finding_count ? `${report.privacy.finding_count} potential pattern matches require review.` : 'No configured PII patterns were detected.'}</p>{report.privacy.findings.map(item => <div className="privacy-finding" key={item.category}><b>{item.category.replaceAll('_', ' ')}</b><span>{item.count} · {item.severity}</span></div>)}</section><section className="panel"><span className="feature-icon"><AlertTriangle /></span><h2>Important limitations</h2><ul className="plain-list">{report.limitations.map((item, i) => <li key={i}>{item}</li>)}</ul></section></div>
  </div>
}
