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
    <div className="border-b border-slate bg-cream px-6 py-6 sm:px-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-5">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-slate/50 bg-charcoal/35">
            <Scale className="text-gold" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[#e8e8e8]">IPC to BNS Comparator</h2>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[180px_auto_minmax(0,1fr)_160px] lg:items-end">
          <div className="shrink-0">
            <select
              value={act}
              onChange={(e) => setAct(e.target.value as 'IPC' | 'BNS')}
              className="w-full cursor-pointer rounded-2xl border border-slate bg-charcoal px-4 py-3 text-sm text-[#e8e8e8] transition-colors focus:border-gold focus:outline-none"
            >
              <option value="IPC">IPC (Old)</option>
              <option value="BNS">BNS (New)</option>
            </select>
          </div>

          <div className="hidden justify-center lg:flex">
            <div className="flex h-[52px] w-[52px] items-center justify-center rounded-2xl border border-slate/40 bg-charcoal/35 text-gold">
              <ArrowRight size={20} />
            </div>
          </div>

          <div className="min-w-0">
            <input
              type="text"
              value={section}
              onChange={(e) => setSection(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter section number..."
              className="w-full rounded-2xl border border-slate bg-charcoal px-4 py-3 text-sm text-[#e8e8e8] transition-colors placeholder:text-silver focus:border-gold focus:outline-none"
              disabled={isComparing}
            />
          </div>

          <button
            className="flex h-[52px] items-center justify-center gap-2 rounded-2xl bg-gold px-5 font-semibold text-cream transition-all whitespace-nowrap hover:bg-gold-light disabled:cursor-not-allowed disabled:opacity-50"
            onClick={handleCompare}
            disabled={!section.trim() || isComparing}
          >
            {isComparing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Comparing...
              </>
            ) : (
              'Compare'
            )}
          </button>
        </div>

        {error && (
          <div className="rounded-2xl border border-error bg-[rgba(239,68,68,0.1)] px-4 py-3 text-sm text-error">
            {error}
          </div>
        )}
      </div>
    </div>
  )
}
