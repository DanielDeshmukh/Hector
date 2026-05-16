'use client'

import { AlertCircle, X } from 'lucide-react'
import { useAppStore } from '@/lib/store'

export function ErrorMessage() {
  const { error, setError } = useAppStore()

  if (!error) return null

  return (
    <div className="flex items-center gap-4 px-6 py-3 bg-[rgba(239,68,68,0.1)] border border-error rounded-lg mx-6 my-3">
      <AlertCircle className="text-error shrink-0" />
      <span className="flex-1 text-sm text-error">{error}</span>
      <button className="text-error p-1 rounded hover:bg-[rgba(239,68,68,0.2)] transition-all" onClick={() => setError(null)}>
        <X size={18} />
      </button>
    </div>
  )
}