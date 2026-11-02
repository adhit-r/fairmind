'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useOrg } from '@/context/OrgContext';
import { IconUsers, IconKey, IconSettings, IconClipboardList } from '@tabler/icons-react';

export default function OrgAdminPage() {
  const { selectedOrg } = useOrg();
  const router = useRouter();

  if (!selectedOrg) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="mx-auto max-w-4xl">
          <div className="rounded-lg border-2 border-gray-300 bg-gray-50 p-6 text-center">
            <p className="text-gray-600">Loading organization...</p>
          </div>
        </div>
      </div>
    );
  }

  const adminCards = [
    {
      id: 'members',
      title: 'Members',
      description: 'Manage team members and roles',
      icon: IconUsers,
      href: '/org-admin/members',
      color: 'border-[var(--fm-line)]',
    },
    {
      id: 'roles',
      title: 'Roles',
      description: 'Create and manage organization roles',
      icon: IconKey,
      href: '/org-admin/roles',
      color: 'border-[var(--fm-line)]',
    },
    {
      id: 'settings',
      title: 'Settings',
      description: 'Organization settings and domain',
      icon: IconSettings,
      href: '/org-admin/settings',
      color: 'border-[var(--fm-line)]',
    },
    {
      id: 'audit-log',
      title: 'Audit Log',
      description: 'View organization activity',
      icon: IconClipboardList,
      href: '/org-admin/audit-log',
      color: 'border-[var(--fm-line)]',
    },
  ];

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8 border-b border-[var(--fm-line)] pb-6">
          <h1 className="text-[30px] font-semibold tracking-[-.03em] text-black">{selectedOrg.name}</h1>
          <p className="mt-2 text-gray-600">Organization Administration</p>
        </div>

        {/* Admin Cards Grid */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {adminCards.map((card) => {
            const Icon = card.icon;
            return (
              <button
                key={card.id}
                onClick={() => router.push(card.href)}
                className="flex flex-col items-start p-6 transition-all fm-card"
              >
                <div className="mb-4 flex items-center gap-3">
                  <Icon size={28} className="text-black" strokeWidth={3} />
                  <h2 className="text-xl font-bold text-black">{card.title}</h2>
                </div>
                <p className="mb-6 text-sm text-gray-600">{card.description}</p>
                <div className="mt-auto flex items-center gap-2 text-black font-bold">
                  <span>Manage</span>
                  <span>→</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Organization Info Box */}
        <div className="mt-12 p-6 fm-card">
          <h3 className="mb-4 font-bold text-black">Organization Details</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm text-gray-600">Organization ID</p>
              <p className="font-mono text-black">{selectedOrg.id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Created</p>
              <p className="text-black">{new Date(selectedOrg.created_at).toLocaleDateString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Your Role</p>
              <p className="font-bold text-black capitalize">{selectedOrg.role}</p>
            </div>
            {selectedOrg.domain && (
              <div>
                <p className="text-sm text-gray-600">Domain</p>
                <p className="text-black">{selectedOrg.domain}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
