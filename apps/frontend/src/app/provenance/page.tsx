'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  GitBranch, 
  GitCommit, 
  GitPullRequest, 
  GitMerge, 
  GitCompare, 
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
  TrendingDown as TrendingDownIcon,
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
  Clock as ClockIcon,
  ArrowLeft
} from 'lucide-react'
import { PageWrapper } from '@/components/core/PageWrapper'
import { Card } from '@/components/core/Card'
import { Button } from '@/components/core/Button'

interface ProvenanceEvent {
  id: string
  type: 'training' | 'deployment' | 'update' | 'approval'
  title: string
  description: string
  model: string
  timestamp: string
  status: 'completed' | 'pending' | 'failed'
  icon: React.ReactNode
}

const demoEvents: ProvenanceEvent[] = [
  {
    id: 'event-1',
    type: 'training',
    title: 'Credit Risk Model v1.1.0 - Training Complete',
    description: 'Model retraining completed with bias mitigation techniques',
    model: 'Credit Risk Model',
    timestamp: '2024-01-17T10:00:00Z',
    status: 'completed',
    icon: <GitCommit className="h-4 w-4" />
  },
  {
    id: 'event-2',
    type: 'deployment',
    title: 'Fraud Detection Model v2.1.0 - Deployed',
    description: 'Model deployed to production with monitoring enabled',
    model: 'Fraud Detection Model',
    timestamp: '2024-01-16T14:30:00Z',
    status: 'completed',
    icon: <GitBranch className="h-4 w-4" />
  },
  {
    id: 'event-3',
    type: 'update',
    title: 'Customer Segmentation Model - Update Pending',
    description: 'Model update awaiting approval from governance team',
    model: 'Customer Segmentation Model',
    timestamp: '2024-01-14T09:15:00Z',
    status: 'pending',
    icon: <GitPullRequest className="h-4 w-4" />
  }
]

export default function ProvenancePage() {
  const router = useRouter()
  const [events, setEvents] = useState<ProvenanceEvent[]>(demoEvents)

  const handleBack = () => {
    router.push('/')
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/10 text-green-400 border-green-500/20'
      case 'pending':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
      case 'failed':
        return 'bg-red-500/10 text-red-400 border-red-500/20'
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20'
    }
  }

  const getEventIconColor = (type: string) => {
    switch (type) {
      case 'training':
        return 'bg-green-500'
      case 'deployment':
        return 'bg-blue-500'
      case 'update':
        return 'bg-yellow-500'
      case 'approval':
        return 'bg-purple-500'
      default:
        return 'bg-slate-500'
    }
  }

  return (
    <PageWrapper title="Model Provenance" subtitle="Track model lineage, data sources, and complete audit trails">
      <div className="mb-6">
        <Button 
          variant="ghost" 
          icon={ArrowLeft}
          onClick={handleBack}
        >
          Back to Dashboard
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card 
          title="Model Lineage" 
          icon={<GitBranch className="h-5 w-5 text-blue-400" />}
          gradient="from-blue-500/10 to-purple-500/10"
        >
          <p className="text-slate-300 text-sm mb-4">
            Track the complete history of model versions, training runs, and deployments.
          </p>
          <Button variant="outline" size="sm">
            View Lineage
          </Button>
        </Card>

        <Card 
          title="Data Sources" 
          icon={<Database className="h-5 w-5 text-green-400" />}
          gradient="from-green-500/10 to-emerald-500/10"
        >
          <p className="text-slate-300 text-sm mb-4">
            Monitor data lineage and track which datasets were used for training.
          </p>
          <Button variant="outline" size="sm">
            View Sources
          </Button>
        </Card>

        <Card 
          title="Audit Trail" 
          icon={<Shield className="h-5 w-5 text-yellow-400" />}
          gradient="from-yellow-500/10 to-orange-500/10"
        >
          <p className="text-slate-300 text-sm mb-4">
            Complete audit trail of all model changes, deployments, and access logs.
          </p>
          <Button variant="outline" size="sm">
            View Audit
          </Button>
        </Card>

        <Card 
          title="Compliance Reports" 
          icon={<FileText className="h-5 w-5 text-purple-400" />}
          gradient="from-purple-500/10 to-pink-500/10"
        >
          <p className="text-slate-300 text-sm mb-4">
            Generate compliance reports for regulatory requirements and governance.
          </p>
          <Button variant="outline" size="sm">
            Generate Report
          </Button>
        </Card>
      </div>

      <Card title="Recent Provenance Events" icon={<Activity className="h-5 w-5 text-slate-400" />}>
        <div className="space-y-4">
          {events.map((event) => (
            <div key={event.id} className="flex items-center space-x-4 p-4 bg-slate-800/30 rounded-xl border border-white/5">
              <div className={`w-10 h-10 ${getEventIconColor(event.type)} rounded-xl flex items-center justify-center`}>
                {event.icon}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-3 mb-1">
                  <h4 className="text-sm font-semibold text-white truncate">
                    {event.title}
                  </h4>
                  <div className={`px-2 py-1 rounded-lg border text-xs font-medium ${getStatusColor(event.status)}`}>
                    <span className="capitalize">{event.status}</span>
                  </div>
                </div>
                <p className="text-sm text-slate-400 mb-1">
                  {event.description}
                </p>
                <div className="flex items-center space-x-4 text-xs text-slate-500">
                  <span>{event.model}</span>
                  <span>•</span>
                  <span>{new Date(event.timestamp).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm" icon={Eye} />
                <Button variant="ghost" size="sm" icon={Download} />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-6 border-t border-white/10">
          <Button variant="outline" className="w-full">
            View All Events
          </Button>
        </div>
      </Card>
    </PageWrapper>
  )
}
