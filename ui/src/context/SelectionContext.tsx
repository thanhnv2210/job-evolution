import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'

type SelectionState = {
  selectedIndustry: string | null
  selectedJobId: number | null
  setSelectedIndustry: (industry: string | null) => void
  setSelectedJobId: (id: number | null) => void
}

const SelectionContext = createContext<SelectionState | null>(null)

export function SelectionProvider({ children }: { children: ReactNode }) {
  const [selectedIndustry, setSelectedIndustry] = useState<string | null>(null)
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)

  return (
    <SelectionContext.Provider
      value={{ selectedIndustry, selectedJobId, setSelectedIndustry, setSelectedJobId }}
    >
      {children}
    </SelectionContext.Provider>
  )
}

export function useSelection() {
  const ctx = useContext(SelectionContext)
  if (!ctx) throw new Error('useSelection must be used inside SelectionProvider')
  return ctx
}
