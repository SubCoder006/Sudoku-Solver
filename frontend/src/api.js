async function post(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const { detail } = await res.json().catch(() => ({}))
    throw new Error(typeof detail === 'string' ? detail : 'Invalid grid')
  }
  return res.json()
}

export const solve = (grid, strategy) => post('/api/solve', { grid, strategy })
export const validate = (grid) => post('/api/validate', { grid })
export const compare = (grid) => post('/api/compare', { grid })