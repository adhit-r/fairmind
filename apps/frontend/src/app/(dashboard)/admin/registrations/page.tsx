'use client'

import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '@/lib/api/api-client'
import { useSearchParams, useRouter } from 'next/navigation'
import { IconCheck, IconX, IconClock, IconUser, IconBuilding } from '@tabler/icons-react'
import { useToast } from '@/hooks/use-toast'

interface RegistrationRequest {
  id: string
  email: string
  name: string
  org_name: string
  org_domain: string | null
  requested_role: string
  message: string | null
  status: string
  review_notes: string | null
  reviewed_at: string | null
  created_at: string
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-50 border-yellow-600 text-yellow-800',
  approved: 'bg-green-50 border-green-600 text-green-800',
  denied: 'bg-red-50 border-red-600 text-red-800',
}

export default function RegistrationsPage() {
  const { toast } = useToast()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [requests, setRequests] = useState<RegistrationRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>(searchParams.get('status') || 'pending')
  const [reviewModal, setReviewModal] = useState<{ id: string; action: 'approve' | 'deny' } | null>(null)
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const fetchRequests = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiClient.get<{ requests: RegistrationRequest[] }>(
        `/api/v1/registrations?status_filter=${filter}`
      )
      setRequests(data.data?.requests || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => { fetchRequests() }, [fetchRequests])

  // Handle approve/deny deep links from email
  useEffect(() => {
    const action = searchParams.get('action') as 'approve' | 'deny' | null
    const id = searchParams.get('id')
    if (action && id) {
      setReviewModal({ id, action })
      router.replace('/admin/registrations')
    }
  }, [searchParams, router])

  const submitReview = async () => {
    if (!reviewModal) return
    setSubmitting(true)
    try {
      await apiClient.post(`/api/v1/registrations/${reviewModal.id}/${reviewModal.action}`, { notes })
      toast({
        title: reviewModal.action === 'approve' ? 'Request approved' : 'Request denied',
        description: 'The applicant has been notified by email.',
      })
      setReviewModal(null)
      setNotes('')
      fetchRequests()
    } catch (e: any) {
      toast({ title: 'Error', description: e?.message, variant: 'destructive' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-w-0">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 border-b border-[var(--fm-line)] pb-6 flex items-center justify-between">
          <div>
            <h1 className="text-[30px] font-semibold tracking-[-.03em]">Access Requests</h1>
            <p className="mt-2 text-gray-600">Review and approve org signup requests. Applicants are notified via email.</p>
          </div>
          <div className="flex gap-2">
            {['pending', 'approved', 'denied'].map(s => (
              <button key={s} onClick={() => setFilter(s)}
                className={`h-8 rounded-full px-4 text-[12.5px] font-medium capitalize transition-colors ${
                  filter === s ? 'bg-[var(--fm-ink)] text-white' : 'border border-[var(--fm-line)] bg-white text-[var(--fm-ink2)]'
                }`}>
                {s}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <div className="h-12 w-12 animate-spin rounded-full border-2 border-[var(--fm-line)] border-t-[var(--fm-ink)]" />
          </div>
        ) : requests.length === 0 ? (
          <div className="p-12 text-center fm-card">
            <IconClock className="mx-auto mb-4 h-12 w-12 text-gray-400" />
            <h3 className="text-xl font-bold">No {filter} requests</h3>
            <p className="mt-2 text-gray-600">New access requests appear here when users sign up.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {requests.map(req => (
              <div key={req.id} className="p-6 fm-card">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="text-lg font-bold">{req.name}</h3>
                      <span className={`border-2 px-2 py-0.5 text-xs font-semibold ${STATUS_COLORS[req.status]}`}>
                        {req.status}
                      </span>
                      <span className="border border-[var(--fm-line)] px-2 py-0.5 text-xs font-semibold">
                        {req.requested_role}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <IconUser className="h-4 w-4" />{req.email}
                      </span>
                      <span className="flex items-center gap-1">
                        <IconBuilding className="h-4 w-4" />{req.org_name}
                        {req.org_domain && ` (${req.org_domain})`}
                      </span>
                    </div>
                    {req.message && (
                      <p className="mt-3 border-l border-[var(--fm-line)] pl-3 text-sm italic text-gray-700">
                        &ldquo;{req.message}&rdquo;
                      </p>
                    )}
                    {req.review_notes && (
                      <p className="mt-2 text-sm text-gray-500">Notes: {req.review_notes}</p>
                    )}
                  </div>

                  {req.status === 'pending' && (
                    <div className="flex gap-2 flex-shrink-0">
                      <button
                        onClick={() => { setReviewModal({ id: req.id, action: 'approve' }); setNotes('') }}
                        className="flex items-center gap-2 rounded-full bg-[var(--fm-ink)] px-4 py-2 font-semibold text-sm text-white transition-all"
                      >
                        <IconCheck className="h-4 w-4" /> Approve
                      </button>
                      <button
                        onClick={() => { setReviewModal({ id: req.id, action: 'deny' }); setNotes('') }}
                        className="flex items-center gap-2 border border-[var(--fm-line)] bg-white px-4 py-2 font-bold text-sm transition-all"
                      >
                        <IconX className="h-4 w-4" /> Deny
                      </button>
                    </div>
                  )}
                </div>

                <p className="mt-3 text-xs text-gray-400">
                  Submitted {new Date(req.created_at).toLocaleString()}
                  {req.reviewed_at && ` · Reviewed ${new Date(req.reviewed_at).toLocaleString()}`}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Review modal */}
      {reviewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md p-8 fm-card">
            <h2 className="text-2xl font-bold mb-2 capitalize">
              {reviewModal.action} Request
            </h2>
            <p className="text-gray-600 mb-4">
              {reviewModal.action === 'approve'
                ? 'The user will receive an approval email and their account will be created.'
                : 'The user will receive a denial email.'}
            </p>
            <div className="space-y-2 mb-6">
              <label className="font-bold text-sm">Notes (optional)</label>
              <textarea
                placeholder={reviewModal.action === 'deny' ? 'Reason for denial...' : 'Welcome message...'}
                value={notes}
                onChange={e => setNotes(e.target.value)}
                rows={3}
                className="w-full border border-[var(--fm-line)] px-3 py-2 text-sm resize-none focus:outline-none"
              />
            </div>
            <div className="flex gap-3">
              <button
                onClick={submitReview}
                disabled={submitting}
                className={`h-10 flex-1 rounded-full text-[13px] font-semibold capitalize transition-colors ${
                  reviewModal.action === 'approve'
                    ? 'bg-[var(--fm-ink)] text-white'
                    : 'bg-[#b4232c] text-white'
                }`}
              >
                {submitting ? 'Processing...' : `Confirm ${reviewModal.action}`}
              </button>
              <button
                onClick={() => setReviewModal(null)}
                className="flex-1 border border-[var(--fm-line)] py-3 font-semibold text-sm bg-white"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
