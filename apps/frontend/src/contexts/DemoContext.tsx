'use client'

import React, { createContext, useContext, useState, ReactNode } from 'react'

interface DemoContextType {
  hasSyntheticData: boolean
  loadSyntheticData: () => void
  clearSyntheticData: () => void
}

const DemoContext = createContext<DemoContextType | undefined>(undefined)

export function DemoProvider({ children }: { children: ReactNode }) {
  const [hasSyntheticData, setHasSyntheticData] = useState(false)

  const loadSyntheticData = () => {
    setHasSyntheticData(true)
  }

  const clearSyntheticData = () => {
    setHasSyntheticData(false)
  }

  return (
    <DemoContext.Provider value={{ hasSyntheticData, loadSyntheticData, clearSyntheticData }}>
      {children}
    </DemoContext.Provider>
  )
}

export function useDemo() {
  const context = useContext(DemoContext)
  if (context === undefined) {
    throw new Error('useDemo must be used within a DemoProvider')
  }
  return context
}
