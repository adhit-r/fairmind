/**
 * Role Management Page
 *
 * Admin interface for managing user roles and permissions in FairMind.
 * Displays available roles and their associated permissions.
 */

"use client";

import { useState, useEffect } from "react";

interface RolePermission {
  role: string;
  description: string;
  permissions: string[];
  color: string;
}

const ROLES_DATA: RolePermission[] = [
  {
    role: "admin",
    description: "Full access to FairMind platform",
    color: "border-red-800 bg-red-50",
    permissions: [
      "model:read",
      "model:write",
      "model:delete",
      "reports:create",
      "reports:read",
      "reports:delete",
      "compliance:manage",
      "users:manage",
      "roles:manage",
      "audit:view",
    ],
  },
  {
    role: "analyst",
    description: "Can create and analyze bias detection models",
    color: "border-blue-800 bg-blue-50",
    permissions: [
      "model:read",
      "model:write",
      "reports:create",
      "reports:read",
      "compliance:view",
    ],
  },
  {
    role: "viewer",
    description: "Read-only access to models and reports",
    color: "border-gray-800 bg-gray-50",
    permissions: ["model:read", "reports:read", "compliance:view"],
  },
];

export default function AdminRolesPage() {
  const [selectedRole, setSelectedRole] = useState<RolePermission | null>(
    ROLES_DATA[0]
  );

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8 border-b-4 border-black pb-6">
          <h1 className="text-4xl font-bold text-black">Role Management</h1>
          <p className="mt-2 text-gray-600">
            Define and manage user roles and permissions
          </p>
        </div>

        {/* Content */}
        <div className="grid gap-8 md:grid-cols-3">
          {/* Role List */}
          <div className="md:col-span-1">
            <div className="space-y-3">
              {ROLES_DATA.map((role) => (
                <button
                  key={role.role}
                  onClick={() => setSelectedRole(role)}
                  className={`w-full rounded-lg border-2 p-4 text-left transition-all ${
                    selectedRole?.role === role.role
                      ? `${role.color} border-2 shadow-brutal-lg`
                      : "border-gray-300 bg-white hover:border-black"
                  }`}
                >
                  <h3 className="font-bold text-black capitalize">{role.role}</h3>
                  <p className="mt-1 text-sm text-gray-600">
                    {role.description}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Role Details */}
          <div className="md:col-span-2">
            {selectedRole && (
              <div
                className={`rounded-lg border-4 border-black p-8 shadow-brutal-lg ${selectedRole.color}`}
              >
                <h2 className="text-3xl font-bold text-black capitalize">
                  {selectedRole.role}
                </h2>
                <p className="mt-3 text-gray-700">{selectedRole.description}</p>

                <div className="mt-8">
                  <h3 className="mb-4 text-xl font-bold text-black">
                    Permissions
                  </h3>
                  <div className="grid gap-2 md:grid-cols-2">
                    {selectedRole.permissions.map((permission) => (
                      <div
                        key={permission}
                        className="flex items-center gap-3 rounded-lg border-2 border-black bg-white p-3"
                      >
                        <div className="h-4 w-4 rounded border-2 border-black bg-black" />
                        <span className="font-semibold text-black">
                          {permission}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Info Box */}
                <div className="mt-8 rounded-lg border-2 border-black bg-white p-4">
                  <p className="text-sm text-gray-700">
                    <strong className="text-black">Note:</strong> Roles are
                    managed in Authentik. To modify roles and permissions,
                    visit the Authentik Admin Interface and update group
                    permissions.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Role Assignment Guide */}
        <div className="mt-12 space-y-8">
          <div className="rounded-lg border-4 border-black bg-white p-8 shadow-brutal-lg">
            <h2 className="mb-4 text-2xl font-bold text-black">
              Role Assignment Guide
            </h2>

            <div className="space-y-6">
              <div>
                <h3 className="mb-2 font-bold text-black">
                  How are roles assigned?
                </h3>
                <p className="text-gray-700">
                  Roles are assigned to users through Authentik groups. When a
                  user logs in, their roles are automatically synced from
                  Authentik to FairMind based on their group membership.
                </p>
              </div>

              <div>
                <h3 className="mb-2 font-bold text-black">
                  To assign roles to a user:
                </h3>
                <ol className="list-inside list-decimal space-y-2 text-gray-700">
                  <li>Go to the Authentik Admin Interface</li>
                  <li>Navigate to Directory &gt; Groups</li>
                  <li>Select the appropriate role group (admin, analyst, viewer)</li>
                  <li>Add the user to the group</li>
                  <li>The user's roles will be updated on their next login</li>
                </ol>
              </div>

              <div>
                <h3 className="mb-2 font-bold text-black">Authentik Link</h3>
                <a
                  href={process.env.NEXT_PUBLIC_AUTHENTIK_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block rounded-lg bg-black px-4 py-2 font-bold text-white hover:shadow-brutal-lg"
                >
                  Open Authentik Admin Interface
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
