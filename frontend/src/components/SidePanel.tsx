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
        className="fixed left-5 top-1/2 z-40 flex h-14 w-11 -translate-y-1/2 items-center justify-center rounded-2xl border border-slate/40 bg-cream text-silver shadow-[0_8px_24px_rgba(0,0,0,0.16)] transition-all hover:bg-charcoal/60 hover:text-gold"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <PanelLeftClose className="h-5 w-5" /> : <PanelLeftOpen className="h-5 w-5" />}
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[3px]" onClick={() => setIsOpen(false)} />
      )}

      <div
        className={`fixed left-5 top-5 bottom-5 z-50 flex w-[340px] flex-col overflow-hidden rounded-[32px] border border-slate/40 bg-cream shadow-[0_32px_96px_rgba(0,0,0,0.32)] transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-[calc(100%+1.25rem)]'
        }`}
      >
        <div className="border-b border-slate/40 bg-cream/80 px-7 py-6">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-silver/50 font-semibold">Workspace</div>
              <div className="mt-2 text-[15px] font-semibold text-[#e8e8e8]">Research Navigator</div>
            </div>
            <button
              className="rounded-lg p-2.5 text-silver/60 transition-all hover:bg-charcoal/40 hover:text-gold border border-transparent hover:border-slate/40"
              onClick={() => setIsOpen(false)}
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          </div>

          <div className="flex rounded-xl border border-slate/40 bg-charcoal/50 p-1">
            <button
              className={`flex-1 rounded-lg px-4 py-2.5 text-sm font-bold transition-all ${
                activeTab === 'history'
                  ? 'bg-gold/15 border border-gold/30 text-gold'
                  : 'text-silver/70 hover:text-[#e8e8e8]'
              }`}
              onClick={() => setActiveTab('history')}
            >
              <span className="flex items-center justify-center gap-2">
                <History size={16} />
                History
              </span>
            </button>
            <button
              className={`flex-1 rounded-lg px-4 py-2.5 text-sm font-bold transition-all ${
                activeTab === 'bookmarks'
                  ? 'bg-gold/15 border border-gold/30 text-gold'
                  : 'text-silver/70 hover:text-[#e8e8e8]'
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

        <div className="border-b border-slate/40 bg-charcoal/30 px-6 py-4">
          <button
            className="flex w-full items-center gap-3 rounded-2xl border border-slate/50 bg-charcoal/60 px-5 py-3.5 text-[13px] font-semibold text-[#e8e8e8] transition-all hover:border-gold/50 hover:bg-charcoal/80 hover:text-gold"
            onClick={handleNewQueryClick}
          >
            <svg className="h-5 w-5 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Query
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-5">
          {activeTab === 'history' ? (
            searchHistory.length === 0 ? (
              <div className="flex h-52 flex-col items-center justify-center text-center text-silver/50">
                <History size={36} />
                <p className="mt-3 text-sm font-medium">No search history yet</p>
              </div>
            ) : (
              <ul className="list-none space-y-2.5 p-0">
                {searchHistory.map((item) => (
                  <li key={item.id}>
                    <button
                      className="flex w-full items-start gap-3 rounded-2xl border border-transparent px-4 py-3.5 text-left transition-all hover:border-slate/30 hover:bg-charcoal/60"
                      onClick={() => handleHistoryClickInternal(item.query)}
                    >
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-slate/35 bg-charcoal/40">
                        <Search size={15} className="text-silver/60" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="truncate overflow-hidden whitespace-nowrap text-[13px] font-medium text-[#e8e8e8]">
                          {item.query}
                        </div>
                        <div className="mt-2">
                          <span className="rounded-lg border border-slate/40 bg-charcoal/60 px-2 py-0.5 text-[10px] font-semibold text-silver/50">
                            {item.route}
                          </span>
                        </div>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )
          ) : bookmarks.length === 0 ? (
            <div className="flex h-52 flex-col items-center justify-center text-center text-silver/50">
              <Bookmark size={36} />
              <p className="mt-3 text-sm font-medium">No bookmarks saved</p>
            </div>
          ) : (
            <ul className="list-none space-y-2.5 p-0">
              {bookmarks.map((item) => (
                <li key={item.id}>
                  <div className="flex items-start gap-3 rounded-2xl border border-transparent px-4 py-3.5 transition-all hover:border-slate/30 hover:bg-charcoal/60">
                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-slate/35 bg-charcoal/40">
                      <Bookmark size={14} className="text-silver" />
                    </div>
                    <button
                      className="min-w-0 flex-1 text-left"
                      onClick={() => handleBookmarkClick(item)}
                    >
                      <span className="block truncate overflow-hidden whitespace-nowrap text-[13px] text-[#e8e8e8]">
                        {item.query}
                      </span>
                    </button>
                    <button
                      className="rounded-lg p-1.5 text-silver transition-all hover:bg-[rgba(239,68,68,0.1)] hover:text-error"
                      onClick={(e) => {
                        e.stopPropagation()
                        removeBookmark(item.id)
                      }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  )
}
