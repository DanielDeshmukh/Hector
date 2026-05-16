'use client'

import { useState, KeyboardEvent } from 'react'
import { Scale, ArrowRight, Loader2 } from 'lucide-react'
import { useAppStore } from '@/lib/store'
import { apiClient } from '@/lib/api'

export function ComparePanel() {
  const { setCompareResult, addSearchHistory } = useAppStore()
  const [act, setAct] = useState<'IPC' | 'BNS'>('IPC')
  const [section, setSection] = useState('')
  const [isComparing, setIsComparing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCompare = async () => {
    if (!section.trim() || isComparing) return

    setIsComparing(true)
    setError(null)

    try {
      const response = await apiClient.compare({
        act,
        section: section.trim(),
        page_size: 5,
      })

      setCompareResult(JSON.stringify(response, null, 2))
      addSearchHistory(`Compare ${act} ${section}`, 'COMPARE')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed')
    } finally {
      setIsComparing(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleCompare()
    }
  }

  return (
    <div className="px-6 py-4 bg-bg-secondary border-b border-border">
      <div className="flex items-center gap-2 mb-4">
        <Scale className="text-accent-gold" />
        <h2 className="text-base font-semibold text-text-primary">IPC ↔ BNS Comparator</h2>
      </div>

      <div className="flex items-center gap-4">
        <div className="shrink-0">
          <select
            value={act}
            onChange={(e) => setAct(e.target.value as 'IPC' | 'BNS')}
            className="px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-sm text-text-primary cursor-pointer transition-colors focus:border-accent-gold focus:outline-none"
          >
            <option value="IPC">IPC (Old)</option>
            <option value="BNS">BNS (New)</option>
          </select>
        </div>

        <div className="text-accent-gold">
          <ArrowRight size={20} />
        </div>

        <div className="flex-1">
          <input
            type="text"
            value={section}
            onChange={(e) => setSection(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter section number..."
            className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-lg text-sm text-text-primary transition-colors focus:border-accent-gold focus:outline-none placeholder:text-text-muted"
            disabled={isComparing}
          />
        </div>

        <button
          className="flex items-center gap-2 px-4 py-2 bg-accent-gold text-bg-primary font-semibold rounded-lg hover:bg-accent-gold-bright transition-all whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={handleCompare}
          disabled={!section.trim() || isComparing}
        >
          {isComparing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Comparing...
            </>
          ) : (
            'Compare'
          )}
        </button>
      </div>

      {error && (
        <div className="mt-3 px-3 py-2 bg-[rgba(239,68,68,0.1)] border border-error rounded-lg text-error text-sm">
          {error}
        </div>
      )}
    </div>
  )
}