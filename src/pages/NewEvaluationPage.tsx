import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, ChevronRight, Info, Plus, Sparkles, Trash2 } from 'lucide-react'
import { api, ApiError } from '../api'
import type { RubricCriterion } from '../types'

const seedCriteria: RubricCriterion[] = [
  { id: 'instruction_following', name: 'Instruction following', description: 'Does the response address the prompt and its explicit instructions?', weight: 8, mode: 'instruction', required_phrases: [] },
  { id: 'response_structure', name: 'Clear structure', description: 'Is the response organized into readable sections or paragraphs?', weight: 5, mode: 'structure', required_phrases: [] },
  { id: 'required_content', name: 'Required content', description: 'Does the response include the phrases or concepts I require?', weight: 7, mode: 'keywords', required_phrases: [] },
]

const newCriterion = (): RubricCriterion => ({ id: `criterion_${crypto.randomUUID().slice(0, 8)}`, name: 'New criterion', description: 'Describe what the response should demonstrate.', weight: 5, mode: 'instruction', required_phrases: [] })

export function NewEvaluationPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ title: '', prompt: '', response: '', reference: '', use_ai: false })
  const [rubric, setRubric] = useState(seedCriteria)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Array<{ field: string; message: string }>>([])
  const [submitting, setSubmitting] = useState(false)
  const updateCriterion = (index: number, patch: Partial<RubricCriterion>) => setRubric(items => items.map((item, i) => i === index ? { ...item, ...patch } : item))
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(''); setFieldErrors([]); setSubmitting(true)
    try {
      const result = await api.createRun({
        title: form.title || `Evaluation ${new Date().toLocaleDateString()}`, prompt: form.prompt, response: form.response,
        reference: form.reference || null, rubric, preferences: { use_ai: form.use_ai, redact_before_ai: true, failure_mode: 'none' },
      }, crypto.randomUUID())
      navigate(`/runs/${result.run.id}`)
    } catch (e) {
      const err = e as ApiError; setError(err.message)
      if (Array.isArray(err.details)) setFieldErrors(err.details as Array<{ field: string; message: string }>)
    } finally { setSubmitting(false) }
  }
  return <div className="narrow-page">
    <div className="page-heading"><div><span className="eyebrow">NEW EVALUATION</span><h1>Set the quality bar</h1><p>Supply the task, candidate response, and a weighted rubric. We’ll show every check as it actually runs.</p></div><div className="stepper"><span className="active">1</span><i /><span>2</span><i /><span>3</span></div></div>
    {error && <div className="alert alert-error"><b>{error}</b>{fieldErrors.map((item, i) => <small key={i}>{item.field}: {item.message}</small>)}</div>}
    <form onSubmit={submit} className="evaluation-form">
      <section className="panel form-section"><div className="form-section-title"><span>01</span><div><h2>Evaluation content</h2><p>The submitted material is stored for your private browser session.</p></div></div>
        <label>Evaluation title <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="e.g. Support answer quality review" maxLength={160} /></label>
        <div className="form-grid"><label>Original prompt <textarea required value={form.prompt} onChange={e => setForm({ ...form, prompt: e.target.value })} placeholder="What was the model asked to do?" rows={7} /></label><label>AI-generated response <textarea required value={form.response} onChange={e => setForm({ ...form, response: e.target.value })} placeholder="Paste the response to evaluate…" rows={7} /></label></div>
        <label>Reference answer or supporting context <span className="optional">Optional</span><textarea value={form.reference} onChange={e => setForm({ ...form, reference: e.target.value })} placeholder="Add a trusted reference. Overlap is labeled as heuristic—not factual proof." rows={4} /></label>
      </section>
      <section className="panel form-section"><div className="form-section-title"><span>02</span><div><h2>Weighted rubric</h2><p>Choose a measurable mode for each criterion and tune its influence.</p></div></div>
        <div className="criterion-list">{rubric.map((criterion, index) => <article className="criterion-card" key={criterion.id}>
          <div className="criterion-head"><strong>Criterion {index + 1}</strong><button type="button" className="icon-btn danger" disabled={rubric.length === 1} onClick={() => setRubric(items => items.filter((_, i) => i !== index))} aria-label="Remove criterion"><Trash2 size={16} /></button></div>
          <div className="form-grid compact"><label>Name<input value={criterion.name} onChange={e => updateCriterion(index, { name: e.target.value })} required /></label><label>Check type<select value={criterion.mode} onChange={e => updateCriterion(index, { mode: e.target.value as RubricCriterion['mode'] })}><option value="instruction">Instruction cues · heuristic</option><option value="keywords">Required phrases · deterministic</option><option value="structure">Response structure · deterministic</option><option value="length">Response length · deterministic</option><option value="reference">Reference overlap · heuristic</option></select></label></div>
          <label>Description<input value={criterion.description} onChange={e => updateCriterion(index, { description: e.target.value })} required /></label>
          <div className="criterion-controls"><label>Weight <span>{criterion.weight}/10</span><input type="range" min="1" max="10" value={criterion.weight} onChange={e => updateCriterion(index, { weight: Number(e.target.value) })} /></label><label>Required phrases <span className="optional">Comma separated</span><input value={criterion.required_phrases.join(', ')} onChange={e => updateCriterion(index, { required_phrases: e.target.value.split(',').map(v => v.trim()).filter(Boolean) })} placeholder="privacy, limitations" /></label></div>
        </article>)}</div>
        <button type="button" className="button button-secondary" onClick={() => setRubric(items => [...items, newCriterion()])} disabled={rubric.length >= 12}><Plus size={16} />Add criterion</button>
      </section>
      <section className="panel form-section"><div className="form-section-title"><span>03</span><div><h2>Evaluation preferences</h2><p>The deterministic workflow always works. External AI is optional.</p></div></div>
        <label className="toggle-card"><input type="checkbox" checked={form.use_ai} onChange={e => setForm({ ...form, use_ai: e.target.checked })} /><span className="toggle" /><Sparkles /><div><strong>Request model-assisted judgment</strong><small>Runs only if the server has a provider key and the privacy gate permits it. Inputs are redacted first.</small></div></label>
        <div className="privacy-note"><Info size={17} /><span>Potential PII is pattern-based and can include false positives. Raw matches are never copied into execution logs.</span></div>
      </section>
      <div className="form-submit"><div><Check size={16} />Your input remains in this form if validation fails.</div><button className="button button-primary button-large" disabled={submitting}>{submitting ? 'Starting evaluation…' : <>Start evaluation <ChevronRight size={18} /></>}</button></div>
    </form>
  </div>
}
