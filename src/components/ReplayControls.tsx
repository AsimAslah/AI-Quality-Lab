import { useEffect, useMemo, useRef, useState } from 'react'
import { Pause, Play, RotateCcw } from 'lucide-react'
import type { ExecutionEvent } from '../types'

export function useReplay(events: ExecutionEvent[]) {
  const ordered = useMemo(() => [...events].sort((a, b) => a.sequence - b.sequence), [events])
  const [index, setIndex] = useState(ordered.length)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const timer = useRef<number | undefined>(undefined)
  useEffect(() => {
    if (!playing || index >= ordered.length) { if (index >= ordered.length) setPlaying(false); return }
    const current = ordered[index]
    const previous = ordered[index - 1]
    const actualGap = previous ? new Date(current.occurred_at).getTime() - new Date(previous.occurred_at).getTime() : 0
    const visibleGap = Math.max(180, Math.min(1200, actualGap || 260)) / speed
    timer.current = window.setTimeout(() => setIndex(i => i + 1), visibleGap)
    return () => window.clearTimeout(timer.current)
  }, [playing, index, ordered, speed])
  const restart = () => { setIndex(0); setPlaying(true) }
  return { visible: ordered.slice(0, index), index, playing, speed, setPlaying, setSpeed, restart, total: ordered.length }
}

export function ReplayControls({ replay }: { replay: ReturnType<typeof useReplay> }) {
  return <div className="replay-controls">
    <button className="button button-secondary" onClick={replay.restart}><RotateCcw size={16} />Restart</button>
    <button className="button button-primary" onClick={() => replay.setPlaying(!replay.playing)} disabled={replay.total === 0}>
      {replay.playing ? <Pause size={16} /> : <Play size={16} />}{replay.playing ? 'Pause' : 'Play'}
    </button>
    <label>Speed <select value={replay.speed} onChange={e => replay.setSpeed(Number(e.target.value))}><option value="0.5">0.5×</option><option value="1">1×</option><option value="2">2×</option><option value="4">4×</option></select></label>
    <span>{replay.index} / {replay.total} events</span>
  </div>
}
