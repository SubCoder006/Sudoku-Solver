const fmt = (n) => n.toLocaleString()

export default function Compare({ rows }) {
  const [naive, mrv] = rows
  const max = Math.max(...rows.map((r) => r.total_steps), 1)
  const bothDone = !naive.aborted && !mrv.aborted && mrv.total_steps > 0

  return (
    <div className="compare">
      <h3>Naive vs MRV</h3>
      {rows.map((r) => (
        <div key={r.strategy} className="cmp-row">
          <div className="cmp-label">{r.strategy === 'mrv' ? 'MRV' : 'Naive'}</div>
          <div className="cmp-bar-wrap">
            <div
              className={`cmp-bar ${r.strategy}`}
              style={{ width: `${(r.total_steps / max) * 100}%` }}
            />
          </div>
          <div className="cmp-nums">
            {r.aborted ? 'gave up at ' : ''}{fmt(r.total_steps)} steps
            <span> · {fmt(r.backtracks)} backtracks · {r.elapsed_ms.toFixed(1)} ms</span>
          </div>
        </div>
      ))}
      {bothDone && (
        <p className="cmp-summary">
          MRV used {(naive.total_steps / mrv.total_steps).toFixed(1)}× fewer steps
          {mrv.elapsed_ms > 0 && <> and was {(naive.elapsed_ms / mrv.elapsed_ms).toFixed(1)}× faster in wall time</>}.
        </p>
      )}
    </div>
  )
}