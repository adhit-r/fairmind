'use client'

import '@/astryx/pages/settings.css'
import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Banner } from '@astryxdesign/core/Banner'
import { Button } from '@astryxdesign/core/Button'
import { Dialog, DialogHeader } from '@astryxdesign/core/Dialog'
import { EmptyState } from '@astryxdesign/core/EmptyState'
import { HStack, VStack } from '@astryxdesign/core/Layout'
import { MetadataList, MetadataListItem } from '@astryxdesign/core/MetadataList'
import { Selector } from '@astryxdesign/core/Selector'
import { Skeleton } from '@astryxdesign/core/Skeleton'
import { Table, pixel, proportional } from '@astryxdesign/core/Table'
import type { TableColumn } from '@astryxdesign/core/Table'
import { Heading, Text } from '@astryxdesign/core/Text'
import { TextInput } from '@astryxdesign/core/TextInput'
import { Token } from '@astryxdesign/core/Token'
import { List, ListItem } from '@astryxdesign/core/List'

import { useOrg } from '@/context/OrgContext'
import { useSession } from '@/context/SessionContext'
import { useIntegrations } from '@/lib/api/hooks/useIntegrations'
import { AIProviderSettings } from '@/components/packs/AIProviderSettings'
import { PlatformConnectionSettings } from '@/components/packs/PlatformConnectionSettings'
import {
  PAGE_SIZE,
  changeMemberRole,
  createApiKey,
  deleteApiKey,
  inviteMember,
  removeMember,
  useApiKeys,
  useMembers,
  useOrgAuditLog,
  usePendingAccessRequests,
  useRoles,
  type ApiKeyRow,
  type AuditEntry,
  type OrgMember,
} from '@/astryx/data/settings'

const SECTIONS = [
  { id: 'organisation', label: 'Organisation' },
  { id: 'ai-provider', label: 'AI provider' },
  { id: 'connections', label: 'Connections' },
  { id: 'team', label: 'Team and roles' },
  { id: 'developers', label: 'Developers' },
  { id: 'audit-log', label: 'Audit log' },
  // Shown to platform admins only: approving a request creates a new organisation.
  { id: 'access-requests', label: 'Access requests' },
] as const
type SectionId = (typeof SECTIONS)[number]['id']

const day = (ts: string | null) => {
  if (!ts) return ''
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="fm-page"><Skeleton height={200} /></div>}>
      <Settings />
    </Suspense>
  )
}

function Settings() {
  const requested = useSearchParams().get('section')
  const platformAdmin = useSession().user?.role === 'admin'
  const sections = SECTIONS.filter((s) => s.id !== 'access-requests' || platformAdmin)
  const [active, setActive] = useState<SectionId>(SECTIONS.find((s) => s.id === requested)?.id ?? 'organisation')
  const title = sections.find((s) => s.id === active)?.label

  return (
    <div className="fm-page">
      <VStack gap={5}>
        <Heading level={1}>Settings</Heading>
        <div className="fm-st">
          <nav className="fm-st-nav" aria-label="Settings sections">
            <List density="spacious">
              {sections.map((s) => (
                <ListItem key={s.id} label={s.label} isSelected={active === s.id} onClick={() => setActive(s.id)} />
              ))}
            </List>
          </nav>
          <div className="fm-st-body">
            <VStack gap={4}>
              <Heading level={2}>{title}</Heading>
              {active === 'organisation' && <OrganisationSection />}
              {active === 'ai-provider' && (
                <>
                  <Text color="secondary">FairMind uses your organisation&apos;s own model key for Ask FairMind, the plan and agent steps.</Text>
                  <div className="fm-st-embed"><AIProviderSettings /></div>
                </>
              )}
              {active === 'connections' && <ConnectionsSection />}
              {active === 'team' && <TeamSection />}
              {active === 'developers' && <DevelopersSection />}
              {active === 'audit-log' && <AuditSection />}
              {active === 'access-requests' && platformAdmin && <AccessRequestsSection />}
            </VStack>
          </div>
        </div>
      </VStack>
    </div>
  )
}

function AccessRequestsSection() {
  const pending = usePendingAccessRequests(true)
  if (pending.loading) return <Skeleton height={80} />
  if (pending.error) return <Problem message={pending.error} retry={pending.reload} />
  const n = pending.data.length
  return (
    <VStack gap={3}>
      <Text color="secondary">
        {n === 0
          ? 'No requests are waiting. New requests also arrive by email.'
          : `${n} ${n === 1 ? 'request is' : 'requests are'} waiting. Approving one creates the organisation and emails the requester a link to choose a password.`}
      </Text>
      <HStack><Button label="Review access requests" variant={n ? 'primary' : 'secondary'} href="/admin/registrations" /></HStack>
    </VStack>
  )
}

