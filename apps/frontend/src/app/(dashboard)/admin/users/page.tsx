/**
 * User Management Page
 *
 * Admin interface for managing FairMind users.
 * Displays user list, roles, last login, and actions.
 */

"use client";

import { useState, useEffect } from "react";
import { apiClient as api } from "@/lib/api/api-client";
import { IconPlus, IconTrash, IconCheck, IconX } from "@tabler/icons-react";

interface User {
  id: string;
  email: string;
  username: string;
  name: string;
  roles: string[];
  is_active: boolean;
  last_login: string | null;
  created_at: string;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showInviteModal, setShowInviteModal] = useState(false);

  // Fetch users on mount
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setIsLoading(true);
        const response = await api.get<{ users: User[] }>(
          "/api/v1/auth/users"
        );
        setUsers(response.users || []);
        setError(null);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to fetch users";
        setError(errorMessage);
        console.error("Error fetching users:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsers();
  }, []);

  const formatDate = (date: string | null) => {
    if (!date) return "Never";
    return new Date(date).toLocaleDateString();
  };

  const getRoleColor = (role: string) => {
    const colors: Record<string, string> = {
      admin: "bg-red-100 text-red-800 border-red-800",
      analyst: "bg-blue-100 text-blue-800 border-blue-800",
      viewer: "bg-gray-100 text-gray-800 border-gray-800",
    };
    return colors[role] || "bg-gray-100 text-gray-800 border-gray-800";
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between border-b-4 border-black pb-6">
          <div>
            <h1 className="text-4xl font-bold text-black">User Management</h1>
            <p className="mt-2 text-gray-600">
              Manage FairMind users, roles, and permissions
            </p>
          </div>
          <button
            onClick={() => setShowInviteModal(true)}
            className="flex items-center gap-2 rounded-lg bg-black px-4 py-2 font-bold text-white transition-all hover:shadow-brutal-lg"
          >
            <IconPlus size={20} />
            Invite User
          </button>
        </div>

        {/* Content */}
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
                  <th className="px-6 py-4 text-left font-bold text-black">
                    Name
                  </th>
                  <th className="px-6 py-4 text-left font-bold text-black">
                    Email
                  </th>
                  <th className="px-6 py-4 text-left font-bold text-black">
                    Roles
                  </th>
                  <th className="px-6 py-4 text-left font-bold text-black">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left font-bold text-black">
                    Last Login
                  </th>
                  <th className="px-6 py-4 text-left font-bold text-black">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-600">
                      No users found
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr
                      key={user.id}
                      className="border-b border-gray-200 hover:bg-gray-50"
                    >
                      <td className="px-6 py-4 font-semibold text-black">
                        {user.name || user.username}
                      </td>
                      <td className="px-6 py-4 text-gray-600">{user.email}</td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-2">
                          {user.roles.map((role) => (
                            <span
                              key={role}
                              className={`rounded border-2 px-3 py-1 text-sm font-bold ${getRoleColor(
                                role
                              )}`}
                            >
                              {role}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          {user.is_active ? (
                            <>
                              <IconCheck size={20} className="text-green-600" />
                              <span className="text-green-600 font-semibold">
                                Active
                              </span>
                            </>
                          ) : (
                            <>
                              <IconX size={20} className="text-red-600" />
                              <span className="text-red-600 font-semibold">
                                Inactive
                              </span>
                            </>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-600">
                        {formatDate(user.last_login)}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => setSelectedUser(user)}
                          className="rounded bg-blue-600 px-3 py-1 text-sm font-bold text-white hover:bg-blue-700"
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Info Box */}
        <div className="mt-8 rounded-lg border-2 border-black bg-white p-6 shadow-brutal-lg">
          <h3 className="mb-3 font-bold text-black">User Management</h3>
          <p className="text-gray-600">
            Users are synced from Authentik during login. To manage users and
            roles, visit the{" "}
            <a
              href={process.env.NEXT_PUBLIC_AUTHENTIK_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="font-bold text-blue-600 hover:underline"
            >
              Authentik Admin Interface
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
