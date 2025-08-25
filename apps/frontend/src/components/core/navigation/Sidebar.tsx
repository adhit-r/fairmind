'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  Shield, 
  BarChart3, 
  Database, 
  Eye, 
  Play, 
  Upload, 
  FileText, 
  Brain,
  Settings,
  User,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Users,
  Activity,
  Clock,
  Plus,
  Search,
  Filter,
  Sun,
  RefreshCw
} from 'lucide-react'

const navigationSections = [
  {
    title: 'Overview',
    items: [
      {
        name: 'Dashboard',
        href: '/',
        icon: BarChart3
      }
    ]
  },
  {
    title: 'Model Management',
    items: [
      {
        name: 'Model Registry',
        href: '/model-registry',
        icon: Database
      },
      {
        name: 'Upload Model',
        href: '/model-upload',
        icon: Upload
      },
      {
        name: 'Model Testing',
        href: '/model-testing',
        icon: Play
      }
    ]
  },
  {
    title: 'Analysis & Compliance',
    items: [
      {
        name: 'Bias Detection',
        href: '/bias-detection',
        icon: Eye
      },
      {
        name: 'Security Testing',
        href: '/security-testing',
        icon: Shield
      },
      {
        name: 'AI BOM',
        href: '/ai-bom',
        icon: Brain
      }
    ]
  },
  {
    title: 'Documentation',
    items: [
      {
        name: 'Model Provenance',
        href: '/provenance',
        icon: FileText
      }
    ]
  }
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b border-gray-700">
        <div className="flex items-center space-x-2">
          <Shield className="h-8 w-8 text-yellow-500" />
          <span className="text-xl font-bold text-white">FairMind</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-6">
        {navigationSections.map((section) => (
          <div key={section.title}>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-3">
              {section.title}
            </h3>
            <div className="space-y-1">
              {section.items.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-yellow-600 text-white shadow-lg'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    <item.icon className="h-5 w-5" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
            <User className="h-4 w-4 text-gray-300" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">Admin</p>
            <p className="text-xs text-gray-400 truncate">admin@fairmind.xyz</p>
          </div>
          <button className="p-1 rounded hover:bg-gray-700 transition-colors">
            <Settings className="h-4 w-4 text-gray-400" />
          </button>
        </div>
      </div>
    </div>
  )
}
