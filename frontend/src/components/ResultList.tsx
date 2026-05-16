'use client'

import { useAppStore } from '@/lib/store'
import { SearchHit } from '@/lib/api'
import { ChevronRight } from 'lucide-react'

export function ResultList() {
  const { searchResponse, selectedItem, setSelectedItem } = useAppStore()

  const results = searchResponse?.items || []

  if (results.length === 0) {
    return null
  }

  const handleSelect = (item: SearchHit) => {
    setSelectedItem(item)
  }

  return (
    <div className="flex flex-col bg-bg-secondary border-r border-border overflow-hidden">
      <div className="flex items-center justify-between px-6 py-3 border-b border-border">
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Results</h3>
        <span className="text-xs text-text-muted">{results.length} found</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {results.map((item, index) => (
          <button
            key={item.id || index}
            className={`w-full flex items-center justify-between px-6 py-3 text-left border-b border-border transition-all ${
              selectedItem?.id === item.id
                ? 'bg-[rgba(212,175,55,0.1)] border-l-3 border-l-accent-gold'
                : 'hover:bg-bg-tertiary'
            }`}
            onClick={() => handleSelect(item)}
          >
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap gap-2 mb-1">
                {item.act ? <span className="px-1.5 py-0.5 bg-accent-gold text-bg-primary text-[10px] font-bold rounded uppercase">BNS</span> : null}
                {item.metadata?.section_number ? (
                  <span className="text-xs text-accent-gold font-semibold">Section {String(item.metadata.section_number)}</span>
                ) : null}
                {item.metadata?.section_title ? (
                  <span className="text-xs text-text-secondary font-medium">{String(item.metadata.section_title)}</span>
                ) : null}
              </div>
              <p className="text-[13px] text-text-secondary line-clamp-2 m-0">{item.snippet}</p>
            </div>

            <div className="flex items-center gap-2 ml-3">
              <span className="text-xs text-success font-semibold min-w-10 text-right">{(item.score * 100).toFixed(0)}%</span>
              <ChevronRight className="w-4 h-4 text-text-muted transition-transform" />
            </div>
          </button>
        ))}
      </div>

      {searchResponse && searchResponse.total_pages > 1 && (
        <div className="px-4 py-3 text-center text-xs text-text-muted border-t border-border">
          Page {searchResponse.page} of {searchResponse.total_pages}
        </div>
      )}
    </div>
  )
}