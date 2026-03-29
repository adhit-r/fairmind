'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import {
  IconArrowLeft,
  IconArrowRight,
  IconBuildingSkyscraper,
  IconCheck,
  IconCircleCheck,
  IconFileCheck,
  IconRobot,
  IconShieldCheck,
} from '@tabler/icons-react'

import { useSystemContext, type AISystemSummary } from '@/components/workflow/SystemContext'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'

// --- Constants ---

const STEPS = [
  { number: 1, label: 'Register system' },
  { number: 2, label: 'Select frameworks' },
  { number: 3, label: 'Bias scan' },
  { number: 4, label: 'Review requirements' },
  { number: 5, label: 'Confirm & enter lifecycle' },
]

const RISK_TIERS: { value: AISystemSummary['riskTier']; label: string; description: string }[] = [
  { value: 'low', label: 'Low', description: 'Minimal societal or business impact' },
  { value: 'medium', label: 'Medium', description: 'Moderate impact — standard governance required' },
  { value: 'high', label: 'High', description: 'Significant impact on individuals or regulated sectors' },
  { value: 'critical', label: 'Critical', description: 'Prohibited-category or high-risk under EU AI Act Art. 6' },
]

const SYSTEM_TYPES = ['Classification', 'Regression', 'Generative AI (LLM)', 'Multimodal', 'Recommendation', 'Computer Vision', 'Other']

const COMPLIANCE_FRAMEWORKS = [
  {
    id: 'eu_ai_act',
    name: 'EU AI Act',
    description: 'Mandatory for high-risk AI systems deployed in the European Union.',
    region: 'EU',
  },
  {
    id: 'gdpr',
    name: 'GDPR',
    description: 'Applies when processing personal data of EU residents.',
    region: 'EU',
  },
  {
    id: 'iso_42001',
    name: 'ISO 42001',
    description: 'International standard for AI management systems.',
    region: 'Global',
  },
  {
    id: 'nist_ai_rmf',
    name: 'NIST AI RMF',
    description: 'Risk management framework for trustworthy AI.',
    region: 'US / Global',
  },
  {
    id: 'dpdp_act',
    name: 'DPDP Act',
    description: 'India Digital Personal Data Protection Act (2023).',
    region: 'India',
  },
]

// Derived evidence requirements per framework
const FRAMEWORK_EVIDENCE: Record<string, string[]> = {
  eu_ai_act: ['Conformity assessment', 'Technical documentation', 'Human oversight procedures'],
  gdpr: ['DPIA report', 'Data processing records', 'Consent mechanism documentation'],
  iso_42001: ['AI policy statement', 'Risk treatment plan', 'Management review records'],
  nist_ai_rmf: ['Govern function evidence', 'Map function evidence', 'Measure function evidence'],
  dpdp_act: ['Data localization confirmation', 'Consent artefacts', 'Grievance redressal mechanism'],
}

// --- Types ---

interface WizardState {
  workspaceName: string
  workspaceOwner: string
  systemName: string
  systemOwner: string
  systemType: string
  systemVersion: string
  riskTier: AISystemSummary['riskTier']
  selectedFrameworks: string[]
  scanDecision: 'run' | 'skip' | null
}

const initialState: WizardState = {
  workspaceName: '',
  workspaceOwner: '',
  systemName: '',
  systemOwner: '',
  systemType: '',
  systemVersion: '',
  riskTier: 'medium',
  selectedFrameworks: [],
  scanDecision: null,
}

// --- Subcomponents ---

