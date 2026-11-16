'use client'

import * as React from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

export interface ConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: React.ReactNode
  description?: React.ReactNode
  confirmLabel?: string
  cancelLabel?: string
  /** Styles the confirm button as destructive instead of primary. */
  destructive?: boolean
  /** Require a written rationale before confirming (decisions, risk acceptance, deletions). */
  requireRationale?: boolean
  rationaleLabel?: string
  rationaleHelp?: string
  /** Minimum trimmed rationale length when requireRationale is set. Default 10. */
  minRationaleLength?: number
  /** Called with the trimmed rationale (if collected). May be async; the dialog stays busy until it settles. */
  onConfirm: (rationale?: string) => void | Promise<void>
  /** External busy flag (e.g. a mutation owned by the caller). */
  busy?: boolean
  /** Error from the last confirm attempt, shown inline. */
  error?: React.ReactNode
}

/** Confirmation for destructive or high-stakes actions, with optional required rationale. */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  destructive = false,
  requireRationale = false,
  rationaleLabel = 'Rationale',
  rationaleHelp = 'Recorded with this decision in the audit trail.',
  minRationaleLength = 10,
  onConfirm,
  busy = false,
  error,
}: ConfirmDialogProps) {
  const [rationale, setRationale] = React.useState('')
  const [touched, setTouched] = React.useState(false)
  const [pending, setPending] = React.useState(false)
  const rationaleId = React.useId()
  const helpId = `${rationaleId}-help`
  const errorId = `${rationaleId}-error`

  React.useEffect(() => {
    if (!open) {
      setRationale('')
      setTouched(false)
      setPending(false)
    }
  }, [open])

  const trimmed = rationale.trim()
  const rationaleInvalid = requireRationale && trimmed.length < minRationaleLength
  const isBusy = busy || pending

  const handleConfirm = async () => {
    if (rationaleInvalid) {
      setTouched(true)
      return
    }
    setPending(true)
    try {
      await onConfirm(requireRationale ? trimmed : undefined)
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => { if (!isBusy) onOpenChange(next) }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>
        {requireRationale && (
          <div className="space-y-2">
            <Label htmlFor={rationaleId}>
              {rationaleLabel} <span className="text-destructive-strong">(required)</span>
            </Label>
            <Textarea
              id={rationaleId}
              value={rationale}
              onChange={(event) => setRationale(event.target.value)}
              onBlur={() => setTouched(true)}
              aria-invalid={touched && rationaleInvalid}
              aria-describedby={touched && rationaleInvalid ? `${helpId} ${errorId}` : helpId}
              disabled={isBusy}
            />
            <p id={helpId} className="text-xs text-muted-foreground">{rationaleHelp}</p>
            {touched && rationaleInvalid && (
              <p id={errorId} role="alert" className="text-xs font-medium text-destructive-strong">
                Enter at least {minRationaleLength} characters explaining the decision.
              </p>
            )}
          </div>
        )}
        {error && <p role="alert" className="text-sm font-medium text-destructive-strong">{error}</p>}
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isBusy}>
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant={destructive ? 'destructive' : 'default'}
            onClick={() => void handleConfirm()}
            disabled={isBusy}
            aria-busy={isBusy}
          >
            {isBusy ? 'Working...' : confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
