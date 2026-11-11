import { beforeEach, describe, expect, it } from 'vitest'
import { getWorkspaceKey, importWorkspaceKey } from './workspace'

describe('workspace access keys', () => {
  beforeEach(() => localStorage.clear())

  it('creates and persists a valid key', () => {
    const first = getWorkspaceKey()
    expect(first.length).toBeGreaterThan(24)
    expect(getWorkspaceKey()).toBe(first)
  })

  it('imports an existing key for another authorized device', () => {
    const shared = 'aql_shared_workspace_key_12345678901234567890'
    importWorkspaceKey(shared)
    expect(getWorkspaceKey()).toBe(shared)
  })

  it('rejects malformed access keys', () => {
    expect(() => importWorkspaceKey('short')).toThrow(/valid/i)
  })
})
