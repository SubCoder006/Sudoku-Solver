import { useEffect, useState } from 'react'
import { solve, validate, compare } from './api'
import { usePlayback } from './usePlayback'
import Board from './Board'
import Compare from './Compare'
import './App.css'

const NO_STEPS = [] // stable reference, so the hook doesn't reset on every render
const blank = () => Array.from({ length: 9 }, () => Array(9).fill(0))
const SAMPLE = [
  [5,3,0,0,7,0,0,0,0],[6,0,0,1,9,5,0,0,0],[0,9,8,0,0,0,0,6,0],
  [8,0,0,0,6,0,0,0,3],[4,0,0,8,0,3,0,0,1],[7,0,0,0,2,0,0,0,6],
  [0,6,0,0,0,0,2,8,0],[0,0,0,4,1,9,0,0,5],[0,0,0,0,8,0,0,7,9],
]

export default function App() {
  const [givens, setGivens] = useState(blank)
  const [mode, setMode] = useState('edit') // 'edit' | 'play'
  const [strategy, setStrategy] = useState('mrv')
  const [result, setResult] = useState(null)
  const [selected, setSelected] = useState(0)
  const [conflicts, setConflicts] = useState(new Set())
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [cmp, setCmp] = useState(null)

  const steps = result?.steps ?? NO_STEPS
  const pb = usePlayback(givens, steps, true) // true = auto-play
  const editing = mode === 'edit'
  const cells = editing ? givens.flat() : pb.board
  const done = !editing && pb.index === pb.total && pb.total > 0

  // Live conflict check while editing
  useEffect(() => {
    if (!editing) return
    let cancelled = false
    validate(givens)
      .then((r) => !cancelled && setConflicts(new Set(r.conflicts.map(([r, c]) => r * 9 + c))))
      .catch(() => {})
    return () => { cancelled = true }
  }, [givens, editing])

  // Clear stale comparison results when the grid changes
  useEffect(() => { setCmp(null) }, [givens])

  // Keyboard input
  useEffect(() => {
    if (!editing) return
    const onKey = (e) => {
      const r = Math.floor(selected / 9), c = selected % 9
      if (/^[0-9]$/.test(e.key)) setCell(r, c, Number(e.key))
      else if (e.key === 'Backspace' || e.key === 'Delete') setCell(r, c, 0)
      else if (e.key === 'ArrowLeft') setSelected(r * 9 + Math.max(0, c - 1))
      else if (e.key === 'ArrowRight') setSelected(r * 9 + Math.min(8, c + 1))
      else if (e.key === 'ArrowUp') setSelected(Math.max(0, r - 1) * 9 + c)
      else if (e.key === 'ArrowDown') setSelected(Math.min(8, r + 1) * 9 + c)
      else return
      e.preventDefault()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  function setCell(r, c, v) {
    setGivens((g) => g.map((row, i) => (i === r ? row.map((x, j) => (j === c ? v : x)) : row)))
  }

  async function onSolve() {
    setBusy(true)
    setError('')
    try {
      const r = await solve(givens, strategy)
      if (!r.solvable) {
        return setError(
          r.aborted
            ? 'Gave up: this puzzle exceeded the step limit.'
            : 'This puzzle has no solution.'
        )
      }
      setResult(r)
      setMode('play')
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  async function onCompare() {
    setBusy(true)
    setError('')
    try {
      const r = await compare(givens)
      setCmp(r.results)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  function backToEdit() {
    setResult(null)
    setMode('edit')
  }

  return (
    <div className="app">
      <h1>Sudoku Solver</h1>
      <div className="layout">
        <Board
          cells={cells}
          givens={givens}
          selected={editing ? selected : -1}
          onSelect={editing ? setSelected : undefined}
          conflicts={editing ? conflicts : new Set()}
          lastStep={editing ? null : pb.lastStep}
          done={done}
        />

        <div className="panel">
          {editing ? (
            <>
              <label>
                Strategy{' '}
                <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
                  <option value="mrv">MRV (smart)</option>
                  <option value="naive">Naive (row by row)</option>
                </select>
              </label>
              <button onClick={onSolve} disabled={busy || conflicts.size > 0}>
                {busy ? 'Solving…' : 'Solve'}
              </button>
              <button onClick={onCompare} disabled={busy || conflicts.size > 0}>
                Compare strategies
              </button>
              <button onClick={() => setGivens(SAMPLE)}>Load sample</button>
              <button onClick={() => setGivens(blank())}>Clear</button>
              <p className="hint">Click a cell, type 1-9, arrows to move, Backspace to clear.</p>
              {cmp && <Compare rows={cmp} />}
            </>
          ) : (
            <>
              <div className="row">
                <button onClick={() => pb.seek(0)}>⏮</button>
                <button onClick={() => pb.seek(pb.index - 1)}>◀</button>
                <button onClick={() => pb.setPlaying(!pb.playing)}>
                  {pb.playing ? 'Pause' : 'Play'}
                </button>
                <button onClick={() => pb.seek(pb.index + 1)}>▶</button>
                <button onClick={() => pb.seek(pb.total)}>⏭</button>
              </div>
              <input
                type="range" min="0" max={pb.total} value={pb.index}
                onChange={(e) => pb.seek(Number(e.target.value))}
              />
              <label>
                Speed: {pb.speed} steps/s
                <input
                  type="range" min="10" max="5000" step="10" value={pb.speed}
                  onChange={(e) => pb.setSpeed(Number(e.target.value))}
                />
              </label>
              <div className="stats">
                <div>Step {pb.index.toLocaleString()} / {pb.total.toLocaleString()}</div>
                <div>Backtracks: {result.backtracks.toLocaleString()}</div>
                <div>Solved in {result.elapsed_ms.toFixed(1)} ms</div>
                {result.truncated && (
                  <div>Animation capped; full solve took {result.total_steps.toLocaleString()} steps</div>
                )}
              </div>
              <button onClick={backToEdit}>Edit puzzle</button>
            </>
          )}
          {error && <p className="error">{error}</p>}
        </div>
      </div>
    </div>
  )
}