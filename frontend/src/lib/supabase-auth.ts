import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Test organization with dummy data
export const TEST_ORG_CONFIG = {
  id: 'test-org-123',
  name: 'Fairmind Demo Corp',
  type: 'demo',
  industry: 'technology',
  size: 'medium',
  models: [
    {
      id: 'model-1',
      name: 'Credit Risk Model',
      framework: 'scikit-learn',
      type: 'classification',
      accuracy: 0.89,
      bias_score: 0.15,
      security_score: 0.92,
      compliance_score: 0.88,
      uploaded_at: '2024-01-15T10:30:00Z',
      file_path: '/models/credit_risk_model.pkl'
    },
    {
      id: 'model-2', 
      name: 'Fraud Detection Model',
      framework: 'tensorflow',
      type: 'classification',
      accuracy: 0.94,
      bias_score: 0.08,
      security_score: 0.95,
      compliance_score: 0.91,
      uploaded_at: '2024-01-20T14:15:00Z',
      file_path: '/models/fraud_detection_model.h5'
    },
    {
      id: 'model-3',
      name: 'Customer Segmentation Model',
      framework: 'pytorch',
      type: 'clustering',
      accuracy: 0.87,
      bias_score: 0.12,
      security_score: 0.89,
      compliance_score: 0.85,
      uploaded_at: '2024-01-25T09:45:00Z',
      file_path: '/models/customer_segmentation.pt'
    }
  ],
  datasets: [
    {
      id: 'dataset-1',
      name: 'Credit Card Transactions',
      samples: 100000,
      features: 30,
      description: 'Credit card transaction data for fraud detection',
      bias_issues: ['geographic_bias', 'age_bias'],
      compliance_status: 'gdpr_compliant'
    },
    {
      id: 'dataset-2',
      name: 'Customer Demographics',
      samples: 50000,
      features: 15,
      description: 'Customer demographic data for segmentation',
      bias_issues: ['gender_bias', 'income_bias'],
      compliance_status: 'ccpa_compliant'
    }
  ],
  bias_analyses: [
    {
      id: 'analysis-1',
      model_id: 'model-1',
      dataset_id: 'dataset-1',
      score: 0.85,
      issues: [
        'Statistical parity bias: 15% difference in approval rates',
        'Equal opportunity bias: 8% difference in true positive rates'
      ],
      recommendations: [
        'Implement MinDiff during training',
        'Add more diverse training data'
      ],
      created_at: '2024-01-16T11:00:00Z'
    }
  ],
  security_tests: [
    {
      id: 'security-1',
      model_id: 'model-1',
      score: 0.92,
      vulnerabilities: [
        'Potential prompt injection vulnerability',
        'Output filtering needs improvement'
      ],
      recommendations: [
        'Implement input validation',
        'Add output sanitization'
      ],
      created_at: '2024-01-17T13:30:00Z'
    }
  ],
  compliance_checks: [
    {
      id: 'compliance-1',
      model_id: 'model-1',
      score: 0.88,
      gaps: [
        'GDPR data retention policy needs review',
        'CCPA consent management requires updates'
      ],
      recommendations: [
        'Update data retention policies',
        'Implement consent management system'
      ],
      created_at: '2024-01-18T15:45:00Z'
    }
  ]
}

// Organization configurations for different types
export const COMPANY_CONFIGS = {
  test: TEST_ORG_CONFIG,
  new: {
    id: null,
    name: '',
    type: 'new',
    industry: '',
    size: '',
    models: [],
    datasets: [],
    bias_analyses: [],
    security_tests: [],
    compliance_checks: []
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
        full_name: fullName,
      },
    },
  })

  if (error) throw error
  return data
}

export const signOut = async () => {
  const { error } = await supabase.auth.signOut()
  if (error) throw error
}

// Create or update user profile
export const createUserProfile = async (user: any) => {
  const { data: existingProfile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single()

  if (!existingProfile) {
    // Create new profile
    const { error } = await supabase
      .from('profiles')
      .insert([
        {
          id: user.id,
          email: user.email,
          full_name: user.user_metadata?.full_name || '',
          role: 'user',
          default_org_id: null,
          onboarding_completed: false
        }
      ])

    if (error) {
      console.error('Error creating profile:', error)
    }
  }
}

// Get organization data
export const getOrganizationData = async (orgId: string) => {
  if (orgId === 'test-org-123') {
    return TEST_ORG_CONFIG
  }
  
  // For real organizations, fetch from database
  const { data, error } = await supabase
    .from('organizations')
    .select('*')
    .eq('id', orgId)
    .single()

  if (error) {
    console.error('Error fetching organization:', error)
    return null
  }

  return data
}

// Create new organization
export const createOrganization = async (orgData: any, userId: string) => {
  const { data, error } = await supabase
    .from('organizations')
    .insert([
      {
        ...orgData,
        created_by: userId,
        created_at: new Date().toISOString()
      }
    ])
    .select()
    .single()

  if (error) {
    console.error('Error creating organization:', error)
    throw error
  }

  return data
} 