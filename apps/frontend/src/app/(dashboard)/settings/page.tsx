'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/hooks/use-toast'
import { MlopsSettings } from '@/components/settings/MlopsSettings'
import { IconSettings, IconUser, IconBell, IconShield, IconAlertTriangle, IconActivity } from '@tabler/icons-react'
import { apiClient } from '@/lib/api/api-client';

interface UserSettings {
  email: string;
  notifications: boolean;
  autoRefresh: boolean;
  theme: string;
  language: string;
}

export default function SettingsPage() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [settings, setSettings] = useState<UserSettings>({
    email: '',
    notifications: true,
    autoRefresh: true,
    theme: 'light',
    language: 'en',
  })

  // Fetch settings on mount
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get('/api/v1/settings/')
        if (response.success && response.data) {
          setSettings(response.data as UserSettings)
        } else {
          // Fallback to defaults if API fails
          setSettings({
            email: 'user@example.com',
            notifications: true,
            autoRefresh: true,
            theme: 'light',
            language: 'en',
          })
        }
      } catch (err) {
        // Fallback to defaults on error
        setSettings({
          email: 'user@example.com',
          notifications: true,
          autoRefresh: true,
          theme: 'light',
          language: 'en',
        })
      } finally {
        setLoading(false)
      }
    }
    fetchSettings()
  }, [])

  const handleSave = async () => {
    try {
      setLoading(true)
      setError(null)

      await apiClient.put('/api/v1/settings/', settings)

      toast({
        title: "Settings saved",
        description: "Your settings have been updated successfully.",
      })
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to save settings')
      setError(error)
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account and application settings
        </p>
      </div>

      {error && (
        <Alert className="border-2 border-red-500 shadow-brutal">
          <IconAlertTriangle className="h-4 w-4" />
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      {loading && (
        <div className="space-y-4">
          <Skeleton className="h-64" />
        </div>
      )}

      {!loading && (
        <Tabs defaultValue="profile" className="space-y-4">
          <TabsList className="border-2 border-black">
            <TabsTrigger value="profile" className="border-r-2 border-black">
              <IconUser className="mr-2 h-4 w-4" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="notifications" className="border-r-2 border-black">
              <IconBell className="mr-2 h-4 w-4" />
              Notifications
            </TabsTrigger>
            <TabsTrigger value="security" className="border-r-2 border-black">
              <IconShield className="mr-2 h-4 w-4" />
              Security
            </TabsTrigger>
            <TabsTrigger value="mlops">
              <IconActivity className="mr-2 h-4 w-4" />
              MLOps
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card className="p-6 border-2 border-black shadow-brutal">
              <h3 className="text-lg font-bold mb-4">Profile Settings</h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={settings.email}
                    onChange={(e) => setSettings({ ...settings, email: e.target.value })}
                    className="border-2 border-black"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="language">Language</Label>
                  <Select
                    value={settings.language}
                    onValueChange={(value) => setSettings({ ...settings, language: value })}
                  >
                    <SelectTrigger className="border-2 border-black">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button variant="default" onClick={handleSave} disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="notifications">
            <Card className="p-6 border-2 border-black shadow-brutal">
              <h3 className="text-lg font-bold mb-4">Notification Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="notifications">Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">
                      Receive email notifications for important events
                    </p>
                  </div>
                  <Switch
                    id="notifications"
                    checked={settings.notifications}
                    onCheckedChange={(checked) => setSettings({ ...settings, notifications: checked })}
                    disabled={loading}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="auto-refresh">Auto Refresh</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically refresh dashboard data
                    </p>
                  </div>
                  <Switch
                    id="auto-refresh"
                    checked={settings.autoRefresh}
                    onCheckedChange={(checked) => setSettings({ ...settings, autoRefresh: checked })}
                    disabled={loading}
                  />
                </div>
                <Button variant="default" onClick={handleSave} disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="security">
            <Card className="p-6 border-2 border-black shadow-brutal">
              <h3 className="text-lg font-bold mb-4">Security Settings</h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="current-password">Current Password</Label>
                  <Input
                    id="current-password"
                    type="password"
                    className="border-2 border-black"
                    disabled={loading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="new-password">New Password</Label>
                  <Input
                    id="new-password"
                    type="password"
                    className="border-2 border-black"
                    disabled={loading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm-password">Confirm New Password</Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    className="border-2 border-black"
                    disabled={loading}
                  />
                </div>
                <Button variant="default" onClick={handleSave} disabled={loading}>
                  {loading ? 'Updating...' : 'Update Password'}
                </Button>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="mlops">
            <MlopsSettings />
          </TabsContent>
        </Tabs>
      )}
    </div >
  )
}
