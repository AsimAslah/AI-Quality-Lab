export function ScoreRing({ score, size = 'large' }: { score: number; size?: 'small' | 'large' }) {
  const bounded = Math.max(0, Math.min(100, score))
  return <div className={`score-ring score-${size}`} style={{ '--score': `${bounded * 3.6}deg` } as React.CSSProperties}>
    <div><strong>{score.toFixed(1)}</strong><span>/100</span></div>
  </div>
}
