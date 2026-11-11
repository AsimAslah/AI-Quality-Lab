import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, CheckCircle2, Gauge, Plus, ShieldAlert, Waypoints } from 'lucide-react'
import { api } from '../api'
import type { RunSummary } from '../types'
import { RunTable } from '../components/RunTable'

type Dashboard = { total_runs: number; completed_runs: number; average_score: number | null; privacy_warnings: number; recent: RunSummary[] }

export function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { api.dashboard().then(setData).catch(e => setError(e.message)) }, [])
  return <>
    <section className="hero">
      <div><span className="eyebrow"><Waypoints size={14} />EXPLAINABLE AI EVALUATION</span><h1>Evaluate the answer.<br /><em>See every decision.</em></h1><p>Turn a prompt, response, and rubric into an evidence-backed report—while a live execution map shows the real backend work.</p><div className="hero-actions"><Link className="button button-primary button-large" to="/new"><Plus size={18} />New evaluation</Link><Link className="button button-ghost button-large" to="/architecture">Explore the system <ArrowRight size={17} /></Link></div></div>
      <div className="hero-visual"><div className="mini-flow"><span className="pulse-dot" /><b>Live pipeline</b><small>Events originate on the server</small><div className="mini-stages"><i className="done" /><i className="done" /><i className="active" /><i /><i /><i /><i /><i /></div><div className="mini-metric"><strong>8</strong><span>observable stages</span></div></div></div>
    </section>
    {error && <div className="alert alert-error">{error}</div>}
    <section className="metric-grid">
      <article><span className="metric-icon purple"><Gauge /></span><div><small>Average score</small><strong>{data?.average_score == null ? '—' : data.average_score.toFixed(1)}</strong></div></article>
      <article><span className="metric-icon green"><CheckCircle2 /></span><div><small>Completed runs</small><strong>{data?.completed_runs ?? '—'}</strong></div></article>
      <article><span className="metric-icon amber"><ShieldAlert /></span><div><small>Privacy warnings</small><strong>{data?.privacy_warnings ?? '—'}</strong></div></article>
      <article><span className="metric-icon blue"><Waypoints /></span><div><small>Total evaluations</small><strong>{data?.total_runs ?? '—'}</strong></div></article>
    </section>
    <section className="panel"><div className="section-heading"><div><span className="eyebrow">YOUR WORKSPACE</span><h2>Recent evaluations</h2></div><Link className="text-link" to="/history">View all <ArrowRight size={15} /></Link></div>{data ? <RunTable runs={data.recent} /> : <div className="skeleton-block" />}</section>
  </>
}
