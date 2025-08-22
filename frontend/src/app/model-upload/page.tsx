"use client"

import React, { useState } from 'react'
import { ModelUpload } from '@/components/features/model-registry/model-upload'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/common/card'
import { Button } from '@/components/ui/common/button'
import { CheckCircle, ArrowLeft } from 'lucide-react'

export default function ModelUploadPage() {
  const router = useRouter()
  const [uploadComplete, setUploadComplete] = useState(false)
  const [uploadedModel, setUploadedModel] = useState<any>(null)

  const handleUploadComplete = (model: any) => {
    setUploadedModel(model)
    setUploadComplete(true)
  }

  const handleCancel = () => {
    router.push('/dashboard')
  }

  const handleContinue = () => {
    router.push('/dashboard')
  }

  const handleUploadAnother = () => {
    setUploadComplete(false)
    setUploadedModel(null)
  }

  if (uploadComplete && uploadedModel) {
    return (
      <div className="container mx-auto p-6">
        <div className="max-w-2xl mx-auto">
          <Button
            variant="ghost"
            onClick={handleContinue}
            className="mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>

          <Card className="border-green-200 bg-green-50">
            <CardContent className="p-8 text-center">
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Model Uploaded Successfully!
              </h2>
              <p className="text-gray-600 mb-6">
                Your model "{uploadedModel.name}" has been uploaded and is now being processed.
              </p>

              <div className="bg-white rounded-lg p-6 mb-6 text-left">
                <h3 className="font-semibold text-gray-900 mb-3">Model Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Name:</span>
                    <span className="font-medium">{uploadedModel.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Version:</span>
                    <span className="font-medium">{uploadedModel.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Type:</span>
                    <span className="font-medium">{uploadedModel.type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Framework:</span>
                    <span className="font-medium">{uploadedModel.framework}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Files:</span>
                    <span className="font-medium">{uploadedModel.files.length} file(s)</span>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h4 className="font-semibold text-blue-900 mb-2">What happens next?</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Model is being analyzed for bias and fairness issues</li>
                  <li>• Security vulnerabilities are being checked</li>
                  <li>• Performance metrics are being calculated</li>
                  <li>• Compliance requirements are being verified</li>
                </ul>
              </div>

              <div className="flex space-x-4 justify-center">
                <Button onClick={handleContinue} className="bg-green-600 hover:bg-green-700">
                  Go to Dashboard
                </Button>
                <Button variant="outline" onClick={handleUploadAnother}>
                  Upload Another Model
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={handleCancel}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>
      </div>

      <ModelUpload 
        onUploadComplete={handleUploadComplete}
        onCancel={handleCancel}
      />
    </div>
  )
}
