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
    <div className="flex flex-col gap-4 px-6 py-4 bg-bg-secondary border-b border-border">
      <div className="flex items-center gap-2 bg-bg-tertiary border border-border rounded-xl px-3 py-2 focus-within:border-accent-gold focus-within:shadow-[0_0_20px_rgba(212,175,55,0.15)] transition-all">
        <Search className="w-5 h-5 text-text-muted shrink-0" />
        <input
          type="text"
          className="flex-1 bg-transparent border-none text-text-primary text-base py-2 outline-none placeholder:text-text-muted"
          placeholder="Search Indian legal sections (e.g., 'Section 302 BNS' or 'murder penalty')..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSearching}
        />
        {query && (
          <button className="text-text-muted p-1 rounded hover:text-text-primary hover:bg-bg-card transition-all" onClick={handleClear}>
            <X size={18} />
          </button>
        )}
      </div>

      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
          <input
            type="checkbox"
            checked={showVerify}
            onChange={(e) => setShowVerify(e.target.checked)}
            className="accent-accent-gold w-4 h-4"
          />
          <span>Enable Verification</span>
        </label>

        <button
          className="flex items-center gap-2 px-4 py-2 bg-accent-gold text-bg-primary font-semibold rounded-lg hover:bg-accent-gold-bright hover:shadow-[0_0_20px_rgba(212,175,55,0.15)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
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