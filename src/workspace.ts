const STORAGE_KEY = 'aql-workspace-key'
const KEY_PATTERN = /^[A-Za-z0-9_-]{24,160}$/

function generateWorkspaceKey(): string {
  return `aql_${crypto.randomUUID().replaceAll('-', '')}_${crypto.randomUUID().replaceAll('-', '')}`
}

export function getWorkspaceKey(): string {
  const existing = localStorage.getItem(STORAGE_KEY)
  if (existing && KEY_PATTERN.test(existing)) return existing
  const created = generateWorkspaceKey()
  localStorage.setItem(STORAGE_KEY, created)
  return created
}

export function importWorkspaceKey(value: string): void {
  const normalized = value.trim()
  if (!KEY_PATTERN.test(normalized)) throw new Error('Enter a valid AI Quality Lab workspace key.')
  localStorage.setItem(STORAGE_KEY, normalized)
}
