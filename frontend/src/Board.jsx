export default function Board({ cells, givens, selected, onSelect, conflicts, lastStep, done }) {
  return (
    <div className="board">
      {Array.from(cells).map((v, k) => {
        const r = Math.floor(k / 9)
        const c = k % 9
        const isGiven = givens[r][c] !== 0
        const cls = ['cell']
        if (isGiven) cls.push('given')
        if (k === selected) cls.push('selected')
        if (conflicts.has(k)) cls.push('conflict')
        if (lastStep && lastStep[0] === r && lastStep[1] === c) {
          cls.push(lastStep[3] === 0 ? 'trying' : 'backtracking')
        }
        if (done && !isGiven) cls.push('solved')
        if (c % 3 === 2 && c !== 8) cls.push('box-right')
        if (r % 3 === 2 && r !== 8) cls.push('box-bottom')
        return (
          <div key={k} className={cls.join(' ')} onClick={() => onSelect?.(k)}>
            {v || ''}
          </div>
        )
      })}
    </div>
  )
}
