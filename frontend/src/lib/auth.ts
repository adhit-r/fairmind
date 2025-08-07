import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Company roles
export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  COMPANY_ADMIN: 'company_admin',
  COMPLIANCE_OFFICER: 'compliance_officer',
  DATA_SCIENTIST: 'data_scientist',
  AUDITOR: 'auditor'
}

// Permission checking
export const hasPermission = async (permission: string): Promise<boolean> => {
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return false
  
  // For now, return true - implement proper permission checking later
  return true
}

// Get current user
export const getCurrentUser = async () => {
  const { data: { user } } = await supabase.auth.getUser()
  return user
}

// Sign in
export const signIn = async (email: string, password: string) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password
  })
  
  if (error) throw error
  return data
}

// Sign out
export const signOut = async () => {
  const { error } = await supabase.auth.signOut()
  if (error) throw error
} 