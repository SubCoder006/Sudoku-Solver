import { useCallback, useEffect, useRef, useState } from 'react'

export function usePlayback(givens, steps) {
  const board = useRef(new Int8Array(81))
  const prev = useRef(new Int8Array(0))
  const pos = useRef(0)
  const acc = useRef(0)
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(200) // steps per second

  // Reset whenever the puzzle or step list changes
  useEffect(() => {
    const start = Int8Array.from(givens.flat())
    board.current = Int8Array.from(start)
    const before = new Int8Array(steps.length)
    const sim = Int8Array.from(start)
    steps.forEach(([r, c, v], i) => {
      const k = r * 9 + c
      before[i] = sim[k]
      sim[k] = v
    })
    prev.current = before
    pos.current = 0
    acc.current = 0
    setIndex(0)
    setPlaying(false)
  }, [givens, steps])

  const seek = useCallback(
    (target) => {
      const t = Math.max(0, Math.min(steps.length, target))
      const b = board.current
      while (pos.current < t) {
        const [r, c, v] = steps[pos.current]
        b[r * 9 + c] = v
        pos.current++
      }
      while (pos.current > t) {
        pos.current--
        const [r, c] = steps[pos.current]
        b[r * 9 + c] = prev.current[pos.current]
      }
      setIndex(t)
    },
    [steps]
  )

  // Animation loop: advance by (speed * elapsed time) steps per frame
  useEffect(() => {
    if (!playing) return
    let raf
    let last = performance.now()
    const tick = (now) => {
      acc.current += ((now - last) * speed) / 1000
      last = now
      const k = Math.floor(acc.current)
      acc.current -= k
      if (k > 0) {
        const target = pos.current + k
        seek(target)
        if (target >= steps.length) {
          setPlaying(false)
          return
        }
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [playing, speed, steps, seek])

  return {
    board: board.current,
    index,
    total: steps.length,
    playing,
    setPlaying,
    speed,
    setSpeed,
    seek,
    lastStep: index > 0 ? steps[index - 1] : null,
  }
}