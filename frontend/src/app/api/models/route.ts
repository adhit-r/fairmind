import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const orgId = searchParams.get('org_id')
  const company = searchParams.get('company')
  
  try {
    
    // Call the backend API
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/models?${searchParams.toString()}`)
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }
    
    const data = await response.json()
    
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching models:', error)
    
    // Fallback to static data
    try {
      const fs = require('fs')
      const path = require('path')
      
      // Read from the backend models_registry.json file
      const registryPath = path.join(process.cwd(), '../../backend/models_registry.json')
      const registryData = fs.readFileSync(registryPath, 'utf8')
      const models = JSON.parse(registryData)
      
      // Filter by org_id if provided
      let filteredModels = models
      if (orgId) {
        filteredModels = models.filter((model: any) => model.org_id === orgId)
      } else if (company) {
        filteredModels = models.filter((model: any) => 
          (model.company || '').toLowerCase() === company.toLowerCase()
        )
      }
      
      return NextResponse.json({
        success: true,
        data: filteredModels,
        total: filteredModels.length
      })
    } catch (fallbackError) {
      console.error('Fallback error:', fallbackError)
      
      // Return empty data as final fallback
      return NextResponse.json({
        success: true,
        data: [],
        total: 0
      })
    }
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Call the backend API
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/models`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error creating model:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to create model' },
      { status: 500 }
    )
  }
}
