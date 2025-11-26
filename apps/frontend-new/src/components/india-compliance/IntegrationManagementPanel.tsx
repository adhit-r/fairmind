'use client'

import React, { useState } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import * as AlertDialog from '@radix-ui/react-alert-dialog'
import {
  Plug,
  Plus,
  Trash2,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
  Loader2,
} from 'lucide-react'

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

interface Integration {
  id: string
  integration_name: string
  status: 'connected' | 'disconnected' | 'error' | 'pending'
  last_sync?: string
  created_at: string
}

interface IntegrationManagementPanelProps {
  integrations: Integration[]
  onConnect?: (integrationName: string, credentials: Record<string, string>) => Promise<void>
  onDisconnect?: (integrationId: string) => Promise<void>
  onSync?: (integrationId: string) => Promise<void>
}

const AVAILABLE_INTEGRATIONS = [
  {
    name: 'onetrust',
    label: 'OneTrust',
    description: 'Consent and privacy data management',
    fields: [
      { name: 'api_key', label: 'API Key', type: 'password' },
      { name: 'org_id', label: 'Organization ID', type: 'text' },
    ],
  },
  {
    name: 'securiti',
    label: 'Securiti.ai',
    description: 'Data discovery and classification',
    fields: [
      { name: 'api_key', label: 'API Key', type: 'password' },
      { name: 'tenant_id', label: 'Tenant ID', type: 'text' },
    ],
  },
  {
    name: 'sprinto',
    label: 'Sprinto',
    description: 'Security controls and audit evidence',
    fields: [{ name: 'api_key', label: 'API Key', type: 'password' }],
  },
  {
    name: 'mlflow',
    label: 'MLflow',
    description: 'Model metadata and versioning',
    fields: [
      { name: 'tracking_uri', label: 'Tracking URI', type: 'text' },
      { name: 'api_key', label: 'API Key', type: 'password' },
    ],
  },
  {
    name: 'aws',
    label: 'AWS',
    description: 'Data residency and cloud storage',
    fields: [
      { name: 'access_key', label: 'Access Key', type: 'password' },
      { name: 'secret_key', label: 'Secret Key', type: 'password' },
      { name: 'region', label: 'Region', type: 'text' },
    ],
  },
]

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'connected':
      return <CheckCircle className="h-5 w-5 text-green-600" />
    case 'disconnected':
      return <AlertCircle className="h-5 w-5 text-gray-400" />
    case 'error':
      return <AlertCircle className="h-5 w-5 text-red-600" />
    case 'pending':
      return <Clock className="h-5 w-5 text-blue-600" />
    default:
      return <AlertCircle className="h-5 w-5 text-gray-400" />
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'connected':
      return 'bg-green-100 text-green-800'
    case 'disconnected':
      return 'bg-gray-100 text-gray-800'
    case 'error':
      return 'bg-red-100 text-red-800'
    case 'pending':
      return 'bg-blue-100 text-blue-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