function StepHeader({ step, total }: { step: number; total: number }) {
  return (
    <div className="mb-6">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">
          Step {step} of {total}
        </span>
        <span className="text-xs font-bold text-muted-foreground">{Math.round((step / total) * 100)}% complete</span>
      </div>
      <Progress value={(step / total) * 100} className="h-2 border-2 border-black" />
      <div className="mt-3 grid grid-cols-5 gap-1">
        {STEPS.map((s) => (
          <div
            key={s.number}
            className={`border-2 py-2 px-1 text-center ${
              s.number < step
                ? 'border-black bg-black text-white'
                : s.number === step
                  ? 'border-black bg-[#fff4de] font-black'
                  : 'border-black bg-white text-muted-foreground'
            }`}
          >
            <p className="text-xs font-bold uppercase truncate">{s.label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// --- Steps ---

function Step1({ state, onChange }: { state: WizardState; onChange: (updates: Partial<WizardState>) => void }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-black uppercase">Register the AI system</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Define the workspace that will own this system and identify the AI system itself.
          This creates real records in the FairMind backend.
        </p>
      </div>

      <div className="border-4 border-black p-5 shadow-[6px_6px_0px_0px_#000]">
        <p className="mb-4 text-xs font-black uppercase tracking-[0.2em] text-orange">Workspace</p>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label className="text-xs font-black uppercase">Workspace name *</Label>
            <Input
              value={state.workspaceName}
              onChange={(e) => onChange({ workspaceName: e.target.value })}
              placeholder="e.g. Acme AI Platform"
              className="border-2 border-black"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-black uppercase">Workspace owner *</Label>
            <Input
              value={state.workspaceOwner}
              onChange={(e) => onChange({ workspaceOwner: e.target.value })}
              placeholder="owner@organization.com"
              className="border-2 border-black"
            />
          </div>
        </div>
      </div>

      <div className="border-4 border-black p-5 shadow-[6px_6px_0px_0px_#000]">
        <p className="mb-4 text-xs font-black uppercase tracking-[0.2em] text-orange">AI system</p>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label className="text-xs font-black uppercase">System name *</Label>
            <Input
              value={state.systemName}
              onChange={(e) => onChange({ systemName: e.target.value })}
              placeholder="e.g. Loan Approval Model v2"
              className="border-2 border-black"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-black uppercase">System owner *</Label>
            <Input
              value={state.systemOwner}
              onChange={(e) => onChange({ systemOwner: e.target.value })}
              placeholder="ml-team@organization.com"
              className="border-2 border-black"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-black uppercase">System type</Label>
            <select
              value={state.systemType}
              onChange={(e) => onChange({ systemType: e.target.value })}
              className="w-full border-2 border-black bg-white px-3 py-2 text-sm font-medium focus:outline-none"
            >
              <option value="">Select type…</option>
              {SYSTEM_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-black uppercase">Version</Label>
            <Input
              value={state.systemVersion}
              onChange={(e) => onChange({ systemVersion: e.target.value })}
              placeholder="e.g. v2.1.0"
              className="border-2 border-black"
            />
          </div>
        </div>

        <div className="mt-5">
          <Label className="text-xs font-black uppercase">Risk tier *</Label>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {RISK_TIERS.map((tier) => (
              <button
                key={tier.value}
                type="button"
                onClick={() => onChange({ riskTier: tier.value })}
                className={`border-2 p-3 text-left transition ${
                  state.riskTier === tier.value
                    ? 'border-black bg-black text-white shadow-[4px_4px_0px_0px_#FF6B35]'
                    : 'border-black bg-white hover:bg-[#fff4de]'
                }`}
              >
                <p className="font-black uppercase">{tier.label}</p>
                <p className={`mt-1 text-xs ${state.riskTier === tier.value ? 'text-slate-300' : 'text-muted-foreground'}`}>
                  {tier.description}
                </p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function Step2({ state, onChange }: { state: WizardState; onChange: (updates: Partial<WizardState>) => void }) {
  const toggle = (id: string) => {
    const next = state.selectedFrameworks.includes(id)
      ? state.selectedFrameworks.filter((f) => f !== id)
      : [...state.selectedFrameworks, id]
    onChange({ selectedFrameworks: next })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-black uppercase">Select compliance frameworks</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Choose the regulatory frameworks that apply to this AI system.
          FairMind will auto-generate the corresponding evidence requirements and compliance checks.
        </p>
      </div>

      <div className="space-y-3">
        {COMPLIANCE_FRAMEWORKS.map((fw) => {
          const selected = state.selectedFrameworks.includes(fw.id)
          return (
            <button
              key={fw.id}
              type="button"
              onClick={() => toggle(fw.id)}
              className={`w-full border-2 p-4 text-left transition ${
                selected
                  ? 'border-black bg-black text-white shadow-[4px_4px_0px_0px_#FF6B35]'
                  : 'border-black bg-white hover:bg-[#fff4de]'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-black uppercase">{fw.name}</p>
                    <Badge
                      variant="outline"
                      className={`border px-2 py-0 text-xs font-bold ${selected ? 'border-white text-white' : 'border-black'}`}
                    >
                      {fw.region}
                    </Badge>
                  </div>
                  <p className={`mt-1 text-sm ${selected ? 'text-slate-300' : 'text-muted-foreground'}`}>
                    {fw.description}
                  </p>
                </div>
                {selected && <IconCheck className="mt-1 h-5 w-5 shrink-0 text-orange" />}
              </div>
            </button>
          )
        })}
      </div>

      {state.selectedFrameworks.length > 0 && (
        <div className="border-2 border-black bg-[#e9f7f0] p-4">
          <p className="text-xs font-black uppercase text-emerald-700">
            {state.selectedFrameworks.length} framework{state.selectedFrameworks.length !== 1 ? 's' : ''} selected —
            evidence requirements will be generated automatically
          </p>
        </div>
      )}

      {state.selectedFrameworks.length === 0 && (
        <div className="border-2 border-black bg-[#fff4de] p-4">
          <p className="text-xs font-black uppercase text-amber-700">
            Select at least one framework to continue. You can add more later.
          </p>
        </div>
      )}
    </div>
  )
}

function Step3({
  state,
  onChange,
}: {
  state: WizardState
  onChange: (updates: Partial<WizardState>) => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-black uppercase">Initial bias scan</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          A baseline bias scan establishes the fairness profile before governance review begins.
          You can queue it now or run it after onboarding completes.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <button
          type="button"
          onClick={() => onChange({ scanDecision: 'run' })}
          className={`border-2 p-5 text-left transition ${
            state.scanDecision === 'run'
              ? 'border-black bg-black text-white shadow-[4px_4px_0px_0px_#FF6B35]'
              : 'border-black bg-white hover:bg-[#fff4de]'
          }`}
        >
          <IconRobot className={`h-6 w-6 ${state.scanDecision === 'run' ? 'text-orange' : ''}`} />
          <p className="mt-3 font-black uppercase">Queue scan after onboarding</p>
          <p className={`mt-2 text-sm ${state.scanDecision === 'run' ? 'text-slate-300' : 'text-muted-foreground'}`}>
            After you confirm, you will be redirected to the Bias Detection page to run the first scan for this system.
          </p>
          {state.scanDecision === 'run' && (
            <div className="mt-3 flex items-center gap-2 text-orange">
              <IconCheck className="h-4 w-4" />
              <span className="text-xs font-bold uppercase">Selected</span>
            </div>
          )}
        </button>

        <button
          type="button"
          onClick={() => onChange({ scanDecision: 'skip' })}
          className={`border-2 p-5 text-left transition ${
            state.scanDecision === 'skip'
              ? 'border-black bg-black text-white shadow-[4px_4px_0px_0px_#FF6B35]'
              : 'border-black bg-white hover:bg-[#fff4de]'
          }`}
        >
          <IconFileCheck className={`h-6 w-6 ${state.scanDecision === 'skip' ? 'text-orange' : ''}`} />
          <p className="mt-3 font-black uppercase">Skip for now</p>
          <p className={`mt-2 text-sm ${state.scanDecision === 'skip' ? 'text-slate-300' : 'text-muted-foreground'}`}>
            Proceed directly to the governance dashboard. The bias scan will appear as a pending task in your workflow.
          </p>
          {state.scanDecision === 'skip' && (
            <div className="mt-3 flex items-center gap-2 text-orange">
              <IconCheck className="h-4 w-4" />
              <span className="text-xs font-bold uppercase">Selected</span>
            </div>
          )}
        </button>
      </div>

      <div className="border-2 border-black bg-[#f5f5f5] p-4">
        <div className="flex items-start gap-3">
          <IconShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-slate-500" />
          <p className="text-sm text-muted-foreground">
            Bias scans require a model artifact and a representative dataset. If neither is uploaded yet,
            FairMind will remind you after onboarding is complete.
          </p>
        </div>
      </div>
    </div>
  )
}

function Step4({ state }: { state: WizardState }) {
  const selectedFwDetails = COMPLIANCE_FRAMEWORKS.filter((f) => state.selectedFrameworks.includes(f.id))
  const allEvidence = selectedFwDetails.flatMap((fw) => (FRAMEWORK_EVIDENCE[fw.id] || []).map((e) => ({ fw: fw.name, evidence: e })))

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-black uppercase">Review requirements</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Based on your selections, here is what FairMind will auto-generate when you confirm.
          No action is required on this page — just review and proceed.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">System</p>
          <p className="mt-2 text-xl font-black">{state.systemName || '—'}</p>
          <p className="mt-1 text-sm text-muted-foreground">{state.systemOwner || '—'}</p>
          {state.systemType && (
            <Badge variant="outline" className="mt-2 border-2 border-black font-bold uppercase">
              {state.systemType}
            </Badge>
          )}
        </div>
        <div className="border-2 border-black p-5 shadow-brutal">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Risk tier</p>
          <p className="mt-2 text-xl font-black uppercase">{state.riskTier}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {RISK_TIERS.find((t) => t.value === state.riskTier)?.description}
          </p>
        </div>
      </div>

      {selectedFwDetails.length > 0 && (
        <div className="border-2 border-black p-5 shadow-brutal">
          <p className="mb-3 text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">
            Frameworks selected
          </p>
          <div className="flex flex-wrap gap-2">
            {selectedFwDetails.map((fw) => (
              <Badge key={fw.id} className="border-2 border-black bg-black px-3 py-1 font-black uppercase text-white">
                {fw.name}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {allEvidence.length > 0 && (
        <div className="border-2 border-black p-5 shadow-brutal">
          <p className="mb-3 text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">
            Evidence requirements that will be created ({allEvidence.length})
          </p>
          <div className="space-y-2">
            {allEvidence.map((item, idx) => (
              <div key={idx} className="flex items-start gap-3 border-b border-black/10 pb-2 last:border-0 last:pb-0">
                <IconCircleCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                <div>
                  <span className="text-sm font-bold">{item.evidence}</span>
                  <span className="ml-2 text-xs text-muted-foreground">({item.fw})</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="border-2 border-black bg-black p-5 text-white">
        <p className="text-xs font-black uppercase tracking-[0.25em] text-orange">Governance lifecycle entry</p>
        <p className="mt-2 font-black uppercase">
          After confirmation, this system enters the <span className="text-orange">Onboard</span> stage of the lifecycle:
        </p>
        <div className="mt-3 flex items-center gap-2 text-sm">
          {['Onboard', 'Assess', 'Govern', 'Remediate', 'Operate'].map((stage, idx, arr) => (
            <span key={stage} className="flex items-center gap-2">
              <span className={`font-bold ${stage === 'Onboard' ? 'text-orange' : 'text-slate-400'}`}>{stage}</span>
              {idx < arr.length - 1 && <IconArrowRight className="h-3 w-3 text-slate-500" />}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

function Step5({
  state,
  submitting,
  onConfirm,
}: {
  state: WizardState
  submitting: boolean
  onConfirm: () => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-black uppercase">Confirm &amp; enter lifecycle</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Review the summary below and confirm. This creates the workspace and AI system in FairMind
          and scopes the dashboard to this system.
        </p>
      </div>

      <div className="border-4 border-black bg-[linear-gradient(135deg,#fff4de_0%,#fff_55%,#e9f7f0_100%)] p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <p className="text-xs font-black uppercase tracking-[0.25em] text-orange">Ready to register</p>
        <h3 className="mt-3 text-2xl font-black uppercase">{state.systemName}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{state.systemOwner}</p>

        <div className="mt-5 grid gap-3 md:grid-cols-3">
          <div className="border-2 border-black bg-white p-3">
            <p className="text-xs font-bold uppercase text-muted-foreground">Workspace</p>
            <p className="mt-1 font-black">{state.workspaceName}</p>
          </div>
          <div className="border-2 border-black bg-white p-3">
            <p className="text-xs font-bold uppercase text-muted-foreground">Risk tier</p>
            <p className="mt-1 font-black uppercase">{state.riskTier}</p>
          </div>
          <div className="border-2 border-black bg-white p-3">
            <p className="text-xs font-bold uppercase text-muted-foreground">Frameworks</p>
            <p className="mt-1 font-black">{state.selectedFrameworks.length || 'None selected'}</p>
          </div>
        </div>

        {state.selectedFrameworks.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {state.selectedFrameworks.map((id) => {
              const fw = COMPLIANCE_FRAMEWORKS.find((f) => f.id === id)
              return fw ? (
                <Badge key={id} variant="outline" className="border-2 border-black font-bold uppercase">
                  {fw.name}
                </Badge>
              ) : null
            })}
          </div>
        )}

        {state.scanDecision === 'run' && (
          <div className="mt-4 flex items-center gap-2 border-2 border-black bg-white p-3">
            <IconRobot className="h-4 w-4 text-orange" />
            <p className="text-sm font-bold">Bias scan queued — you will be redirected after confirmation.</p>
          </div>
        )}
      </div>

      <Button
        type="button"
        onClick={onConfirm}
        disabled={submitting}
        className="w-full border-2 border-black py-4 text-lg font-black uppercase shadow-[4px_4px_0px_0px_#FF6B35]"
      >
        {submitting ? (
          'Creating system…'
        ) : (
          <>
            <IconBuildingSkyscraper className="mr-3 h-5 w-5" />
            Register AI system and enter lifecycle
          </>
        )}
      </Button>
    </div>
  )
}

// --- Main page ---

export default function OnboardPage() {
  const router = useRouter()
  const { createWorkspaceAndSystem } = useSystemContext()
  const { toast } = useToast()
  const [step, setStep] = useState(1)
  const [state, setState] = useState<WizardState>(initialState)
  const [submitting, setSubmitting] = useState(false)

  const update = (updates: Partial<WizardState>) => setState((prev) => ({ ...prev, ...updates }))

  const canAdvance = (): boolean => {
    if (step === 1) {
      return (
        state.workspaceName.trim().length > 0 &&
        state.workspaceOwner.trim().length > 0 &&
        state.systemName.trim().length > 0 &&
        state.systemOwner.trim().length > 0
      )
    }
    if (step === 2) return state.selectedFrameworks.length > 0
    if (step === 3) return state.scanDecision !== null
    return true
  }

  const handleConfirm = async () => {
    try {
      setSubmitting(true)
      await createWorkspaceAndSystem({
        workspaceName: state.workspaceName,
        workspaceOwner: state.workspaceOwner,
        systemName: state.systemName,
        systemOwner: state.systemOwner,
        riskTier: state.riskTier,
        stage: 'onboard',
        systemType: state.systemType || undefined,
        systemVersion: state.systemVersion || undefined,
        complianceFrameworks: state.selectedFrameworks,
      })
      toast({
        title: 'AI system registered',
        description: `${state.systemName} is now in the governance lifecycle.`,
      })
      if (state.scanDecision === 'run') {
        router.push('/bias')
      } else {
        router.push('/dashboard')
      }
    } catch (error) {
      toast({
        title: 'Registration failed',
        description: error instanceof Error ? error.message : 'Could not register the AI system.',
        variant: 'destructive',
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Page header */}
      <Card className="overflow-hidden border-4 border-black bg-black text-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <div className="p-6">
          <div className="flex items-center gap-3">
            <div className="border-2 border-white p-2 shadow-[4px_4px_0px_0px_#FF6B35]">
              <IconBuildingSkyscraper className="h-6 w-6 text-orange" />
            </div>
            <div>
              <Badge className="border-2 border-orange bg-orange/20 px-3 py-1 font-black uppercase text-orange">
                Onboard
              </Badge>
            </div>
          </div>
          <h1 className="mt-4 text-4xl font-black uppercase tracking-tight">
            Register a new AI system
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-300">
            Complete this 5-step flow to register your AI system in FairMind and enter the governed lifecycle:
            assessment → risk → evidence → remediation → approval → release.
          </p>
        </div>
      </Card>

      {/* Wizard card */}
      <Card className="border-4 border-black p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <StepHeader step={step} total={STEPS.length} />

        {step === 1 && <Step1 state={state} onChange={update} />}
        {step === 2 && <Step2 state={state} onChange={update} />}
        {step === 3 && <Step3 state={state} onChange={update} />}
        {step === 4 && <Step4 state={state} />}
        {step === 5 && <Step5 state={state} submitting={submitting} onConfirm={() => void handleConfirm()} />}

        {step < 5 && (
          <div className="mt-8 flex justify-between gap-4">
            <Button
              variant="neutral"
              onClick={() => setStep((s) => Math.max(1, s - 1))}
              disabled={step === 1}
              className="border-2 border-black font-bold"
            >
              <IconArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button
              onClick={() => setStep((s) => s + 1)}
              disabled={!canAdvance()}
              className="border-2 border-black font-black uppercase shadow-[4px_4px_0px_0px_#FF6B35]"
            >
              Continue
              <IconArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        )}
      </Card>
    </div>
  )
}
