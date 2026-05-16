'use client'

import { useState, KeyboardEvent } from 'react'
import { Search, Loader2, X } from 'lucide-react'
import { useAppStore } from '@/lib/store'
import { apiClient } from '@/lib/api'

export function SearchBar() {
  const {
    query,
    setQuery,
    isSearching,
    setIsSearching,
    setSearchResponse,
    setError,
    addSearchHistory,
  } = useAppStore()

  const [showVerify, setShowVerify] = useState(false)

  const handleSearch = async () => {
    if (!query.trim() || isSearching) return

    setIsSearching(true)
    setError(null)
    setSearchResponse(null)

    try {
      const response = await apiClient.search({
        query: query.trim(),
        verify: showVerify,
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
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const handleClear = () => {
    setQuery('')
    setSearchResponse(null)
    setError(null)
  }

  return (
    <div className="flex flex-col gap-4 px-6 py-4 bg-cream border-b border-slate">
      <div className="flex items-center gap-2 bg-charcoal border border-slate rounded-xl px-3 py-2 focus-within:border-gold focus-within:shadow-[0_0_20px_rgba(201,169,98,0.15)] transition-all">
        <Search className="w-5 h-5 text-silver shrink-0" />
        <input
          type="text"
          className="flex-1 bg-transparent border-none text-[#e8e8e8] text-base py-2 outline-none placeholder:text-silver"
          placeholder="Search Indian legal sections (e.g., 'Section 302 BNS' or 'murder penalty')..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSearching}
        />
        {query && (
          <button className="text-silver p-1 rounded hover:text-[#e8e8e8] hover:bg-charcoal transition-all" onClick={handleClear}>
            <X size={18} />
          </button>
        )}
      </div>

      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm text-silver cursor-pointer">
          <input
            type="checkbox"
            checked={showVerify}
            onChange={(e) => setShowVerify(e.target.checked)}
            className="accent-gold w-4 h-4"
          />
          <span>Enable Verification</span>
        </label>

        <button
          className="flex items-center gap-2 px-4 py-2 bg-gold text-cream font-semibold rounded-lg hover:bg-gold-light hover:shadow-[0_0_20px_rgba(201,169,98,0.15)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={handleSearch}
          disabled={!query.trim() || isSearching}
        >
          {isSearching ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
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
    </div>
  )
}