function Problem({ message, retry }: { message: string; retry?: () => void }) {
  return <EmptyState title="This could not load" description={message} actions={retry ? <Button label="Try again" onClick={retry} /> : undefined} isCompact />
}

function OrganisationSection() {
  const { selectedOrg, isLoading, error } = useOrg()
  if (isLoading) return <Skeleton height={120} />
  if (error || !selectedOrg) return <Problem message={error ?? 'No organisation is selected.'} />
  return (
    <VStack gap={4}>
      <MetadataList columns="multi" orientation="vertical" label={{ position: 'top' }}>
        <MetadataListItem label="Name">{selectedOrg.name}</MetadataListItem>
        <MetadataListItem label="Your role">{selectedOrg.role}</MetadataListItem>
        {selectedOrg.domain && <MetadataListItem label="Domain">{selectedOrg.domain}</MetadataListItem>}
        <MetadataListItem label="Created">{day(selectedOrg.created_at)}</MetadataListItem>
      </MetadataList>
      <Banner status="info" title="Read-only for now" description="There is no way to rename an organisation or change its settings from the app yet." />
    </VStack>
  )
}

function ConnectionsSection() {
  const { integrations, loading, error, refresh } = useIntegrations()
  return (
    <VStack gap={5}>
      <VStack gap={2}>
        <Heading level={3}>Where FairMind looks for AI systems</Heading>
        {loading ? (
          <Skeleton height={60} />
        ) : error ? (
          <Problem message={error} retry={() => void refresh()} />
        ) : integrations.length === 0 ? (
          <Text color="secondary">No source is connected yet.</Text>
        ) : (
          <VStack gap={1}>
            {integrations.map((i) => (
              <HStack key={i.id} gap={2} vAlign="center" wrap="wrap">
                <Text weight="semibold">{i.name}</Text>
                <Token size="sm" label={i.kind} />
                <Text color="secondary" size="sm">{i.lastSyncedAt ? `Last sync ${day(i.lastSyncedAt)}` : 'Not synced yet'}</Text>
              </HStack>
            ))}
          </VStack>
        )}
        <HStack><Button label="Manage in Discovery" variant="secondary" href="/discovery" /></HStack>
      </VStack>
      <VStack gap={2}>
        <Heading level={3}>Claude Managed Agents</Heading>
        <Text color="secondary">The connection that feeds agent audits.</Text>
        <div className="fm-st-embed"><PlatformConnectionSettings /></div>
      </VStack>
    </VStack>
  )
}

type MemberRow = OrgMember & Record<string, unknown>