export const IntegrationManagementPanel: React.FC<IntegrationManagementPanelProps> = ({
  integrations,
  onConnect,
  onDisconnect,
  onSync,
}) => {
  const [isConnecting, setIsConnecting] = useState(false)
  const [isSyncing, setIsSyncing] = useState<string | null>(null)
  const [isDisconnecting, setIsDisconnecting] = useState<string | null>(null)
  const [selectedIntegration, setSelectedIntegration] = useState<string | null>(null)
  const [credentials, setCredentials] = useState<Record<string, string>>({})
  const [disconnectId, setDisconnectId] = useState<string | null>(null)

  const connectedIntegrations = integrations.filter(i => i.status === 'connected')
  const availableIntegrations = AVAILABLE_INTEGRATIONS.filter(
    ai => !connectedIntegrations.some(ci => ci.integration_name === ai.name)
  )

  const handleConnect = async () => {
    if (!selectedIntegration || !onConnect) return

    try {
      setIsConnecting(true)
      await onConnect(selectedIntegration, credentials)
      setSelectedIntegration(null)
      setCredentials({})
    } catch (error) {
      console.error('Connection failed:', error)
    } finally {
      setIsConnecting(false)
    }
  }

  const handleSync = async (integrationId: string) => {
    if (!onSync) return

    try {
      setIsSyncing(integrationId)
      await onSync(integrationId)
    } catch (error) {
      console.error('Sync failed:', error)
    } finally {
      setIsSyncing(null)
    }
  }

  const handleDisconnect = async () => {
    if (!disconnectId || !onDisconnect) return

    try {
      setIsDisconnecting(disconnectId)
      await onDisconnect(disconnectId)
      setDisconnectId(null)
    } catch (error) {
      console.error('Disconnect failed:', error)
    } finally {
      setIsDisconnecting(null)
    }
  }

  const selectedIntegrationConfig = AVAILABLE_INTEGRATIONS.find(
    ai => ai.name === selectedIntegration
  )

  return (
    <div className="space-y-6">
      {/* Connected Integrations */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Connected Integrations</CardTitle>
              <CardDescription>
                Manage your connected compliance and governance tools
              </CardDescription>
            </div>
            <Dialog>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  Add Integration
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Connect New Integration</DialogTitle>
                  <DialogDescription>
                    Select an integration and provide your credentials
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                  {/* Integration Selection */}
                  <div>
                    <Label htmlFor="integration-select">Integration</Label>
                    <Select value={selectedIntegration || ''} onValueChange={setSelectedIntegration}>
                      <SelectTrigger id="integration-select">
                        <SelectValue placeholder="Select an integration" />
                      </SelectTrigger>
                      <SelectContent>
                        {availableIntegrations.map(integration => (
                          <SelectItem key={integration.name} value={integration.name}>
                            {integration.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Credentials Form */}
                  {selectedIntegrationConfig && (
                    <div className="space-y-3">
                      <p className="text-sm text-gray-600">{selectedIntegrationConfig.description}</p>
                      {selectedIntegrationConfig.fields.map(field => (
                        <div key={field.name}>
                          <Label htmlFor={field.name}>{field.label}</Label>
                          <Input
                            id={field.name}
                            type={field.type}
                            placeholder={`Enter ${field.label.toLowerCase()}`}
                            value={credentials[field.name] || ''}
                            onChange={e =>
                              setCredentials({
                                ...credentials,
                                [field.name]: e.target.value,
                              })
                            }
                          />
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-4">
                    <Button
                      variant="noShadow"
                      onClick={() => {
                        setSelectedIntegration(null)
                        setCredentials({})
                      }}
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleConnect}
                      disabled={isConnecting || !selectedIntegration}
                      className="flex-1 gap-2"
                    >
                      {isConnecting && <Loader2 className="h-4 w-4 animate-spin" />}
                      Connect
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {connectedIntegrations.length === 0 ? (
            <div className="text-center py-8">
              <Plug className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No integrations connected yet</p>
              <p className="text-sm text-gray-400">Add your first integration to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {connectedIntegrations.map(integration => (
                <div
                  key={integration.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3 flex-1">
                    <div className="flex-shrink-0">{getStatusIcon(integration.status)}</div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-sm">
                        {AVAILABLE_INTEGRATIONS.find(ai => ai.name === integration.integration_name)
                          ?.label || integration.integration_name}
                      </h4>
                      <p className="text-xs text-gray-600">
                        {integration.last_sync
                          ? `Last synced: ${formatDate(integration.last_sync)}`
                          : 'Never synced'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge className={getStatusColor(integration.status)}>
                      {integration.status.replace('_', ' ').toUpperCase()}
                    </Badge>

                    <Button
                      variant="noShadow"
                      size="sm"
                      onClick={() => handleSync(integration.id)}
                      disabled={isSyncing === integration.id}
                      className="gap-1"
                    >
                      {isSyncing === integration.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                      Sync
                    </Button>

                    <AlertDialog.Root open={disconnectId === integration.id} onOpenChange={(open) => !open && setDisconnectId(null)}>
                      <AlertDialog.Trigger asChild>
                        <Button
                          variant="noShadow"
                          size="sm"
                          onClick={() => setDisconnectId(integration.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </AlertDialog.Trigger>
                      <AlertDialog.Portal>
                        <AlertDialog.Overlay className="fixed inset-0 z-50 bg-black/50" />
                        <AlertDialog.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-sm translate-x-[-50%] translate-y-[-50%] rounded-lg border bg-white p-6 shadow-lg">
                          <AlertDialog.Title className="font-semibold">Disconnect Integration?</AlertDialog.Title>
                          <AlertDialog.Description className="mt-2 text-sm text-gray-600">
                            This will disconnect{' '}
                            {AVAILABLE_INTEGRATIONS.find(ai => ai.name === integration.integration_name)
                              ?.label || integration.integration_name}{' '}
                            and stop syncing data from this source.
                          </AlertDialog.Description>
                          <div className="mt-6 flex gap-2 justify-end">
                            <AlertDialog.Cancel asChild>
                              <Button variant="noShadow" size="sm">Cancel</Button>
                            </AlertDialog.Cancel>
                            <Button
                              variant="default"
                              size="sm"
                              onClick={handleDisconnect}
                              disabled={isDisconnecting === integration.id}
                              className="gap-2"
                            >
                              {isDisconnecting === integration.id && (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              )}
                              Disconnect
                            </Button>
                          </div>
                        </AlertDialog.Content>
                      </AlertDialog.Portal>
                    </AlertDialog.Root>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Integration Status Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Integration Status</CardTitle>
          <CardDescription>Overview of all available integrations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {AVAILABLE_INTEGRATIONS.map(integration => {
              const isConnected = connectedIntegrations.some(
                ci => ci.integration_name === integration.name
              )
              return (
                <div
                  key={integration.name}
                  className={`p-4 rounded-lg border-2 transition-colors ${
                    isConnected
                      ? 'border-green-200 bg-green-50'
                      : 'border-gray-200 bg-gray-50 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold text-sm">{integration.label}</h4>
                      <p className="text-xs text-gray-600 mt-1">{integration.description}</p>
                    </div>
                    {isConnected && <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />}
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default IntegrationManagementPanel
