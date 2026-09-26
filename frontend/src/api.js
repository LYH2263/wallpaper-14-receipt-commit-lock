async function ensureOk(r) {
  if (r.ok) return
  const text = await r.text()
  let msg = text
  try { msg = JSON.parse(text).detail ?? text } catch { /* keep raw text */ }
  throw new Error(msg)
}
export async function getJSON(path) {
  const r = await fetch(path)
  await ensureOk(r)
  return r.json()
}
export async function postJSON(path, body) {
  const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  await ensureOk(r)
  return r.json()
}
