'use client'

import { useState } from 'react'
import { History, Bookmark, Trash2, Search, PanelLeftOpen, PanelLeftClose } from 'lucide-react'
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
      <button
        className="fixed left-4 top-1/2 z-40 flex h-14 w-10 -translate-y-1/2 items-center justify-center rounded-2xl border border-slate bg-cream text-silver shadow-[0_16px_40px_rgba(0,0,0,0.18)] transition-all hover:bg-charcoal hover:text-gold"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-40 bg-black/45 backdrop-blur-[2px]" onClick={() => setIsOpen(false)} />
      )}

      <div
        className={`fixed left-4 top-4 bottom-4 z-50 flex w-[320px] flex-col overflow-hidden rounded-[28px] border border-slate bg-cream shadow-[0_24px_80px_rgba(0,0,0,0.32)] transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-[calc(100%+1rem)]'
        }`}
      >
        <div className="border-b border-slate/60 px-5 py-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <div className="text-[10px] uppercase tracking-[0.18em] text-silver/45">Workspace</div>
              <div className="mt-1 text-sm text-[#e8e8e8]">Research Navigator</div>
            </div>
            <button
              className="rounded-lg p-2 text-silver transition-all hover:bg-charcoal hover:text-[#e8e8e8]"
              onClick={() => setIsOpen(false)}
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          </div>

          <div className="flex rounded-2xl bg-charcoal/50 p-1">
            <button
              className={`flex-1 rounded-xl px-4 py-2 text-sm font-medium transition-all ${
                activeTab === 'history'
                  ? 'border border-gold/30 text-gold'
                  : 'text-silver hover:text-[#e8e8e8]'
              }`}
              onClick={() => setActiveTab('history')}
            >
              <span className="flex items-center justify-center gap-2">
                <History size={16} />
                History
              </span>
            </button>
            <button
              className={`flex-1 rounded-xl px-4 py-2 text-sm font-medium transition-all ${
                activeTab === 'bookmarks'
                  ? 'border border-gold/30 text-gold'
                  : 'text-silver hover:text-[#e8e8e8]'
              }`}
              onClick={() => setActiveTab('bookmarks')}
            >
              <span className="flex items-center justify-center gap-2">
                <Bookmark size={16} />
                Bookmarks
              </span>
            </button>
          </div>
        </div>

        <div className="border-b border-slate/60 px-5 py-4">
          <button
            className="flex w-full items-center gap-2 rounded-2xl border border-slate/60 bg-charcoal/50 px-4 py-3 text-[13px] text-[#e8e8e8] transition-all hover:border-gold/50 hover:bg-charcoal"
            onClick={handleNewQueryClick}
          >
            <svg className="h-4 w-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Query
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-4">
          {activeTab === 'history' ? (
            searchHistory.length === 0 ? (
              <div className="flex h-52 flex-col items-center justify-center text-center text-silver">
                <History size={32} />
                <p className="mt-2 text-sm">No search history yet</p>
              </div>
            ) : (
              <ul className="list-none space-y-2 p-0">
                {searchHistory.map((item) => (
                  <li key={item.id}>
                    <button
                      className="flex w-full items-center rounded-2xl px-3 py-3 text-left transition-all hover:bg-charcoal"
                      onClick={() => handleHistoryClickInternal(item.query)}
                    >
                      <Search size={14} className="mr-3 shrink-0 text-silver" />
                      <span className="flex-1 truncate overflow-hidden whitespace-nowrap text-[13px] text-[#e8e8e8]">
                        {item.query}
                      </span>
                      <span className="ml-2 rounded bg-charcoal px-1.5 py-0.5 text-[10px] text-silver">
                        {item.route}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )
          ) : bookmarks.length === 0 ? (
            <div className="flex h-52 flex-col items-center justify-center text-center text-silver">
              <Bookmark size={32} />
              <p className="mt-2 text-sm">No bookmarks saved</p>
            </div>
          ) : (
            <ul className="list-none space-y-2 p-0">
              {bookmarks.map((item) => (
                <li key={item.id}>
                  <button
                    className="flex w-full items-center rounded-2xl px-3 py-3 text-left transition-all hover:bg-charcoal"
                    onClick={() => handleBookmarkClick(item)}
                  >
                    <Bookmark size={14} className="mr-3 shrink-0 text-silver" />
                    <span className="flex-1 truncate overflow-hidden whitespace-nowrap text-[13px] text-[#e8e8e8]">
                      {item.query}
                    </span>
                    <button
                      className="ml-2 rounded p-1 text-silver transition-all hover:bg-[rgba(239,68,68,0.1)] hover:text-error"
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
          )}
        </div>
      </div>
    </>
  )
}
