/** Parse CSV text into a header and rows; numeric-looking cells become numbers. Handles quoted fields. */
export function parseCsv(text: string, maxRows = 5000): { header: string[]; rows: Record<string, string | number>[]; truncated: boolean } {
  const records: string[][] = []
  let field = ''
  let record: string[] = []
  let quoted = false
  for (let i = 0; i < text.length; i++) {
    const c = text[i]
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++ }
      else if (c === '"') quoted = false
      else field += c
    } else if (c === '"') quoted = true
    else if (c === ',') { record.push(field); field = '' }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++
      record.push(field); field = ''
      if (record.some((v) => v !== '')) records.push(record)
      record = []
    } else field += c
  }
  if (field !== '' || record.length) { record.push(field); if (record.some((v) => v !== '')) records.push(record) }
  const header = (records.shift() ?? []).map((h) => h.trim())
  const truncated = records.length > maxRows
  const rows = records.slice(0, maxRows).map((r) =>
    Object.fromEntries(header.map((h, i) => {
      const raw = (r[i] ?? '').trim()
      return [h, raw !== '' && !Number.isNaN(Number(raw)) ? Number(raw) : raw]
    }))
  )
  return { header, rows, truncated }
}
