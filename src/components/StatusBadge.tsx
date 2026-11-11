import { Check, Circle, Clock3, RotateCcw, SkipForward, TriangleAlert, X } from 'lucide-react'

const icons = { pending: Circle, queued: Clock3, running: Clock3, completed: Check, completed_with_warnings: TriangleAlert, failed: X, retrying: RotateCcw, recovered: Check, skipped: SkipForward }

export function StatusBadge({ status }: { status: string }) {
  const Icon = icons[status as keyof typeof icons] ?? Circle
  return <span className={`status status-${status}`}><Icon size={13} />{status.replaceAll('_', ' ')}</span>
}
