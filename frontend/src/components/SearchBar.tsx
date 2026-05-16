'use client'

import { useState, KeyboardEvent } from 'react'
import { Search, Loader2, X, FileText, List, AlignLeft } from 'lucide-react'
import { useAppStore } from '@/lib/store'
import { apiClient } from '@/lib/api'

type ResponseFormat = 'summary' | 'detailed' | 'citations'

interface SearchBarProps {
  onSubmit?: (query: string) => void
  disabled?: boolean
}

export function SearchBar({ onSubmit, disabled }: SearchBarProps) {
  const {
    query: storeQuery,
    setQuery: setStoreQuery,
    isSearching,
    setIsSearching,
    setSearchResponse,
    setError,
    addSearchHistory,
  } = useAppStore()

  const query = storeQuery
  const setQuery = setStoreQuery

  const [showVerify, setShowVerify] = useState(false)
  const [format, setFormat] = useState<ResponseFormat>('summary')
  const [includeRelated, setIncludeRelated] = useState(true)

  // Use onSubmit prop if provided (new design), otherwise use internal search
  const handleSubmit = async () => {
    if (!query.trim() || isSearching) return

    if (onSubmit) {
      onSubmit(query.trim())
      return
    }

    // Original behavior
    setIsSearching(true)
    setError(null)
    setSearchResponse(null)

    try {
      const response = await apiClient.search({
        query: query.trim(),
        verify: showVerify,
        format: format,
        include_related: includeRelated,
        page: 1,
        page_size: 10,
      })

      setSearchResponse(response)
      addSearchHistory(query.trim(), response.route)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setIsSearching(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !disabled) {
      handleSubmit()
    }
  }

  const handleClear = () => {
    setQuery('')
    setSearchResponse(null)
    setError(null)
  }

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-8 py-6 sm:px-10 lg:px-14">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <div className="flex min-w-0 items-center gap-4 rounded-2xl border border-slate/50 bg-charcoal/60 px-5 py-4 transition-all focus-within:border-gold/60 focus-within:shadow-[0_0_20px_rgba(201,169,98,0.15)]">
          <Search className="h-5 w-5 shrink-0 text-gold/70" />
          <input
            type="text"
            className="flex-1 border-none bg-transparent py-1 text-base text-[#e8e8e8] outline-none placeholder:text-silver/60"
            placeholder="Search Indian legal sections (e.g., 'Section 302 BNS' or 'murder penalty')..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || isSearching}
          />
          {query && (
            <button className="rounded p-1.5 text-silver/70 transition-all hover:text-gold hover:bg-charcoal" onClick={handleClear}>
              <X size={18} />
            </button>
          )}
        </div>

        <button
          className="flex h-[52px] items-center justify-center gap-2 rounded-2xl bg-gold px-8 text-cream font-semibold transition-all hover:bg-gold-light hover:shadow-[0_0_25px_rgba(201,169,98,0.25)] disabled:cursor-not-allowed disabled:opacity-50 lg:min-w-[160px]"
          onClick={handleSubmit}
          disabled={disabled || !query.trim() || isSearching}
        >
          {isSearching ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Search size={18} />
              Search
            </>
          )}
        </button>
      </div>

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-4 sm:gap-5">
          {/* Format Selector */}
          <div className="flex items-center gap-1.5 rounded-xl bg-charcoal/60 p-1.5 border border-slate/40">
            <button
              type="button"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                format === 'summary'
                  ? 'bg-gold/20 text-gold border border-gold/30'
                  : 'text-silver/70 hover:text-[#e8e8e8] border border-transparent'
              }`}
              onClick={() => setFormat('summary')}
            >
              <AlignLeft size={14} />
              Summary
            </button>
            <button
              type="button"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                format === 'detailed'
                  ? 'bg-gold/20 text-gold border border-gold/30'
                  : 'text-silver/70 hover:text-[#e8e8e8] border border-transparent'
              }`}
              onClick={() => setFormat('detailed')}
            >
              <FileText size={14} />
              Detailed
            </button>
            <button
              type="button"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                format === 'citations'
                  ? 'bg-gold/20 text-gold border border-gold/30'
                  : 'text-silver/70 hover:text-[#e8e8e8] border border-transparent'
              }`}
              onClick={() => setFormat('citations')}
            >
              <List size={14} />
              Citations
            </button>
          </div>

          <label className="flex items-center gap-2.5 text-sm text-silver/70 cursor-pointer hover:text-silver transition-all">
            <input
              type="checkbox"
              checked={showVerify}
              onChange={(e) => setShowVerify(e.target.checked)}
              className="accent-gold w-4 h-4 rounded cursor-pointer"
            />
            <span className="font-medium">Verify</span>
          </label>

          <label className="flex items-center gap-2.5 text-sm text-silver/70 cursor-pointer hover:text-silver transition-all">
            <input
              type="checkbox"
              checked={includeRelated}
              onChange={(e) => setIncludeRelated(e.target.checked)}
              className="accent-gold w-4 h-4 rounded cursor-pointer"
            />
            <span className="font-medium">Related</span>
          </label>
        </div>
      </div>
    </div>
  )
}
