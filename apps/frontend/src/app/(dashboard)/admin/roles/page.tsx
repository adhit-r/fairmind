import { redirect } from 'next/navigation'

// Roles and permissions live on the API-backed organisation admin page.
export default function RolesPage() {
  redirect('/org-admin/roles')
}
