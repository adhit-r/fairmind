#!/usr/bin/env bun
/**
 * Integration Verification Script
 * Extends previous PR work by verifying all API integrations work with real backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface EndpointCheck {
  endpoint: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  status: 'success' | 'error' | 'not_tested'
  responseTime?: number
  error?: string
  hasData?: boolean
}

const endpoints: Array<{ path: string; method: 'GET' | 'POST' | 'PUT' | 'DELETE'; description: string }> = [
  // Dashboard & Core
  { path: '/api/v1/database/dashboard-stats', method: 'GET', description: 'Dashboard statistics' },
  { path: '/api/v1/database/models', method: 'GET', description: 'List models' },
  { path: '/api/v1/database/audit-logs', method: 'GET', description: 'Audit logs' },
  { path: '/api/v1/database/monitoring-metrics', method: 'GET', description: 'Monitoring metrics' },
  
  // AI Governance
  { path: '/api/v1/ai-governance/status', method: 'GET', description: 'System status' },
  { path: '/api/v1/ai-governance/policies', method: 'GET', description: 'List policies' },
  { path: '/api/v1/ai-governance/compliance/frameworks', method: 'GET', description: 'Compliance frameworks' },
  
  // Bias Detection
  { path: '/api/v1/bias-detection/detect', method: 'POST', description: 'Bias detection' },
  { path: '/api/v1/modern-bias-detection/comprehensive-evaluation', method: 'POST', description: 'Modern bias evaluation' },
  
  // AI BOM
  { path: '/api/v1/ai-bom/documents', method: 'GET', description: 'AI BOM documents' },
  { path: '/api/v1/ai-bom/stats', method: 'GET', description: 'AI BOM stats' },
  
  // Analytics
  { path: '/api/v1/core/metrics/summary', method: 'GET', description: 'Metrics summary' },
]

async function checkEndpoint(endpoint: { path: string; method: string; description: string }): Promise<EndpointCheck> {
  const startTime = Date.now()
  const url = `${API_BASE_URL}${endpoint.path}`
  
  try {
    const options: RequestInit = {
      method: endpoint.method,
      headers: {
        'Content-Type': 'application/json',
      },
    }
    
    // Add body for POST requests
    if (endpoint.method === 'POST') {
      options.body = JSON.stringify({ test: true })
    }
    
    const response = await fetch(url, options)
    const responseTime = Date.now() - startTime
    
    let hasData = false
    try {
      const data = await response.json()
      hasData = data && (data.data || data.success || Object.keys(data).length > 0)
    } catch {
      // Not JSON response
    }
    
    if (response.ok) {
      return {
        endpoint: endpoint.path,
        method: endpoint.method as any,
        status: 'success',
        responseTime,
        hasData,
      }
    } else {
      return {
        endpoint: endpoint.path,
        method: endpoint.method as any,
        status: 'error',
        responseTime,
        error: `HTTP ${response.status}`,
        hasData: false,
      }
    }
  } catch (error) {
    return {
      endpoint: endpoint.path,
      method: endpoint.method as any,
      status: 'error',
      responseTime: Date.now() - startTime,
      error: error instanceof Error ? error.message : 'Unknown error',
      hasData: false,
    }
  }
}

async function verifyAllIntegrations() {
  console.log('🔍 Verifying API Integrations...\n')
  console.log(`Backend URL: ${API_BASE_URL}\n`)
  
  // Check backend health first
  try {
    const healthResponse = await fetch(`${API_BASE_URL}/health`)
    if (healthResponse.ok) {
      console.log('✅ Backend is running\n')
    } else {
      console.log('⚠️  Backend health check failed\n')
    }
  } catch {
    console.log('❌ Backend is not accessible\n')
    return
  }
  
  const results: EndpointCheck[] = []
  
  for (const endpoint of endpoints) {
    process.stdout.write(`Checking ${endpoint.description}... `)
    const result = await checkEndpoint(endpoint)
    results.push(result)
    
    if (result.status === 'success') {
      console.log(`✅ (${result.responseTime}ms)`)
    } else {
      console.log(`❌ ${result.error}`)
    }
  }
  
  // Summary
  console.log('\n📊 Summary:')
  const successful = results.filter(r => r.status === 'success').length
  const failed = results.filter(r => r.status === 'error').length
  const withData = results.filter(r => r.hasData).length
  
  console.log(`  ✅ Successful: ${successful}/${results.length}`)
  console.log(`  ❌ Failed: ${failed}/${results.length}`)
  console.log(`  📦 With Data: ${withData}/${results.length}`)
  
  // Failed endpoints
  if (failed > 0) {
    console.log('\n❌ Failed Endpoints:')
    results.filter(r => r.status === 'error').forEach(r => {
      console.log(`  - ${r.endpoint} (${r.method}): ${r.error}`)
    })
  }
  
  // Endpoints without data
  const noData = results.filter(r => r.status === 'success' && !r.hasData)
  if (noData.length > 0) {
    console.log('\n⚠️  Endpoints returning empty data:')
    noData.forEach(r => {
      console.log(`  - ${r.endpoint}`)
    })
  }
  
  return results
}

// Run verification
verifyAllIntegrations().catch(console.error)

