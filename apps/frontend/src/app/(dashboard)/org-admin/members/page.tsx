'use client';

import React, { useEffect, useState } from 'react';
import { useOrg } from '@/context/OrgContext';
import { apiClient as api } from '@/lib/api/api-client';
import { IconPlus, IconTrash, IconCheck, IconX } from '@tabler/icons-react';

interface OrgMember {
  id: string;
  email: string;
  name: string | null;
  role: string;
  is_active: boolean;
  joined_at: string | null;
}

export default function OrgMembersPage() {
  const { selectedOrg } = useOrg();
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('analyst');
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);

  useEffect(() => {
    fetchMembers();
  }, [selectedOrg]);

  const fetchMembers = async () => {
    if (!selectedOrg) return;
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.get<{ members: OrgMember[] }>(
        `/api/v1/organizations/${selectedOrg.id}/members`
      );
      if (response.success && response.data) {
        setMembers(response.data.members);
      } else {
        setError(response.error || 'Failed to fetch members');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch members';
      setError(errorMessage);
      console.error('Error fetching members:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrg || !inviteEmail) return;

    try {
      setInviteLoading(true);
      setInviteError(null);

      const response = await api.post<{ success: boolean }>(
        `/api/v1/organizations/${selectedOrg.id}/members/invite`,
        {
          email: inviteEmail,
          role: inviteRole,
        }
      );

      if (response.success) {
        setInviteEmail('');
        setInviteRole('analyst');
        setShowInviteForm(false);
        await fetchMembers();
      } else {
        setInviteError(response.error || 'Failed to send invitation');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send invitation';
      setInviteError(errorMessage);
      console.error('Error inviting member:', err);
    } finally {
      setInviteLoading(false);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!selectedOrg || !confirm('Remove this member from the organization?')) return;

    try {
      const response = await api.delete(
        `/api/v1/organizations/${selectedOrg.id}/members/${memberId}`
      );

      if (response.success) {
        await fetchMembers();
      } else {
        alert('Failed to remove member');
      }
    } catch (err) {
      console.error('Error removing member:', err);
      alert('Failed to remove member');
    }
  };

  const getRoleColor = (role: string) => {
    const colors: Record<string, string> = {
      admin: 'bg-red-100 text-red-800 border-red-800',
      analyst: 'bg-blue-100 text-blue-800 border-blue-800',
      viewer: 'bg-gray-100 text-gray-800 border-gray-800',
    };
    return colors[role] || 'bg-gray-100 text-gray-800 border-gray-800';
  };

  const formatDate = (date: string | null) => {
    if (!date) return '—';
    return new Date(date).toLocaleDateString();
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between border-b-4 border-black pb-6">
          <div>
            <h1 className="text-4xl font-bold text-black">Organization Members</h1>
            <p className="mt-2 text-gray-600">Manage team members and their roles</p>
          </div>
          <button
            onClick={() => setShowInviteForm(!showInviteForm)}
            className="flex items-center gap-2 rounded-lg bg-black px-4 py-2 font-bold text-white transition-all hover:shadow-brutal-lg active:translate-y-1"
          >
            <IconPlus size={20} />
            {showInviteForm ? 'Cancel' : 'Invite Member'}
          </button>
        </div>

        {/* Invite Form */}
        {showInviteForm && (
          <div className="mb-8 rounded-lg border-4 border-black bg-white p-6 shadow-brutal-lg">
            <form onSubmit={handleInvite}>
              <div className="mb-4">
                <label className="mb-2 block font-bold text-black">Email Address</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full rounded border-2 border-black px-4 py-2 font-mono text-black placeholder-gray-400"
                  placeholder="user@example.com"
                  required
                />
              </div>

              <div className="mb-6">
                <label className="mb-2 block font-bold text-black">Role</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full rounded border-2 border-black px-4 py-2 font-bold text-black"
                >
                  <option value="viewer">Viewer</option>
                  <option value="analyst">Analyst</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              {inviteError && (
                <div className="mb-4 rounded-lg border-2 border-red-800 bg-red-50 p-3">
                  <p className="text-sm text-red-800">{inviteError}</p>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={inviteLoading}
                  className="rounded-lg bg-black px-6 py-2 font-bold text-white transition-all hover:shadow-brutal-lg disabled:opacity-50"
                >
                  {inviteLoading ? 'Sending...' : 'Send Invitation'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowInviteForm(false);
                    setInviteError(null);
                  }}
                  className="rounded-lg border-2 border-black px-6 py-2 font-bold text-black transition-all hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Members List */}
        {isLoading ? (
          <div className="flex justify-center">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-black" />
          </div>
        ) : error ? (
          <div className="rounded-lg border-2 border-red-800 bg-red-50 p-4">
            <p className="text-red-800">Error: {error}</p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border-4 border-black shadow-brutal-lg">
            <table className="w-full">
              <thead className="border-b-4 border-black bg-gray-100">
                <tr>
                  <th className="px-6 py-4 text-left font-bold text-black">Name</th>
                  <th className="px-6 py-4 text-left font-bold text-black">Email</th>
                  <th className="px-6 py-4 text-left font-bold text-black">Role</th>
                  <th className="px-6 py-4 text-left font-bold text-black">Status</th>
                  <th className="px-6 py-4 text-left font-bold text-black">Joined</th>
                  <th className="px-6 py-4 text-left font-bold text-black">Actions</th>
                </tr>
              </thead>
              <tbody>
                {members.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-600">
                      No members found
                    </td>
                  </tr>
                ) : (
                  members.map((member) => (
                    <tr key={member.id} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-6 py-4 font-semibold text-black">
                        {member.name || '—'}
                      </td>
                      <td className="px-6 py-4 font-mono text-gray-600">{member.email}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-block rounded border-2 px-3 py-1 text-sm font-bold ${getRoleColor(
                            member.role
                          )}`}
                        >
                          {member.role}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          {member.is_active ? (
                            <>
                              <IconCheck size={20} className="text-green-600" />
                              <span className="font-semibold text-green-600">Active</span>
                            </>
                          ) : (
                            <>
                              <IconX size={20} className="text-red-600" />
                              <span className="font-semibold text-red-600">Inactive</span>
                            </>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-600">{formatDate(member.joined_at)}</td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => handleRemoveMember(member.id)}
                          className="flex items-center gap-2 rounded bg-red-600 px-3 py-1 text-sm font-bold text-white transition-all hover:bg-red-700 active:translate-y-1"
                        >
                          <IconTrash size={16} />
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
