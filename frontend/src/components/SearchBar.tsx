'use client'

import { useState, KeyboardEvent } from 'react'
import { Search, Loader2, X } from 'lucide-react'
import { useAppStore } from '@/lib/store'
import { apiClient } from '@/lib/api'
import styles from './SearchBar.module.css'

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
    <div className={styles.container}>
      <div className={styles.inputWrapper}>
        <Search className={styles.searchIcon} />
        <input
          type="text"
          className={styles.input}
          placeholder="Search Indian legal sections (e.g., 'Section 302 BNS' or 'murder penalty')..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSearching}
        />
        {query && (
          <button className={styles.clearButton} onClick={handleClear}>
            <X size={18} />
          </button>
        )}
      </div>

      <div className={styles.controls}>
        <label className={styles.checkbox}>
          <input
            type="checkbox"
            checked={showVerify}
            onChange={(e) => setShowVerify(e.target.checked)}
          />
          <span>Enable Verification</span>
        </label>

        <button
          className={styles.searchButton}
          onClick={handleSearch}
          disabled={!query.trim() || isSearching}
        >
          {isSearching ? (
            <>
              <Loader2 className={styles.spinner} />
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