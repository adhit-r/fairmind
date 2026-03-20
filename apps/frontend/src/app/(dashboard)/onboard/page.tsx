'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import {
  IconArrowRight,
  IconBuildingSkyscraper,
  IconChecklist,
  IconDatabase,
  IconFileCheck,
  IconRobot,
  IconSettings,
  IconUsers,
} from '@tabler/icons-react'

import { useSystemContext } from '@/components/workflow/SystemContext'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useToast } from '@/hooks/use-toast'
import { useDatasets } from '@/lib/api/hooks/useDatasets'
import { useModels } from '@/lib/api/hooks/useModels'

function formatCountLabel(count: number, singular: string, plural: string) {
  return `${count} ${count === 1 ? singular : plural}`
}

export default function OnboardPage() {
  const { selectedSystem, systems, loading: systemsLoading, createWorkspaceAndSystem } = useSystemContext()
  const { data: models, loading: modelsLoading } = useModels()
  const { datasets, loading: datasetsLoading } = useDatasets()
  const { toast } = useToast()
  const [workspaceName, setWorkspaceName] = useState('Acme Workspace')
  const [workspaceOwner, setWorkspaceOwner] = useState('owner@acme.ai')
  const [systemName, setSystemName] = useState('Acme New AI System')
  const [systemOwner, setSystemOwner] = useState('ml-owner@acme.ai')
  const [creating, setCreating] = useState(false)

  const loading = modelsLoading || datasetsLoading || systemsLoading

  const onboardingState = useMemo(() => {
    const hasModel = models.length > 0
    const hasDataset = datasets.length > 0
    const readyForAssess = hasModel && hasDataset
    const checklist = [
      {
        title: 'Workspace scope defined',
        description: `Current owner is ${selectedSystem.owner}. Confirm workspace settings, ownership, and invite list.`,
        done: Boolean(selectedSystem.owner),
        href: '/settings',
      },
      {
        title: 'Model asset available',
        description: hasModel
          ? `${formatCountLabel(models.length, 'model is', 'models are')} available for assessment.`
          : 'No model assets are currently available in the workspace.',
        done: hasModel,
        href: '/bias',
      },
      {
        title: 'Representative dataset available',
        description: hasDataset
          ? `${formatCountLabel(datasets.length, 'dataset is', 'datasets are')} available for evaluation.`
          : 'No datasets are currently available for the selected AI system.',
        done: hasDataset,
        href: '/bias',
      },
      {
        title: 'First assessment path selected',
        description: readyForAssess
          ? 'The system can move into fairness and governance evaluation now.'
          : 'Assessment should wait until both the model and dataset are ready.',
        done: readyForAssess,
        href: readyForAssess ? '/bias' : '/settings',
      },
    ]

    return {
      readyForAssess,
      checklist,
      readinessScore: checklist.filter((item) => item.done).length * 25,
    }
  }, [datasets.length, models.length, selectedSystem.owner])

  const handleCreateSystem = async () => {
    try {
      setCreating(true)
      const created = await createWorkspaceAndSystem({
        workspaceName,
        workspaceOwner,
        systemName,
        systemOwner,
        riskTier: 'medium',
        stage: 'onboard',
      })
      toast({
        title: 'AI system created',
        description: `${created.name} is now the selected system for onboarding.`,
      })
    } catch (error) {
      toast({
        title: 'Creation failed',
        description: error instanceof Error ? error.message : 'Could not create workspace and AI system.',
        variant: 'destructive',
      })
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden border-4 border-black bg-[linear-gradient(135deg,#fff4de_0%,#fff 55%,#e9f7f0_100%)] shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <div className="grid gap-0 xl:grid-cols-[1.15fr_0.85fr]">
          <div className="border-b-4 border-black p-6 xl:border-b-0 xl:border-r-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-2 border-black bg-black px-3 py-1 font-black uppercase text-white">
                <IconBuildingSkyscraper className="mr-2 h-4 w-4" />
                Entry flow
              </Badge>
              <Badge variant="outline" className="border-2 border-black bg-white px-3 py-1 font-bold uppercase">
                {selectedSystem.name}
              </Badge>
            </div>

            <h1 className="mt-4 text-4xl font-black uppercase tracking-tight text-balance">
              Onboard the AI system before you assess or approve it
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-700">
              This page defines the start of the FairMind workflow. Confirm ownership, make sure a
              model and representative dataset are available, and then move into the first
              assessment path without guessing where to start.
            </p>

            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Lifecycle stage</p>
                <p className="mt-2 text-3xl font-black uppercase">{selectedSystem.stage}</p>
              </div>
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Onboard readiness</p>
                <p className="mt-2 text-3xl font-black">{onboardingState.readinessScore}%</p>
              </div>
              <div className="border-2 border-black bg-white p-4 shadow-[4px_4px_0px_0px_#000]">
                <p className="text-xs font-bold uppercase text-muted-foreground">Risk tier</p>
                <p className="mt-2 text-3xl font-black uppercase">{selectedSystem.riskTier}</p>
              </div>
            </div>
          </div>

          <div className="bg-black p-6 text-white">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-orange">Onboard sequence</p>
            <div className="mt-4 space-y-3">
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">1. Confirm ownership</p>
                <p className="mt-1 text-sm text-slate-200">
                  Know who owns the AI system, who reviews it, and which workspace it belongs to.
                </p>
              </div>
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">2. Verify assets</p>
                <p className="mt-1 text-sm text-slate-200">
                  Make sure the model artifact and production-like dataset are available.
                </p>
              </div>
              <div className="border-2 border-white p-4">
                <p className="font-black uppercase">3. Start assessment</p>
                <p className="mt-1 text-sm text-slate-200">
                  Move directly into fairness, compliance, and governance evaluation.
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Owner</p>
          <p className="mt-2 text-lg font-black">{selectedSystem.owner}</p>
        </Card>
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Models</p>
          <p className="mt-2 text-3xl font-black">{loading ? '—' : models.length}</p>
        </Card>
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Datasets</p>
          <p className="mt-2 text-3xl font-black">{loading ? '—' : datasets.length}</p>
        </Card>
        <Card className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Next stage</p>
          <p className="mt-2 text-3xl font-black uppercase">{onboardingState.readyForAssess ? 'Assess' : 'Setup'}</p>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card className="border-2 border-black p-6 shadow-brutal">
          <h2 className="text-2xl font-black uppercase">Onboarding Checklist</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            This checklist should be completed before governance work starts for the selected AI system.
          </p>

          <div className="mt-6 space-y-4">
            {onboardingState.checklist.map((item) => (
              <div key={item.title} className="rounded-2xl border-2 border-black bg-white p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    {item.done ? (
                      <IconFileCheck className="mt-0.5 h-5 w-5 text-emerald-600" />
                    ) : (
                      <IconChecklist className="mt-0.5 h-5 w-5 text-orange-600" />
                    )}
                    <div>
                      <p className="font-black uppercase">{item.title}</p>
                      <p className="mt-1 text-sm text-slate-700">{item.description}</p>
                    </div>
                  </div>
                  <Button asChild variant="neutral" className="border-2 border-black font-bold">
                    <Link href={item.href}>
                      Open
                      <IconArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="border-2 border-black p-6 shadow-brutal">
          <h2 className="text-2xl font-black uppercase">Start Here</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Use these entry points instead of jumping straight into disconnected pages.
          </p>

          <div className="mt-6 space-y-4">
            <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
              <p className="font-black uppercase">System registry</p>
              <p className="mt-1 text-sm text-slate-700">
                {loading
                  ? 'Loading workspace systems...'
                  : `${formatCountLabel(systems.length, 'AI system is', 'AI systems are')} available in the current backend registry.`}
              </p>
            </div>

            <Link href="/settings" className="block rounded-2xl border-2 border-black bg-slate-50 p-4 transition hover:bg-orange hover:text-black">
              <div className="flex items-center gap-3">
                <IconUsers className="h-5 w-5" />
                <div>
                  <p className="font-black uppercase">Workspace and owners</p>
                  <p className="mt-1 text-sm text-slate-700">
                    Confirm email, owners, notifications, and operational defaults.
                  </p>
                </div>
              </div>
            </Link>

            <Link href="/bias" className="block rounded-2xl border-2 border-black bg-slate-50 p-4 transition hover:bg-orange hover:text-black">
              <div className="flex items-center gap-3">
                <IconRobot className="h-5 w-5" />
                <div>
                  <p className="font-black uppercase">Assess model and dataset</p>
                  <p className="mt-1 text-sm text-slate-700">
                    Use the first assessment route to verify the selected assets are ready.
                  </p>
                </div>
              </div>
            </Link>

            <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
              <div className="flex items-center gap-3">
                <IconDatabase className="h-5 w-5" />
                <div>
                  <p className="font-black uppercase">Asset inventory</p>
                  <p className="mt-1 text-sm text-slate-700">
                    {loading
                      ? 'Loading current workspace assets...'
                      : `${formatCountLabel(models.length, 'model', 'models')} and ${formatCountLabel(datasets.length, 'dataset', 'datasets')} are visible right now.`}
                  </p>
                </div>
              </div>
            </div>

            <Button asChild variant="default" className="w-full">
              <Link href={onboardingState.readyForAssess ? '/bias' : '/settings'}>
                {onboardingState.readyForAssess ? 'Proceed to assessment' : 'Complete workspace setup'}
                <IconArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </Card>
      </div>

      <Card className="border-2 border-black p-6 shadow-brutal">
        <h2 className="text-2xl font-black uppercase">Create backend AI system</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          This writes a real workspace and AI system to the backend registry so the shared scope
          model is no longer demo-only.
        </p>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <p className="text-xs font-bold uppercase text-muted-foreground">Workspace name</p>
            <Input value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} className="border-2 border-black bg-white" />
          </div>
          <div className="space-y-2">
            <p className="text-xs font-bold uppercase text-muted-foreground">Workspace owner</p>
            <Input value={workspaceOwner} onChange={(event) => setWorkspaceOwner(event.target.value)} className="border-2 border-black bg-white" />
          </div>
          <div className="space-y-2">
            <p className="text-xs font-bold uppercase text-muted-foreground">AI system name</p>
            <Input value={systemName} onChange={(event) => setSystemName(event.target.value)} className="border-2 border-black bg-white" />
          </div>
          <div className="space-y-2">
            <p className="text-xs font-bold uppercase text-muted-foreground">AI system owner</p>
            <Input value={systemOwner} onChange={(event) => setSystemOwner(event.target.value)} className="border-2 border-black bg-white" />
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Button type="button" onClick={() => void handleCreateSystem()} disabled={creating} className="border-2 border-black font-black uppercase">
            {creating ? 'Creating...' : 'Create workspace and AI system'}
          </Button>
          <Button asChild variant="neutral" className="border-2 border-black font-bold">
            <Link href="/dashboard">
              Return to dashboard
              <IconArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </Card>

      <Card className="border-2 border-black p-6 shadow-brutal">
        <h2 className="text-2xl font-black uppercase">What onboarding means in FairMind now</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
            <div className="flex items-center gap-3">
              <IconSettings className="h-5 w-5" />
              <p className="font-black uppercase">Scope</p>
            </div>
            <p className="mt-2 text-sm text-slate-700">
              Pick the AI system, confirm ownership, and use one scoped object across the workflow.
            </p>
          </div>
          <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
            <div className="flex items-center gap-3">
              <IconRobot className="h-5 w-5" />
              <p className="font-black uppercase">Assets</p>
            </div>
            <p className="mt-2 text-sm text-slate-700">
              Ensure the model and production-like dataset exist before testing or governance review starts.
            </p>
          </div>
          <div className="rounded-2xl border-2 border-black bg-slate-50 p-4">
            <div className="flex items-center gap-3">
              <IconArrowRight className="h-5 w-5" />
              <p className="font-black uppercase">Handoff</p>
            </div>
            <p className="mt-2 text-sm text-slate-700">
              Route directly into assessment once the checklist is complete instead of browsing modules.
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}
