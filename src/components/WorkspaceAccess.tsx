import { FormEvent, useEffect, useState } from 'react'
import { Check, Clipboard, KeyRound, X } from 'lucide-react'
import { api } from '../api'
import { importWorkspaceKey } from '../workspace'

export function WorkspaceAccess({ onClose }: { onClose: () => void }) {
  const [key, setKey] = useState('')
  const [incoming, setIncoming] = useState('')
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    api.workspaceAccess()
      .then(result => { if (active) setKey(result.key) })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'Could not load workspace access') })
    return () => { active = false }
  }, [])

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(key)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setError('Clipboard access was unavailable. Select and copy the key manually.')
    }
  }
  const connect = (event: FormEvent) => {
    event.preventDefault()
    try {
      importWorkspaceKey(incoming)
      window.location.assign('/')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Invalid workspace key')
    }
  }
  return <div className="modal-backdrop" role="presentation" onMouseDown={event => event.target === event.currentTarget && onClose()}>
    <section className="workspace-modal" role="dialog" aria-modal="true" aria-labelledby="workspace-title">
      <button className="icon-btn modal-close" onClick={onClose} aria-label="Close workspace access"><X /></button>
      <span className="feature-icon"><KeyRound /></span>
      <h2 id="workspace-title">Workspace access</h2>
      <p>Your private access key lets an authorized device open the same persisted evaluation history. Treat it like a password.</p>
      <label>Current workspace key<div className="key-copy"><code>{key || 'Loading secure access key…'}</code><button className="button button-secondary" onClick={copy} disabled={!key}>{copied ? <Check size={16} /> : <Clipboard size={16} />}{copied ? 'Copied' : 'Copy'}</button></div></label>
      <form onSubmit={connect}>
        <label>Connect another workspace<input value={incoming} onChange={event => setIncoming(event.target.value)} placeholder="Paste a workspace key" autoComplete="off" /></label>
        {error && <div className="field-error">{error}</div>}
        <button className="button button-primary" disabled={!incoming.trim()}>Connect and reload</button>
      </form>
    </section>
  </div>
}
