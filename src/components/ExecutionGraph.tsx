import { useEffect, useMemo, useState } from 'react'
import { Background, Controls, Handle, Position, ReactFlow, type NodeProps } from '@xyflow/react'
import { Check, Circle, Clock3, Database, RotateCcw, ScanSearch, Server, SkipForward, Sparkles, TriangleAlert, X } from 'lucide-react'
import type { ExecutionEvent, StageStatus } from '../types'
import { STAGES } from '../types'

const statusIcon = { pending: Circle, running: Clock3, completed: Check, failed: X, retrying: RotateCcw, recovered: Check, skipped: SkipForward }
const layerIcon = { 'Browser → API': Server, Database, 'Evaluation engine': ScanSearch, 'Privacy engine': TriangleAlert, 'External provider': Sparkles, 'Database → Browser': Database }

type StageNodeData = { label: string; layer: string; status: StageStatus; event?: ExecutionEvent; selected: boolean }

function StageNode({ data }: NodeProps) {
  const d = data as StageNodeData
  const Icon = statusIcon[d.status]
  const Layer = layerIcon[d.layer as keyof typeof layerIcon] ?? Server
  return <div className={`flow-node flow-${d.status} ${d.selected ? 'flow-selected' : ''}`}>
    <Handle type="target" position={Position.Left} />
    <div className="flow-node-top"><span><Layer size={13} />{d.layer}</span><Icon size={15} /></div>
    <strong>{d.label}</strong>
    <small>{d.event?.message ?? 'Waiting to run'}</small>
    <div className="flow-node-foot"><span>{d.status}</span><span>{d.event?.duration_ms != null ? `${d.event.duration_ms.toFixed(1)} ms` : '—'}</span></div>
    <Handle type="source" position={Position.Right} />
  </div>
}

const nodeTypes = { stage: StageNode }

export function latestStageEvents(events: ExecutionEvent[]) {
  const map = new Map<string, ExecutionEvent>()
  for (const event of events) map.set(event.stage_id, event)
  return map
}

export function ExecutionGraph({ events, selected, onSelect }: { events: ExecutionEvent[]; selected: string | null; onSelect: (id: string) => void }) {
  const latest = useMemo(() => latestStageEvents(events), [events])
  const [mobile, setMobile] = useState(() => typeof window !== 'undefined' && window.innerWidth <= 700)
  useEffect(() => {
    const update = () => setMobile(window.innerWidth <= 700)
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])
  const nodes = useMemo(() => STAGES.map((stage, index) => ({
    id: stage.id, type: 'stage', position: { x: (index % 4) * 270, y: Math.floor(index / 4) * 180 },
    data: { label: stage.name, layer: stage.layer, status: latest.get(stage.id)?.status ?? 'pending', event: latest.get(stage.id), selected: stage.id === selected },
  })), [latest, selected])
  const edges = useMemo(() => STAGES.slice(0, -1).map((stage, index) => ({
    id: `${stage.id}-${STAGES[index + 1].id}`, source: stage.id, target: STAGES[index + 1].id,
    animated: latest.get(STAGES[index + 1].id)?.status === 'running',
    className: latest.get(stage.id)?.status === 'completed' ? 'edge-complete' : '',
  })), [latest])
  if (mobile) return <div className="mobile-flow" aria-label="Live execution diagram">
    {STAGES.map((stage, index) => {
      const event = latest.get(stage.id)
      const status = event?.status ?? 'pending'
      const Icon = statusIcon[status]
      const Layer = layerIcon[stage.layer as keyof typeof layerIcon] ?? Server
      return <button key={stage.id} type="button" className={`mobile-flow-node flow-${status} ${selected === stage.id ? 'flow-selected' : ''}`} onClick={() => onSelect(stage.id)}>
        <span className="mobile-flow-number">{String(index + 1).padStart(2, '0')}</span>
        <span className="mobile-flow-copy"><small><Layer size={12} />{stage.layer}</small><strong>{stage.name}</strong><em>{event?.message ?? 'Waiting to run'}</em></span>
        <span className="mobile-flow-status"><Icon size={17} /><b>{status}</b><small>{event?.duration_ms != null ? `${event.duration_ms.toFixed(1)} ms` : '—'}</small></span>
      </button>
    })}
  </div>
  return <div className="flow-canvas" aria-label="Live execution diagram">
    <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView minZoom={0.55} maxZoom={1.25} onNodeClick={(_, node) => onSelect(node.id)} nodesDraggable={false} nodesConnectable={false} proOptions={{ hideAttribution: true }}>
      <Background gap={22} size={1} /><Controls showInteractive={false} />
    </ReactFlow>
  </div>
}
