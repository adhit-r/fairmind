"use client"

import { ModelUpload } from "@/components/features/model-catalog/model-upload"
import { ProtectedRoute } from "@/components/core/auth/protected-route"

export default function ModelUploadPage() {
  return (
    <ProtectedRoute>
      <div className="container mx-auto py-6">
        <ModelUpload />
      </div>
    </ProtectedRoute>
  )
}