function TeamSection() {
  const { selectedOrg } = useOrg()
  const orgId = selectedOrg?.id
  const members = useMembers(orgId)
  const roles = useRoles(orgId)
  const [inviting, setInviting] = useState(false)
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const [confirming, setConfirming] = useState<string | null>(null)

  const roleOptions = roles.data.map((r) => ({ value: r.name, label: r.name }))
  const inviteRole = role || roleOptions.find((o) => o.value === 'analyst')?.value || roleOptions[0]?.value || ''

  async function run(key: string, call: () => Promise<{ success: boolean; error?: string; message?: string }>, after?: () => void) {
    setBusy(key)
    setFailure(null)
    const res = await call()
    setBusy(null)
    if (res.success) {
      after?.()
      members.reload()
    } else setFailure(res.error || res.message || 'That did not work')
  }

  const columns: TableColumn<MemberRow>[] = [
    {
      key: 'person',
      header: 'Person',
      width: proportional(3),
      renderCell: (m) => (
        <VStack gap={0}>
          <Text maxLines={1}>{m.name || m.email || m.user_id}</Text>
          {m.name && m.email && <Text color="secondary" size="sm" maxLines={1}>{m.email}</Text>}
        </VStack>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      width: pixel(200),
      renderCell: (m) => (
        <Selector
          label={`Role for ${m.name || m.email || 'member'}`}
          isLabelHidden
          size="sm"
          value={m.role}
          options={roleOptions.some((o) => o.value === m.role) ? roleOptions : [...roleOptions, { value: m.role, label: m.role }]}
          onChange={(v: string) => void run(`role-${m.id}`, () => changeMemberRole(orgId!, m.id, v))}
        />
      ),
    },
    { key: 'status', header: 'Status', width: pixel(100), renderCell: (m) => <Token size="sm" color={m.status === 'active' ? 'green' : 'gray'} label={m.status} /> },
    {
      key: 'remove',
      header: '',
      width: pixel(150),
      renderCell: (m) =>
        confirming === m.id ? (
          <Button label="Confirm remove" size="sm" variant="destructive" isLoading={busy === `rm-${m.id}`} onClick={() => void run(`rm-${m.id}`, () => removeMember(orgId!, m.id), () => setConfirming(null))} />
        ) : (
          <Button label="Remove" size="sm" variant="ghost" onClick={() => setConfirming(m.id)} />
        ),
    },
  ]

  if (!orgId) return <Problem message="No organisation is selected." />
  return (
    <VStack gap={5}>
      {failure && <Banner status="error" title={failure} isDismissable onDismiss={() => setFailure(null)} />}
      <VStack gap={2}>
        <HStack hAlign="between" vAlign="center">
          <Heading level={3}>People</Heading>
          <Button label="Invite a person" variant="secondary" onClick={() => setInviting(true)} />
        </HStack>
        {members.loading ? (
          <Skeleton height={120} />
        ) : members.error ? (
          <Problem message={members.error} retry={members.reload} />
        ) : members.data.length === 0 ? (
          <Text color="secondary">No members yet.</Text>
        ) : (
          <Table<MemberRow> data={members.data as MemberRow[]} columns={columns} idKey="id" density="balanced" />
        )}
      </VStack>
      <VStack gap={2}>
        <Heading level={3}>Roles</Heading>
        {roles.loading ? (
          <Skeleton height={80} />
        ) : roles.error ? (
          <Problem message={roles.error} retry={roles.reload} />
        ) : roles.data.length === 0 ? (
          <Text color="secondary">No custom roles. Members use the built-in owner, admin and member roles.</Text>
        ) : (
          <ul className="fm-st-roles">
            {roles.data.map((r) => (
              <li key={r.id}>
                <HStack gap={2} vAlign="center">
                  <Text weight="semibold">{r.name}</Text>
                  {r.is_system_role && <Token size="sm" label="Built in" />}
                  <Text color="secondary" size="sm">{r.permissions.length} permission{r.permissions.length === 1 ? '' : 's'}</Text>
                </HStack>
                {r.description && <Text color="secondary" size="sm">{r.description}</Text>}
              </li>
            ))}
          </ul>
        )}
      </VStack>

      <Dialog isOpen={inviting} onOpenChange={setInviting} width={460}>
        <DialogHeader title="Invite a person" onOpenChange={setInviting} />
        <div className="fm-st-pad">
          <VStack gap={4}>
            <TextInput label="Email" type="email" value={email} onChange={setEmail} />
            <Selector label="Role" value={inviteRole} onChange={setRole} options={roleOptions} />
            <HStack gap={2} hAlign="end">
              <Button label="Cancel" variant="ghost" onClick={() => setInviting(false)} />
              <Button
                label="Send invitation"
                variant="primary"
                isDisabled={!email.includes('@') || !inviteRole}
                isLoading={busy === 'invite'}
                onClick={() => void run('invite', () => inviteMember(orgId, email.trim(), inviteRole), () => { setInviting(false); setEmail('') })}
              />
            </HStack>
          </VStack>
        </div>
      </Dialog>
    </VStack>
  )
}

type KeyRow = ApiKeyRow & Record<string, unknown>

function DevelopersSection() {
  const keys = useApiKeys()
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [failure, setFailure] = useState<string | null>(null)
  const [created, setCreated] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [confirming, setConfirming] = useState<string | null>(null)

  async function create() {
    setBusy('create')
    setFailure(null)
    const res = await createApiKey(name.trim(), description.trim())
    setBusy(null)
    if (res.success && res.data) {
      setCreating(false)
      setName('')
      setDescription('')
      setCopied(false)
      setCreated(res.data.api_key)
      keys.reload()
    } else setFailure(res.error || res.message || 'The key could not be made')
  }

  async function revoke(keyName: string) {
    setBusy(`del-${keyName}`)
    setFailure(null)
    const res = await deleteApiKey(keyName)
    setBusy(null)
    setConfirming(null)
    if (res.success) keys.reload()
    else setFailure(res.error || res.message || 'The key could not be deleted')
  }

  const columns: TableColumn<KeyRow>[] = [
    {
      key: 'name',
      header: 'Key',
      width: proportional(3),
      renderCell: (k) => (
        <VStack gap={0}>
          <Text maxLines={1}>{k.name}</Text>
          {k.description && <Text color="secondary" size="sm" maxLines={1}>{k.description}</Text>}
        </VStack>
      ),
    },
    { key: 'created', header: 'Created', width: pixel(170), renderCell: (k) => <Text color="secondary" hasTabularNumbers>{day(k.created_at)}</Text> },
    { key: 'expires', header: 'Expires', width: pixel(170), renderCell: (k) => <Text color="secondary" hasTabularNumbers>{day(k.expires_at)}</Text> },
    {
      key: 'delete',
      header: '',
      width: pixel(150),
      renderCell: (k) =>
        confirming === k.name ? (
          <Button label="Confirm delete" size="sm" variant="destructive" isLoading={busy === `del-${k.name}`} onClick={() => void revoke(k.name)} />
        ) : (
          <Button label="Delete" size="sm" variant="ghost" onClick={() => setConfirming(k.name)} />
        ),
    },
  ]

  return (
    <VStack gap={4}>
      <Text color="secondary">API keys are yours, not the organisation&apos;s. Use one in CI or the FairMind CLI.</Text>
      {failure && !creating && <Banner status="error" title={failure} isDismissable onDismiss={() => setFailure(null)} />}
      <HStack><Button label="Create a key" variant="secondary" onClick={() => setCreating(true)} /></HStack>
      {keys.loading ? (
        <Skeleton height={100} />
      ) : keys.error ? (
        <Problem message={keys.error} retry={keys.reload} />
      ) : keys.data.length === 0 ? (
        <Text color="secondary">You have no API keys.</Text>
      ) : (
        <Table<KeyRow> data={keys.data as KeyRow[]} columns={columns} idKey="name" density="balanced" />
      )}

      <Dialog isOpen={creating} onOpenChange={setCreating} width={460}>
        <DialogHeader title="Create an API key" onOpenChange={setCreating} />
        <div className="fm-st-pad">
          <VStack gap={4}>
            <TextInput label="Name" value={name} onChange={setName} />
            <TextInput label="Description" isOptional value={description} onChange={setDescription} />
            {failure && <Banner status="error" title={failure} />}
            <HStack gap={2} hAlign="end">
              <Button label="Cancel" variant="ghost" onClick={() => setCreating(false)} />
              <Button label="Create key" variant="primary" isDisabled={!name.trim()} isLoading={busy === 'create'} onClick={() => void create()} />
            </HStack>
          </VStack>
        </div>
      </Dialog>

      <Dialog isOpen={created !== null} onOpenChange={(o) => !o && setCreated(null)} width={520}>
        <DialogHeader title="Your new key" onOpenChange={() => setCreated(null)} />
        <div className="fm-st-pad">
          <VStack gap={3}>
            <Banner status="warning" title="Copy this key now" description="It is shown once and cannot be read again." />
            <span className="fm-st-key">{created}</span>
            <HStack gap={2} hAlign="end">
              <Button label="Close" variant="ghost" onClick={() => setCreated(null)} />
              <Button label={copied ? 'Copied' : 'Copy key'} variant="primary" onClick={() => void navigator.clipboard.writeText(created ?? '').then(() => setCopied(true))} />
            </HStack>
          </VStack>
        </div>
      </Dialog>
    </VStack>
  )
}

type AuditRow = AuditEntry & Record<string, unknown>

function AuditSection() {
  const { selectedOrg } = useOrg()
  const [page, setPage] = useState(0)
  const log = useOrgAuditLog(selectedOrg?.id, page)
  const last = Math.max(0, Math.ceil(log.data.total / PAGE_SIZE) - 1)

  const columns: TableColumn<AuditRow>[] = [
    { key: 'when', header: 'When', width: pixel(170), renderCell: (e) => <Text color="secondary" hasTabularNumbers>{day(e.created_at)}</Text> },
    { key: 'action', header: 'Action', width: pixel(140), renderCell: (e) => <Text>{e.action}</Text> },
    {
      key: 'resource',
      header: 'Resource',
      width: proportional(2),
      renderCell: (e) => <Text maxLines={1}>{e.resource_type}{e.resource_id ? ` ${e.resource_id.slice(0, 8)}` : ''}</Text>,
    },
    { key: 'who', header: 'By', width: proportional(2), renderCell: (e) => <Text color="secondary" maxLines={1}>{e.user_id}</Text> },
    {
      key: 'result',
      header: 'Result',
      width: pixel(110),
      renderCell: (e) => <Token size="sm" color={e.status === 'success' ? 'green' : 'red'} label={e.status === 'success' ? 'Done' : 'Failed'} />,
    },
  ]

  if (!selectedOrg) return <Problem message="No organisation is selected." />
  if (log.loading && log.data.logs.length === 0) return <Skeleton height={200} />
  if (log.error) return <Problem message={log.error} retry={log.reload} />
  if (log.data.logs.length === 0) return <Text color="secondary">Nothing has been logged for this organisation yet.</Text>
  return (
    <VStack gap={3}>
      <Table<AuditRow> data={log.data.logs as AuditRow[]} columns={columns} idKey="id" density="balanced" textOverflow="truncate" />
      <HStack gap={3} vAlign="center" hAlign="between">
        <Text color="secondary" size="sm">Page {page + 1} of {last + 1}, {log.data.total} entries</Text>
        <HStack gap={2}>
          <Button label="Newer" size="sm" variant="secondary" isDisabled={page === 0} onClick={() => setPage(page - 1)} />
          <Button label="Older" size="sm" variant="secondary" isDisabled={page >= last} onClick={() => setPage(page + 1)} />
        </HStack>
      </HStack>
    </VStack>
  )
}
