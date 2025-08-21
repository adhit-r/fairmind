"use client"

import { useState, useEffect } from 'react'
import React from 'react'
import { 
  FileText, 
  Brain, 
  Network, 
  Search, 
  Filter, 
  Eye, 
  Download, 
  Share, 
  Plus, 
  Settings, 
  RefreshCw, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Save, 
  Edit, 
  Trash2, 
  Copy, 
  Bookmark, 
  Tag, 
  Hash, 
  Link, 
  Unlink, 
  GitBranch, 
  GitCommit, 
  GitMerge, 
  GitPullRequest, 
  GitCompare, 
  GitFork, 
  X, 
  CheckCircle, 
  AlertTriangle, 
  Info, 
  HelpCircle, 
  Star, 
  Award, 
  Calendar, 
  MapPin, 
  UserCheck, 
  Scale, 
  ChevronRight, 
  ChevronDown, 
  Sparkles, 
  BarChart, 
  PieChart, 
  LineChart, 
  ArrowRight, 
  FileUp, 
  TestTube, 
  Play, 
  Pause, 
  Shield
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"

interface KnowledgeNode {
  id: string
  type: 'model' | 'dataset' | 'bias' | 'compliance' | 'security' | 'user'
  name: string
  description: string
  connections: string[]
  metadata: any
  position: { x: number; y: number }
}

interface KnowledgeConnection {
  id: string
  source: string
  target: string
  type: 'uses' | 'depends_on' | 'detects' | 'violates' | 'implements' | 'tests'
  strength: number
}

export default function KnowledgeGraphPage() {
  const [nodes, setNodes] = useState<KnowledgeNode[]>([])
  const [connections, setConnections] = useState<KnowledgeConnection[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [zoom, setZoom] = useState(1)

  useEffect(() => {
    loadKnowledgeGraph()
  }, [])

  const loadKnowledgeGraph = async () => {
    try {
      setLoading(true)
      
      // In a real implementation, this would come from the API
      // For now, we'll generate realistic knowledge graph data
      const datasets = await fairmindAPI.getAvailableDatasets()
      
      const mockNodes: KnowledgeNode[] = []
      const mockConnections: KnowledgeConnection[] = []
      
      // Create nodes for each dataset
      datasets.forEach((dataset, index) => {
        const datasetNode: KnowledgeNode = {
          id: `dataset-${index}`,
          type: 'dataset',
          name: dataset.name,
          description: dataset.description,
          connections: [],
          metadata: {
            samples: dataset.samples,
            columns: dataset.columns,
            created_date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString()
          },
          position: { x: Math.random() * 800, y: Math.random() * 600 }
        }
        mockNodes.push(datasetNode)
        
        // Create model node for each dataset
        const modelNode: KnowledgeNode = {
          id: `model-${index}`,
          type: 'model',
          name: `${dataset.name} Model`,
          description: `AI model trained on ${dataset.name}`,
          connections: [`dataset-${index}`],
          metadata: {
            framework: ['TensorFlow', 'PyTorch', 'Scikit-learn'][Math.floor(Math.random() * 3)],
            accuracy: Math.random() * 0.2 + 0.8,
            parameters: Math.floor(Math.random() * 1000000) + 1000
          },
          position: { x: Math.random() * 800, y: Math.random() * 600 }
        }
        mockNodes.push(modelNode)
        
        // Create bias node
        const biasNode: KnowledgeNode = {
          id: `bias-${index}`,
          type: 'bias',
          name: `${dataset.name} Bias Analysis`,
          description: `Bias detection results for ${dataset.name}`,
          connections: [`model-${index}`],
          metadata: {
            bias_score: Math.random() * 0.3 + 0.7,
            fairness_metrics: ['demographic_parity', 'equalized_odds', 'individual_fairness'],
            last_analyzed: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
          },
          position: { x: Math.random() * 800, y: Math.random() * 600 }
        }
        mockNodes.push(biasNode)
        
        // Create connections
        mockConnections.push({
          id: `conn-${index}-1`,
          source: `model-${index}`,
          target: `dataset-${index}`,
          type: 'uses',
          strength: 0.9
        })
        
        mockConnections.push({
          id: `conn-${index}-2`,
          source: `bias-${index}`,
          target: `model-${index}`,
          type: 'detects',
          strength: 0.8
        })
      })
      
      // Add compliance and security nodes
      const complianceNode: KnowledgeNode = {
        id: 'compliance-1',
        type: 'compliance',
        name: 'GDPR Compliance',
        description: 'General Data Protection Regulation compliance framework',
        connections: mockNodes.filter(n => n.type === 'model').map(n => n.id),
        metadata: {
          framework: 'GDPR',
          status: 'active',
          last_audit: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
        },
        position: { x: 400, y: 100 }
      }
      mockNodes.push(complianceNode)
      
      const securityNode: KnowledgeNode = {
        id: 'security-1',
        type: 'security',
        name: 'OWASP Security',
        description: 'OWASP AI/LLM Security Framework',
        connections: mockNodes.filter(n => n.type === 'model').map(n => n.id),
        metadata: {
          framework: 'OWASP AI/LLM',
          vulnerabilities: Math.floor(Math.random() * 5),
          last_scan: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
        },
        position: { x: 600, y: 100 }
      }
      mockNodes.push(securityNode)
      
      // Add compliance and security connections
      mockNodes.filter(n => n.type === 'model').forEach(model => {
        mockConnections.push({
          id: `conn-compliance-${model.id}`,
          source: model.id,
          target: 'compliance-1',
          type: 'implements',
          strength: Math.random() * 0.3 + 0.7
        })
        
        mockConnections.push({
          id: `conn-security-${model.id}`,
          source: model.id,
          target: 'security-1',
          type: 'tests',
          strength: Math.random() * 0.3 + 0.7
        })
      })
      
      setNodes(mockNodes)
      setConnections(mockConnections)
    } catch (error) {
      console.error('Error loading knowledge graph:', error)
      setNodes([])
      setConnections([])
    } finally {
      setLoading(false)
    }
  }

  const filteredNodes = nodes.filter(node => {
    const matchesSearch = node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         node.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterType === 'all' || node.type === filterType
    return matchesSearch && matchesFilter
  })

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'model': return 'bg-blue-500'
      case 'dataset': return 'bg-green-500'
      case 'bias': return 'bg-red-500'
      case 'compliance': return 'bg-purple-500'
      case 'security': return 'bg-orange-500'
      case 'user': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'model': return Brain
      case 'dataset': return FileText
      case 'bias': return AlertTriangle
      case 'compliance': return Scale
      case 'security': return Shield
      case 'user': return UserCheck
      default: return Info
    }
  }

  const getConnectionColor = (type: string) => {
    switch (type) {
      case 'uses': return 'stroke-blue-500'
      case 'depends_on': return 'stroke-yellow-500'
      case 'detects': return 'stroke-red-500'
      case 'violates': return 'stroke-red-600'
      case 'implements': return 'stroke-green-500'
      case 'tests': return 'stroke-purple-500'
      default: return 'stroke-gray-500'
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-black text-gray-900 mb-2 flex items-center">
              <Network className="h-8 w-8 mr-3 text-blue-600" />
              AI Knowledge Graph
            </h1>
            <p className="text-lg font-bold text-gray-600 mb-4">
              Visualize relationships between models, datasets, bias detection, and compliance.
            </p>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-blue-100 border-2 border-black px-3 py-1 rounded-lg">
                <Network className="h-4 w-4 text-blue-800" />
                <span className="text-sm font-bold text-blue-800">{nodes.length} Nodes</span>
              </div>
              <div className="flex items-center space-x-2 bg-green-100 border-2 border-black px-3 py-1 rounded-lg">
                <Link className="h-4 w-4 text-green-800" />
                <span className="text-sm font-bold text-green-800">{connections.length} Connections</span>
              </div>
              <button 
                onClick={loadKnowledgeGraph}
                disabled={loading}
                className="flex items-center space-x-2 bg-white border-2 border-black px-3 py-1 rounded-lg hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 text-gray-700 ${loading ? 'animate-spin' : ''}`} />
                <span className="text-sm font-bold text-gray-700">Refresh</span>
              </button>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-gradient-to-br from-green-600 to-blue-600 rounded-lg border-2 border-black shadow-4px-4px-0px-black flex items-center justify-center">
              <Network className="h-10 w-10 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search nodes by name or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-300 rounded-lg font-bold focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-3 border-2 border-gray-300 rounded-lg font-bold focus:border-blue-500 focus:outline-none"
            >
              <option value="all">All Types</option>
              <option value="model">Models</option>
              <option value="dataset">Datasets</option>
              <option value="bias">Bias Analysis</option>
              <option value="compliance">Compliance</option>
              <option value="security">Security</option>
            </select>
            <button className="bg-blue-500 text-white border-2 border-black px-4 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
              <ZoomIn className="h-4 w-4 mr-2" />
              Zoom In
            </button>
            <button className="bg-blue-500 text-white border-2 border-black px-4 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
              <ZoomOut className="h-4 w-4 mr-2" />
              Zoom Out
            </button>
            <button className="bg-green-500 text-white border-2 border-black px-4 py-3 rounded-lg font-bold hover:bg-green-600 shadow-2px-2px-0px-black transition-all duration-200">
              <Plus className="h-4 w-4 mr-2" />
              Add Node
            </button>
          </div>
        </div>
      </div>

      {/* Knowledge Graph Visualization */}
      <div className="bg-white border-2 border-black rounded-lg p-6 shadow-4px-4px-0px-black">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-black text-gray-900">Knowledge Graph Visualization</h2>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-bold text-gray-600">Zoom: {Math.round(zoom * 100)}%</span>
                         <button className="bg-gray-100 border-2 border-black px-3 py-1 rounded-lg font-bold text-sm hover:bg-gray-200 shadow-2px-2px-0px-black transition-all duration-200">
               <RotateCcw className="h-4 w-4" />
             </button>
          </div>
        </div>

        {loading ? (
          <div className="h-96 bg-gray-100 rounded-lg animate-pulse flex items-center justify-center">
            <div className="text-center">
              <Network className="h-16 w-16 text-gray-400 mx-auto mb-4 animate-pulse" />
              <div className="text-gray-500 font-bold">Loading knowledge graph...</div>
            </div>
          </div>
        ) : (
          <div className="relative h-96 bg-gray-50 rounded-lg border-2 border-gray-200 overflow-hidden">
            {/* SVG Container for Graph */}
            <svg className="w-full h-full" viewBox="0 0 1000 600">
              {/* Connections */}
              {connections.map((connection) => {
                const sourceNode = nodes.find(n => n.id === connection.source)
                const targetNode = nodes.find(n => n.id === connection.target)
                
                if (!sourceNode || !targetNode) return null
                
                return (
                  <line
                    key={connection.id}
                    x1={sourceNode.position.x}
                    y1={sourceNode.position.y}
                    x2={targetNode.position.x}
                    y2={targetNode.position.y}
                    stroke={getConnectionColor(connection.type).replace('stroke-', '')}
                    strokeWidth={connection.strength * 3}
                    opacity={0.6}
                    markerEnd="url(#arrowhead)"
                  />
                )
              })}
              
              {/* Arrow marker */}
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="7"
                  refX="9"
                  refY="3.5"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                </marker>
              </defs>
              
              {/* Nodes */}
              {filteredNodes.map((node) => {
                const IconComponent = getNodeIcon(node.type)
                return (
                  <g key={node.id}>
                    <circle
                      cx={node.position.x}
                      cy={node.position.y}
                      r="30"
                      className={`${getNodeColor(node.type)} border-2 border-black cursor-pointer hover:opacity-80 transition-opacity`}
                      onClick={() => setSelectedNode(node)}
                    />
                    <foreignObject
                      x={node.position.x - 15}
                      y={node.position.y - 15}
                      width="30"
                      height="30"
                      className="pointer-events-none"
                    >
                      <div className="flex items-center justify-center w-full h-full">
                        <IconComponent className="h-4 w-4 text-white" />
                      </div>
                    </foreignObject>
                  </g>
                )
              })}
            </svg>
            
            {/* Node Labels */}
            <div className="absolute inset-0 pointer-events-none">
              {filteredNodes.map((node) => (
                <div
                  key={`label-${node.id}`}
                  className="absolute transform -translate-x-1/2 -translate-y-full"
                  style={{
                    left: node.position.x,
                    top: node.position.y - 40
                  }}
                >
                  <div className="bg-white border border-gray-300 rounded px-2 py-1 text-xs font-bold text-gray-700 whitespace-nowrap">
                    {node.name}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Node Details Modal */}
      {selectedNode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white border-2 border-black rounded-lg p-8 shadow-4px-4px-0px-black max-w-2xl w-full">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-black text-gray-900 flex items-center">
                <div className={`p-2 rounded-lg border-2 border-black ${getNodeColor(selectedNode.type)} mr-3`}>
                  {React.createElement(getNodeIcon(selectedNode.type), { className: "h-6 w-6 text-white" })}
                </div>
                {selectedNode.name}
              </h2>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-2 rounded-lg border-2 border-black hover:bg-gray-50 shadow-2px-2px-0px-black transition-all duration-200"
              >
                <X className="h-5 w-5 text-gray-700" />
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-black text-gray-900 mb-2">Description</h3>
                <p className="text-gray-700 font-bold">{selectedNode.description}</p>
              </div>

              <div>
                <h3 className="text-lg font-black text-gray-900 mb-2">Type</h3>
                <span className="inline-block px-3 py-1 bg-gray-100 border-2 border-black rounded-lg font-bold text-sm capitalize">
                  {selectedNode.type}
                </span>
              </div>

              <div>
                <h3 className="text-lg font-black text-gray-900 mb-2">Connections</h3>
                <div className="space-y-2">
                  {selectedNode.connections.map((connectionId) => {
                    const connectedNode = nodes.find(n => n.id === connectionId)
                    return connectedNode ? (
                      <div key={connectionId} className="flex items-center space-x-2 p-2 bg-gray-50 border-2 border-gray-200 rounded-lg">
                        <div className={`w-3 h-3 rounded-full ${getNodeColor(connectedNode.type)}`}></div>
                        <span className="font-bold text-gray-700">{connectedNode.name}</span>
                        <span className="text-sm font-bold text-gray-500 capitalize">({connectedNode.type})</span>
                      </div>
                    ) : null
                  })}
                </div>
              </div>

              {Object.keys(selectedNode.metadata).length > 0 && (
                <div>
                  <h3 className="text-lg font-black text-gray-900 mb-2">Metadata</h3>
                  <div className="space-y-2">
                    {Object.entries(selectedNode.metadata).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="font-bold text-gray-600 capitalize">{key.replace('_', ' ')}:</span>
                        <span className="font-black text-gray-900">
                          {typeof value === 'number' ? value.toLocaleString() : 
                           typeof value === 'boolean' ? (value ? 'Yes' : 'No') :
                           Array.isArray(value) ? value.join(', ') : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="mt-8 flex justify-center space-x-4">
              <button className="bg-blue-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-blue-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Eye className="h-4 w-4 mr-2" />
                View Details
              </button>
              <button className="bg-green-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-green-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Download className="h-4 w-4 mr-2" />
                Export
              </button>
              <button className="bg-purple-500 text-white border-2 border-black px-6 py-3 rounded-lg font-bold hover:bg-purple-600 shadow-2px-2px-0px-black transition-all duration-200">
                <Share className="h-4 w-4 mr-2" />
                Share
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
