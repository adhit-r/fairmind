import { createClient } from '@supabase/supabase-js'

// Supabase client configuration
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Company-specific roles and permissions
export const COMPANY_ROLES = {
  SUPER_ADMIN: {
    name: 'super_admin',
    permissions: ['*'] // All permissions
  },
  COMPANY_ADMIN: {
    name: 'company_admin',
    permissions: [
      'models:read',
      'models:write',
      'models:delete',
      'simulations:read',
      'simulations:write',
      'compliance:read',
      'compliance:write',
      'users:read',
      'users:write'
    ]
  },
  COMPLIANCE_OFFICER: {
    name: 'compliance_officer',
    permissions: [
      'models:read',
      'compliance:read',
      'compliance:write',
      'audit:read',
      'reports:read',
      'reports:write'
    ]
  },
  DATA_SCIENTIST: {
    name: 'data_scientist',
    permissions: [
      'models:read',
      'models:write',
      'simulations:read',
      'simulations:write',
      'testing:read',
      'testing:write'
    ]
  },
  AUDITOR: {
    name: 'auditor',
    permissions: [
      'models:read',
      'audit:read',
      'compliance:read',
      'reports:read'
    ]
  }
}

// Company configurations
export const COMPANY_CONFIGS = {
  'bankcorp': {
    name: 'BankCorp',
    domain: 'bankcorp.com',
    logo: '/logos/bankcorp.png',
    theme: 'bankcorp-theme',
    features: ['credit-scoring', 'fraud-detection', 'compliance'],
    compliance_frameworks: ['NIST', 'GDPR', 'SOX'],
    risk_levels: ['low', 'medium', 'high', 'critical']
  },
  'securebank': {
    name: 'SecureBank',
    domain: 'securebank.com',
    logo: '/logos/securebank.png',
    theme: 'securebank-theme',
    features: ['fraud-detection', 'aml', 'kyc'],
    compliance_frameworks: ['NIST', 'GDPR', 'PCI-DSS'],
    risk_levels: ['low', 'medium', 'high', 'critical']
  },
  'visiontech': {
    name: 'VisionTech',
    domain: 'visiontech.com',
    logo: '/logos/visiontech.png',
    theme: 'visiontech-theme',
    features: ['computer-vision', 'image-classification'],
    compliance_frameworks: ['NIST', 'GDPR'],
    risk_levels: ['low', 'medium', 'high']
  }
}

// Authentication functions
export const signIn = async (email: string, password: string) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password
  })
  
  if (error) throw error
  
  // Create or update user profile
  await createUserProfile(data.user!)
  
  return data
}

export const signUp = async (email: string, password: string, fullName: string) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: fullName
      }
    }
  })
  
  if (error) throw error
  
  return data
}

export const signOut = async () => {
  const { error } = await supabase.auth.signOut()
  if (error) throw error
}

export const getCurrentUser = async () => {
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error) throw error
  return user
}

// User profile management
export const createUserProfile = async (user: any) => {
  const companyId = getUserCompanyFromEmail(user.email)
  
  const { error } = await supabase
    .from('users')
    .upsert({
      id: user.id,
      email: user.email,
      full_name: user.user_metadata?.full_name,
      company_id: companyId,
      role: 'data_scientist', // Default role
      permissions: COMPANY_ROLES.DATA_SCIENTIST.permissions,
      created_at: new Date().toISOString()
    })
  
  if (error) throw error
}

export const getUserProfile = async (userId: string) => {
  const { data, error } = await supabase
    .from('users')
    .select(`
      *,
      companies (
        id,
        name,
        domain,
        logo_url,
        theme,
        compliance_frameworks
      )
    `)
    .eq('id', userId)
    .single()
  
  if (error) throw error
  return data
}

// Company management
export const getUserCompanyFromEmail = (email: string): string | null => {
  const domain = email.split('@')[1]
  
  const domainToCompany: Record<string, string> = {
    'bankcorp.com': 'bankcorp',
    'securebank.com': 'securebank',
    'visiontech.com': 'visiontech'
  }
  
  return domainToCompany[domain] || null
}

export const getUserCompany = async () => {
  const user = await getCurrentUser()
  if (!user) return null
  
  const profile = await getUserProfile(user.id)
  return profile?.companies
}

export const getCompanyConfig = (companyId: string) => {
  return COMPANY_CONFIGS[companyId as keyof typeof COMPANY_CONFIGS] || null
}

// Permission checking
export const hasPermission = async (permission: string): Promise<boolean> => {
  try {
    const user = await getCurrentUser()
    if (!user) return false
    
    const profile = await getUserProfile(user.id)
    if (!profile) return false
    
    // Super admin has all permissions
    if (profile.role === 'super_admin') return true
    
    // Check user's permissions
    const userPermissions = profile.permissions || []
    return userPermissions.includes(permission) || userPermissions.includes('*')
  } catch (error) {
    console.error('Permission check failed:', error)
    return false
  }
}

export const getUserPermissions = async (): Promise<string[]> => {
  try {
    const user = await getCurrentUser()
    if (!user) return []
    
    const profile = await getUserProfile(user.id)
    if (!profile) return []
    
    return profile.permissions || []
  } catch (error) {
    console.error('Failed to get user permissions:', error)
    return []
  }
}

// Company-specific data queries
export const getCompanyModels = async () => {
  const user = await getCurrentUser()
  if (!user) return []
  
  const { data, error } = await supabase
    .from('models')
    .select('*')
    .order('created_at', { ascending: false })
  
  if (error) throw error
  return data || []
}

export const getCompanySimulations = async () => {
  const user = await getCurrentUser()
  if (!user) return []
  
  const { data, error } = await supabase
    .from('simulations')
    .select('*')
    .order('created_at', { ascending: false })
  
  if (error) throw error
  return data || []
}

// Real-time subscriptions
export const subscribeToCompanyData = (table: string, callback: (payload: any) => void) => {
  return supabase
    .channel(`${table}_changes`)
    .on('postgres_changes', 
      { 
        event: '*', 
        schema: 'public', 
        table 
      }, 
      callback
    )
    .subscribe()
}

// Auth state management
export const onAuthStateChange = (callback: (event: string, session: any) => void) => {
  return supabase.auth.onAuthStateChange(callback)
}

// Password reset
export const resetPassword = async (email: string) => {
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/reset-password`
  })
  
  if (error) throw error
}

// Update user profile
export const updateUserProfile = async (updates: any) => {
  const user = await getCurrentUser()
  if (!user) throw new Error('No authenticated user')
  
  const { error } = await supabase
    .from('users')
    .update(updates)
    .eq('id', user.id)
  
  if (error) throw error
}

// Company management functions
export const createCompany = async (companyData: any) => {
  const { data, error } = await supabase
    .from('companies')
    .insert(companyData)
    .select()
    .single()
  
  if (error) throw error
  return data
}

export const getCompanies = async () => {
  const { data, error } = await supabase
    .from('companies')
    .select('*')
    .order('name')
  
  if (error) throw error
  return data || []
} 