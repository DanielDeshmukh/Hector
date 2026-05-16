'use client'

import { useState } from 'react'
import { History, Bookmark, Trash2, Search } from 'lucide-react'
import { useAppStore } from '@/lib/store'

type Tab = 'history' | 'bookmarks'

interface SidePanelProps {
  onNewQuery?: () => void
  onHistoryClick?: (historyItem: { query: string }) => void
}

export function SidePanel({ onNewQuery, onHistoryClick }: SidePanelProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('history')
  const { searchHistory, bookmarks, removeBookmark, setQuery } = useAppStore()

  const handleHistoryClickInternal = (query: string) => {
    setQuery(query)
    setIsOpen(false)
    if (onHistoryClick) {
      onHistoryClick({ query })
    }
  }

  const handleNewQueryClick = () => {
    setIsOpen(false)
    if (onNewQuery) {
      onNewQuery()
    }
  }

  const handleBookmarkClick = (bookmark: typeof bookmarks[0]) => {
    setQuery(bookmark.query)
    setIsOpen(false)
  }

  return (
    <>
      <button className="fixed left-0 top-1/2 -translate-y-1/2 w-6 h-15 bg-cream border border-slate border-l-0 rounded-r-lg text-silver text-xs z-90 transition-all hover:bg-charcoal hover:text-gold" onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? '✕' : '☰'}
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/50 z-95" onClick={() => setIsOpen(false)} />
      )}

      <div className={`fixed left-0 top-0 bottom-0 w-70 bg-cream border-r border-slate z-100 flex flex-col transition-transform duration-250 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex border-b border-slate">
          <button
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all ${
              activeTab === 'history'
                ? 'text-gold border-gold'
                : 'text-silver border-transparent hover:text-[#e8e8e8] hover:bg-charcoal'
            }`}
            onClick={() => setActiveTab('history')}
          >
            <History size={16} />
            History
          </button>
          <button
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all ${
              activeTab === 'bookmarks'
                ? 'text-gold border-gold'
                : 'text-silver border-transparent hover:text-[#e8e8e8] hover:bg-charcoal'
            }`}
            onClick={() => setActiveTab('bookmarks')}
          >
            <Bookmark size={16} />
            Bookmarks
          </button>
        </div>

        {/* New Query Button */}
        <div className="px-3 py-3 border-b border-slate/60">
          <button
            className="w-full flex items-center gap-2 px-4 py-2.5 bg-charcoal/50 border border-slate/60 rounded-lg text-[13px] text-[#e8e8e8] hover:border-gold/50 hover:bg-charcoal transition-all"
            onClick={handleNewQueryClick}
          >
            <svg className="w-4 h-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Query
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {activeTab === 'history' ? (
            searchHistory.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-50 text-silver text-center">
                <History size={32} />
                <p className="mt-2 text-sm">No search history yet</p>
              </div>
            ) : (
              <ul className="list-none p-0">
                {searchHistory.map((item) => (
                  <li key={item.id} className="mb-1">
                    <button className="w-full flex items-center px-3 py-2 rounded-lg text-left transition-all hover:bg-charcoal" onClick={() => handleHistoryClickInternal(item.query)}>
                      <Search size={14} className="text-silver mr-2 shrink-0" />
                      <span className="flex-1 text-[13px] text-[#e8e8e8] truncate whitespace-nowrap overflow-hidden">{item.query}</span>
                      <span className="text-[10px] text-silver px-1.5 py-0.5 bg-charcoal rounded ml-2">{item.route}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )
          ) : (
            bookmarks.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-50 text-silver text-center">
                <Bookmark size={32} />
                <p className="mt-2 text-sm">No bookmarks saved</p>
              </div>
            ) : (
              <ul className="list-none p-0">
                {bookmarks.map((item) => (
                  <li key={item.id} className="mb-1">
                    <button className="w-full flex items-center px-3 py-2 rounded-lg text-left transition-all hover:bg-charcoal" onClick={() => handleBookmarkClick(item)}>
                      <Bookmark size={14} className="text-silver mr-2 shrink-0" />
                      <span className="flex-1 text-[13px] text-[#e8e8e8] truncate whitespace-nowrap overflow-hidden">{item.query}</span>
                      <button
                        className="text-silver p-1 rounded hover:text-error hover:bg-[rgba(239,68,68,0.1)] transition-all ml-2"
                        onClick={(e) => {
                          e.stopPropagation()
                          removeBookmark(item.id)
                        }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </button>
                  </li>
                ))}
              </ul>
            )
          )}
        </div>
      </div>
    </>
  )
}