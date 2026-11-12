import { beforeEach, describe, expect, it } from 'vitest'
import { getWorkspaceKey, importWorkspaceKey } from './workspace'

describe('workspace access keys', () => {
  beforeEach(() => localStorage.clear())

  it('keeps using the server cookie until a shared key is imported', () => {
    expect(getWorkspaceKey()).toBeNull()
  })

  it('imports an existing key for another authorized device', () => {
    const shared = 'aql_shared_workspace_key_12345678901234567890'
    importWorkspaceKey(shared)
    expect(getWorkspaceKey()).toBe(shared)
  })

  it('rejects malformed access keys', () => {
    expect(() => importWorkspaceKey('short')).toThrow(/valid/i)
  })

  it('discards malformed stored values instead of sending them', () => {
    localStorage.setItem('aql-workspace-key', 'broken')
    expect(getWorkspaceKey()).toBeNull()
    expect(localStorage.getItem('aql-workspace-key')).toBeNull()
  })
})
