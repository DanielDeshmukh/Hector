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
    <div className="flex flex-col bg-cream border-r border-slate/40 overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate/40 bg-cream/80">
        <h3 className="text-xs font-semibold text-silver/70 uppercase tracking-wider">Results</h3>
        <span className="text-xs font-medium text-silver/50 bg-slate/20 px-2.5 py-1 rounded-lg">{results.length} found</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {results.map((item, index) => (
          <button
            key={item.id || index}
            className={`w-full flex items-center justify-between px-6 py-4 text-left border-b border-slate/40 transition-all group ${
              selectedItem?.id === item.id
                ? 'bg-gold/8 border-l-4 border-l-gold'
                : 'hover:bg-charcoal/40'
            }`}
            onClick={() => handleSelect(item)}
          >
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap gap-2.5 mb-2">
                {item.act ? <span className="px-2.5 py-1 bg-gold/20 text-gold text-[10px] font-bold rounded-lg uppercase border border-gold/30">BNS</span> : null}
                {item.metadata?.section_number ? (
                  <span className="text-xs text-gold/90 font-bold">Section {String(item.metadata.section_number)}</span>
                ) : null}
                {item.metadata?.section_title ? (
                  <span className="text-xs text-silver/70 font-semibold">{String(item.metadata.section_title)}</span>
                ) : null}
              </div>
              <p className="text-[13px] text-silver/60 line-clamp-2 m-0 font-medium">{item.snippet}</p>
            </div>

            <div className="flex items-center gap-3 ml-4 shrink-0">
              <span className="text-xs text-success font-bold min-w-12 text-right">{(item.score * 100).toFixed(0)}%</span>
              <ChevronRight className="w-4 h-4 text-silver/40 group-hover:text-gold transition-colors" />
            </div>
          </button>
        ))}
      </div>

      {searchResponse && searchResponse.total_pages > 1 && (
        <div className="px-6 py-3 text-center text-xs text-silver/50 border-t border-slate/40 bg-cream/50 font-medium">
          Page {searchResponse.page} of {searchResponse.total_pages}
        </div>
      )}
    </div>
  )
}