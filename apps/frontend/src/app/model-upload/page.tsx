'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { 
  CheckCircle, 
  ArrowLeft, 
  Upload, 
  Database, 
  FileText, 
  AlertTriangle, 
  X, 
  Info,
  Brain,
  Sparkles,
  Zap
} from 'lucide-react'
import { PageWrapper } from '@/components/core/PageWrapper'
import { Card } from '@/components/core/Card'
import { Button } from '@/components/core/Button'
import { api } from '@/config/api'

export default function ModelUploadPage() {
    return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
          MODEL_UPLOAD
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          REGISTER.AI.MODELS.FOR.GOVERNANCE.TRACKING.AND.COMPLIANCE.MONITORING
        </p>
                </div>
                
      {/* Upload Flow Steps */}
      <div className="grid gap-4 sm:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
                <div>
              <p className="text-xs text-muted-foreground font-mono">STEP_1</p>
              <p className="text-lg font-bold text-gold">UPLOAD</p>
                  </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
                  </div>
                </div>
                  </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
                <div>
              <p className="text-xs text-muted-foreground font-mono">STEP_2</p>
              <p className="text-lg font-bold">VALIDATE</p>
                  </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
                  </div>
                </div>
              </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">STEP_3</p>
              <p className="text-lg font-bold">TEST</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
        </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">STEP_4</p>
              <p className="text-lg font-bold">DEPLOY</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
                        </div>
                      </div>
                    </div>
                    
      {/* Main Upload Form */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 lg:grid-cols-3">
        {/* Upload Form */}
        <div className="bg-card border border-border rounded-lg lg:col-span-2 min-h-[600px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">MODEL_INFORMATION</h3>
            <p className="text-xs text-muted-foreground font-mono">
              PROVIDE.MODEL.METADATA.AND.UPLOAD.FILES
            </p>
                  </div>
          <div className="flex-1 p-4">
            <div className="space-y-6">
              {/* Model Details Form */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-mono text-muted-foreground mb-2">
                    MODEL_NAME *
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-background border border-border rounded font-mono text-sm"
                    placeholder="E.G._CREDIT_RISK_MODEL"
                  />
            </div>
              <div>
                  <label className="block text-xs font-mono text-muted-foreground mb-2">
                    VERSION *
                </label>
                <input
                  type="text"
                    className="w-full px-3 py-2 bg-background border border-border rounded font-mono text-sm"
                    placeholder="E.G._1.0.0"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-mono text-muted-foreground mb-2">
                  DESCRIPTION
                </label>
                <textarea
                  rows={3}
                  className="w-full px-3 py-2 bg-background border border-border rounded font-mono text-sm"
                  placeholder="DESCRIBE.MODEL.PURPOSE.AND.FUNCTIONALITY"
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-mono text-muted-foreground mb-2">
                    MODEL_TYPE
                  </label>
                  <select className="w-full px-3 py-2 bg-background border border-border rounded font-mono text-sm">
                    <option value="">SELECT_TYPE</option>
                    <option value="classification">CLASSIFICATION</option>
                    <option value="regression">REGRESSION</option>
                    <option value="clustering">CLUSTERING</option>
                    <option value="nlp">NLP</option>
                    <option value="computer-vision">COMPUTER_VISION</option>
                    <option value="custom">CUSTOM</option>
                  </select>
            </div>
                <div>
                  <label className="block text-xs font-mono text-muted-foreground mb-2">
                    FRAMEWORK
              </label>
                  <select className="w-full px-3 py-2 bg-background border border-border rounded font-mono text-sm">
                    <option value="">SELECT_FRAMEWORK</option>
                    <option value="tensorflow">TENSORFLOW</option>
                    <option value="pytorch">PYTORCH</option>
                    <option value="scikit-learn">SCIKIT_LEARN</option>
                    <option value="xgboost">XGBOOST</option>
                    <option value="lightgbm">LIGHTGBM</option>
                    <option value="other">OTHER</option>
                  </select>
                </div>
            </div>

              <div>
                <label className="block text-xs font-mono text-muted-foreground mb-2">
                  TAGS
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 bg-background border border-border rounded font-mono text-sm"
                  placeholder="E.G._FINANCE_RISK_ML_COMMA_SEPARATED"
                />
              </div>
              
              {/* File Upload Area */}
              <div>
                <label className="block text-xs font-mono text-muted-foreground mb-2">
                  MODEL_FILE *
                </label>
                <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-gold transition-colors">
                  <svg className="h-12 w-12 text-muted-foreground mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-sm font-mono mb-2">
                    CLICK_TO_UPLOAD_OR_DRAG_AND_DROP
                  </p>
                  <p className="text-xs text-muted-foreground font-mono">
                    SUPPORTED_FORMATS: PKL_JOBLIB_H5_ONNX_PB_PT_PTH
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4 pt-4">
                <button className="bg-gold text-gold-foreground hover:bg-gold/90 px-4 py-2 rounded font-mono text-sm transition-colors">
                  <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  <span>UPLOAD_MODEL</span>
                </button>
                <button className="bg-transparent border border-border hover:bg-accent px-4 py-2 rounded font-mono text-sm transition-colors">
                  <span>CANCEL</span>
                </button>
              </div>
            </div>
              </div>
            </div>

        {/* Info Panel */}
        <div className="space-y-4">
          {/* Upload Guidelines */}
          <div className="bg-card border border-border rounded-lg min-h-[300px] flex flex-col">
            <div className="p-4 border-b border-border">
              <h3 className="text-sm font-bold text-gold">UPLOAD_GUIDELINES</h3>
              <p className="text-xs text-muted-foreground font-mono">
                REQUIREMENTS.AND.BEST.PRACTICES
              </p>
            </div>
            <div className="flex-1 p-4">
              <div className="space-y-4 text-xs">
                <div>
                  <h4 className="font-bold text-sm mb-2">SUPPORTED_FORMATS</h4>
                  <ul className="space-y-1 text-muted-foreground font-mono">
                    <li>• PICKLE (.PKL)</li>
                    <li>• JOBLIB (.JOBLIB)</li>
                    <li>• HDF5 (.H5)</li>
                    <li>• ONNX (.ONNX)</li>
                    <li>• TENSORFLOW (.PB)</li>
                    <li>• PYTORCH (.PT, .PTH)</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-bold text-sm mb-2">FILE_SIZE_LIMIT</h4>
                  <p className="text-muted-foreground font-mono">MAXIMUM_FILE_SIZE: 100_MB</p>
                </div>
                
                <div>
                  <h4 className="font-bold text-sm mb-2">REQUIRED_FIELDS</h4>
                  <ul className="space-y-1 text-muted-foreground font-mono">
                    <li>• MODEL_NAME</li>
                    <li>• VERSION</li>
                    <li>• MODEL_FILE</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* What Happens Next */}
          <div className="bg-card border border-border rounded-lg min-h-[300px] flex flex-col">
            <div className="p-4 border-b border-border">
              <h3 className="text-sm font-bold text-gold">WHAT_HAPPENS_NEXT</h3>
              <p className="text-xs text-muted-foreground font-mono">
                UPLOAD.PROCESS.FLOW
              </p>
            </div>
            <div className="flex-1 p-4">
              <div className="space-y-3 text-xs">
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-gold rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-gold-foreground text-xs font-bold">1</span>
                  </div>
                  <div>
                    <p className="font-bold mb-1">FILE_VALIDATION</p>
                    <p className="text-muted-foreground font-mono">VERIFY_MODEL_FILE_FORMAT_AND_STRUCTURE</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-muted rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-muted-foreground text-xs font-bold">2</span>
                  </div>
                  <div>
                    <p className="font-bold mb-1">METADATA_EXTRACTION</p>
                    <p className="text-muted-foreground font-mono">EXTRACT_MODEL_ARCHITECTURE_AND_PARAMETERS</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-muted rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-muted-foreground text-xs font-bold">3</span>
                  </div>
              <div>
                    <p className="font-bold mb-1">GOVERNANCE_SETUP</p>
                    <p className="text-muted-foreground font-mono">CONFIGURE_BIAS_DETECTION_AND_MONITORING</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Uploads */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="flex flex-col space-y-1.5">
            <h3 className="text-sm font-bold text-gold">RECENT_UPLOADS</h3>
            <p className="text-xs text-muted-foreground font-mono">LATEST.MODEL.REGISTRATIONS</p>
          </div>
        </div>
        <div className="p-4">
          <div className="rounded-md border border-border">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 text-xs font-mono">MODEL_NAME</th>
                  <th className="text-left p-3 text-xs font-mono">TYPE</th>
                  <th className="text-left p-3 text-xs font-mono">UPLOAD_DATE</th>
                  <th className="text-left p-3 text-xs font-mono">STATUS</th>
                  <th className="text-right p-3 text-xs font-mono">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border">
                  <td className="p-3 text-xs font-mono text-muted-foreground" colSpan={5}>
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                      </div>
                      <h4 className="text-sm font-bold mb-2">NO_MODELS_UPLOADED</h4>
                      <p className="text-xs text-muted-foreground font-mono">
                        UPLOAD_YOUR_FIRST_MODEL_TO_GET_STARTED
                      </p>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
