'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Database, 
  Upload, 
  Search, 
  Filter, 
  Eye, 
  Edit, 
  Trash2, 
  Download, 
  Share2, 
  Settings, 
  RefreshCw, 
  Plus, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  FileText, 
  Brain, 
  Shield, 
  Activity, 
  ChevronRight, 
  ChevronDown, 
  HelpCircle, 
  BookOpen, 
  Video, 
  MessageSquare, 
  Mail, 
  Bell, 
  User, 
  LogOut, 
  Home, 
  XCircle,
  TrendingDown,
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
  Clock as ClockIcon,
  Sparkles,
  Zap
} from 'lucide-react'
import { PageWrapper } from '@/components/core/PageWrapper'
import { Card } from '@/components/core/Card'
import { Button } from '@/components/core/Button'
import { api } from '@/config/api'

interface Model {
  id: string
  name: string
  description: string
  model_type: string
  version: string
  upload_date: string
  file_path: string
  file_size: number
  tags: string[]
  metadata: any
  status: 'active' | 'inactive' | 'pending' | 'testing'
  accuracy?: number
  bias_score?: number
  security_score?: number
  compliance_score?: number
}

export default function ModelRegistry() {
  return (
    <div className="space-y-6 p-4 md:p-6 max-w-[2000px] mx-auto">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gold">
          MODEL_REGISTRY
            </h1>
        <p className="text-xs md:text-sm text-muted-foreground font-mono">
          MANAGE.AND.TRACK.AI.MODELS.FOR.GOVERNANCE.AND.COMPLIANCE
            </p>
          </div>
          
      {/* Registry Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">TOTAL_MODELS</p>
              <p className="text-lg font-bold">0</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">NO_MODELS</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">ACTIVE_MODELS</p>
              <p className="text-lg font-bold">0</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">NO_ACTIVE</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">MODELS_IN_TESTING</p>
              <p className="text-lg font-bold">0</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">NO_TESTING</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-mono">COMPLIANCE_RATE</p>
              <p className="text-lg font-bold">--</p>
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">NO_DATA</span>
              </div>
            </div>
            </div>
          </div>
        </div>

      {/* Action Section */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-2">
          <button className="bg-gold text-gold-foreground hover:bg-gold/90 w-full sm:w-auto px-4 py-2 rounded font-mono text-sm transition-colors">
            <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span className="whitespace-nowrap">UPLOAD_NEW_MODEL</span>
          </button>
          <button className="bg-transparent border border-border hover:bg-accent w-full sm:w-auto px-4 py-2 rounded font-mono text-sm transition-colors">
            <svg className="inline mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span className="whitespace-nowrap">SEARCH_MODELS</span>
          </button>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative w-full sm:w-80">
            <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              placeholder="SEARCH_MODELS_BY_NAME_TYPE_TAGS..."
              className="pl-10 font-mono text-xs h-9 w-full bg-background border border-border rounded px-3"
            />
          </div>
                  </div>
                </div>

      {/* Model Categories */}
      <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-3">
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">RECENT_UPLOADS</h3>
            <p className="text-xs text-muted-foreground font-mono">LATEST.MODEL.REGISTRATIONS</p>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2">NO_RECENT_UPLOADS</h4>
                <p className="text-xs text-muted-foreground font-mono">UPLOAD_YOUR_FIRST_MODEL_TO_GET_STARTED</p>
              </div>
                  </div>
                  </div>
                </div>
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">MODEL_TYPES</h3>
            <p className="text-xs text-muted-foreground font-mono">CLASSIFICATION.REGRESSION.NLP.CV</p>
                  </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2">NO_MODEL_TYPES</h4>
                <p className="text-xs text-muted-foreground font-mono">UPLOAD_MODELS_TO_SEE_TYPE_DISTRIBUTION</p>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg min-h-[400px] flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-bold text-gold">MODEL_STATUS</h3>
            <p className="text-xs text-muted-foreground font-mono">ACTIVE.TESTING.PENDING.INACTIVE</p>
              </div>
          <div className="flex-1 p-4">
            <div className="h-full w-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h4 className="text-sm font-bold mb-2">NO_STATUS_DATA</h4>
                <p className="text-xs text-muted-foreground font-mono">UPLOAD_MODELS_TO_SEE_STATUS_DISTRIBUTION</p>
      </div>
    </div>
            </div>
        </div>
        </div>

      {/* Model Registry Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="flex flex-col space-y-1.5">
            <h3 className="text-sm font-bold text-gold">MODEL_REGISTRY_TABLE</h3>
            <p className="text-xs text-muted-foreground font-mono">COMPREHENSIVE.MODEL.MANAGEMENT.AND.TRACKING</p>
          </div>
        </div>
        <div className="p-4">
          <div className="rounded-md border border-border">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 text-xs font-mono">MODEL_NAME</th>
                  <th className="text-left p-3 text-xs font-mono">TYPE</th>
                  <th className="text-left p-3 text-xs font-mono">VERSION</th>
                  <th className="text-left p-3 text-xs font-mono">STATUS</th>
                  <th className="text-left p-3 text-xs font-mono">UPLOAD_DATE</th>
                  <th className="text-left p-3 text-xs font-mono">COMPLIANCE</th>
                  <th className="text-left p-3 text-xs font-mono">BIAS_SCORE</th>
                  <th className="text-left p-3 text-xs font-mono">SECURITY_SCORE</th>
                  <th className="text-right p-3 text-xs font-mono">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border">
                  <td className="p-3 text-xs font-mono text-muted-foreground" colSpan={9}>
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                      </div>
                      <h4 className="text-sm font-bold mb-2">NO_MODELS_REGISTERED</h4>
                      <p className="text-xs text-muted-foreground font-mono">
                        UPLOAD_YOUR_FIRST_MODEL_TO_START_MANAGING_YOUR_AI_PORTFOLIO
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
