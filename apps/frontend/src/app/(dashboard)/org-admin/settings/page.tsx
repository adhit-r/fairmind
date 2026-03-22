'use client';

import React, { useEffect, useState } from 'react';
import { useOrg } from '@/context/OrgContext';
import { apiClient as api } from '@/lib/api/api-client';
import { IconCheck, IconX } from '@tabler/icons-react';

interface OrgSettings {
  id: string;
  name: string;
  slug: string;
  domain?: string;
  description?: string;
  logo_url?: string;
  billing_email?: string;
  is_public: boolean;
}

export default function OrgSettingsPage() {
  const { selectedOrg } = useOrg();
  const [settings, setSettings] = useState<OrgSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [domain, setDomain] = useState('');
  const [description, setDescription] = useState('');
  const [billingEmail, setBillingEmail] = useState('');
  const [isPublic, setIsPublic] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, [selectedOrg]);

  const fetchSettings = async () => {
    if (!selectedOrg) return;
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.get<OrgSettings>(
        `/api/v1/organizations/${selectedOrg.id}/settings`
      );
      const settingsData = response.data || response.data;
      if (response.success && settingsData) {
        setSettings(settingsData);
        setName(settingsData.name);
        setSlug(settingsData.slug);
        setDomain(settingsData.domain || '');
        setDescription(settingsData.description || '');
        setBillingEmail(settingsData.billing_email || '');
        setIsPublic(settingsData.is_public);
      } else {
        setError(response.error || 'Failed to fetch settings');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch settings';
      setError(errorMessage);
      console.error('Error fetching settings:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrg) return;

    try {
      setIsSaving(true);
      setSaveMessage(null);

      const response = await api.put<{ success: boolean }>(
        `/api/v1/organizations/${selectedOrg.id}/settings`,
        {
          name,
          slug,
          domain,
          description,
          billing_email: billingEmail,
          is_public: isPublic,
        }
      );

      if (response.success) {
        setSaveMessage('Settings saved successfully');
        setTimeout(() => setSaveMessage(null), 3000);
        await fetchSettings();
      } else {
        setError(response.error || 'Failed to save settings');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save settings';
      setError(errorMessage);
      console.error('Error saving settings:', err);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="mx-auto max-w-2xl">
          <div className="flex justify-center">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-black" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className="mb-8 border-b-4 border-black pb-6">
          <h1 className="text-4xl font-bold text-black">Organization Settings</h1>
          <p className="mt-2 text-gray-600">Manage your organization's information</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 rounded-lg border-2 border-red-800 bg-red-50 p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {saveMessage && (
          <div className="mb-6 flex items-center gap-2 rounded-lg border-2 border-green-800 bg-green-50 p-4">
            <IconCheck size={20} className="text-green-600" />
            <p className="text-green-800">{saveMessage}</p>
          </div>
        )}

        {/* Settings Form */}
        <form onSubmit={handleSave} className="rounded-lg border-4 border-black bg-white p-8 shadow-brutal-lg">
          {/* Organization Name */}
          <div className="mb-6">
            <label className="mb-2 block font-bold text-black">Organization Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded border-2 border-black px-4 py-2 text-black placeholder-gray-400"
              placeholder="My Organization"
              required
            />
          </div>

          {/* Slug */}
          <div className="mb-6">
            <label className="mb-2 block font-bold text-black">Organization Slug</label>
            <input
              type="text"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="w-full rounded border-2 border-black px-4 py-2 font-mono text-black placeholder-gray-400"
              placeholder="my-organization"
              required
            />
            <p className="mt-1 text-xs text-gray-600">Used in URLs and identifiers</p>
          </div>

          {/* Domain */}
          <div className="mb-6">
            <label className="mb-2 block font-bold text-black">Domain</label>
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full rounded border-2 border-black px-4 py-2 text-black placeholder-gray-400"
              placeholder="example.com"
            />
            <p className="mt-1 text-xs text-gray-600">For email domain verification</p>
          </div>

          {/* Description */}
          <div className="mb-6">
            <label className="mb-2 block font-bold text-black">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded border-2 border-black px-4 py-2 text-black placeholder-gray-400"
              placeholder="Organization description"
              rows={4}
            />
          </div>

          {/* Billing Email */}
          <div className="mb-6">
            <label className="mb-2 block font-bold text-black">Billing Email</label>
            <input
              type="email"
              value={billingEmail}
              onChange={(e) => setBillingEmail(e.target.value)}
              className="w-full rounded border-2 border-black px-4 py-2 text-black placeholder-gray-400"
              placeholder="billing@example.com"
            />
          </div>

          {/* Public Organization */}
          <div className="mb-8 flex items-center gap-3 rounded-lg border-2 border-gray-300 bg-gray-50 p-4">
            <input
              type="checkbox"
              id="isPublic"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
              className="h-5 w-5 cursor-pointer border-2 border-black"
            />
            <label htmlFor="isPublic" className="cursor-pointer flex-1 font-bold text-black">
              Make organization publicly discoverable
            </label>
            <div className="flex items-center gap-1">
              {isPublic ? (
                <>
                  <IconCheck size={16} className="text-green-600" />
                  <span className="text-xs font-bold text-green-600">Public</span>
                </>
              ) : (
                <>
                  <IconX size={16} className="text-gray-400" />
                  <span className="text-xs font-bold text-gray-600">Private</span>
                </>
              )}
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isSaving}
              className="rounded-lg bg-black px-6 py-2 font-bold text-white transition-all hover:shadow-brutal-lg disabled:opacity-50 active:translate-y-1"
            >
              {isSaving ? 'Saving...' : 'Save Settings'}
            </button>
            <button
              type="button"
              onClick={() => fetchSettings()}
              className="rounded-lg border-2 border-black px-6 py-2 font-bold text-black transition-all hover:bg-gray-50"
            >
              Reset
            </button>
          </div>
        </form>

        {/* Organization Info Box */}
        <div className="mt-8 rounded-lg border-4 border-black bg-white p-6 shadow-brutal-lg">
          <h3 className="mb-4 font-bold text-black">Organization Information</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between border-b border-gray-200 pb-2">
              <span className="text-gray-600">Organization ID</span>
              <span className="font-mono font-bold text-black">{selectedOrg?.id}</span>
            </div>
            <div className="flex justify-between border-b border-gray-200 pb-2">
              <span className="text-gray-600">Owner</span>
              <span className="font-bold text-black">{selectedOrg?.owner_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Created</span>
              <span className="font-bold text-black">
                {selectedOrg?.created_at
                  ? new Date(selectedOrg.created_at).toLocaleDateString()
                  : '—'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
