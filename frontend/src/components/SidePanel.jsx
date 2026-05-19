import { useState } from 'react'
import { Search, PanelLeftClose, Gavel, Clock } from 'lucide-react'
import useAppStore from '../lib/store'

function SidePanel({ onNewQuery, onHistoryClick }) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const { searchHistory } = useAppStore()

  const handleNewQueryClick = () => {
    if (onNewQuery) {
      onNewQuery()
    }
  }

  const handleHistoryClickInternal = (query) => {
    if (onHistoryClick) {
      onHistoryClick({ query })
    }
  }

  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  }

  if (isCollapsed) {
    return (
      <div className="flex h-full w-16 flex-col border-r border-slate/40 bg-cream">
        <button
          className="flex h-16 w-full items-center justify-center border-b border-slate/40 text-silver/60 transition-all hover:bg-charcoal/40 hover:text-gold"
          onClick={() => setIsCollapsed(false)}
        >
          <PanelLeftClose className="h-5 w-5" />
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-full w-[18%] min-w-70 max-w-85 flex-col border-r border-slate/40 bg-cream">
      {/* Sidebar Header - Brand Block */}
      <div className="flex items-start justify-between border-b border-slate/40 p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-gold/30 bg-gold/10">
            <Gavel className="h-5 w-5 text-gold" />
          </div>
          <div>
            <div className="text-[15px] font-semibold text-[#e8e8e8]">HECTOR</div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-silver/60">Legal Intelligence</div>
          </div>
        </div>
        <button
          className="rounded-lg p-2 text-silver/60 transition-all hover:bg-charcoal/40 hover:text-gold"
          onClick={() => setIsCollapsed(true)}
        >
          <PanelLeftClose className="h-4 w-4" />
        </button>
      </div>

      {/* Middle Section - New Query Button & Recent Queries */}
      <div className="flex-1 overflow-y-auto">
        {/* New Query Button */}
        <div className="px-6 py-5">
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

        {/* Recent Queries Section Label */}
        <div className="px-6 py-2">
          <div className="text-[10px] uppercase tracking-[0.2em] text-silver/50 font-semibold">Recent Queries</div>
        </div>

        {/* Recent Queries List */}
        <div className="px-4 py-2">
          {searchHistory.length === 0 ? (
            <div className="flex h-40 flex-col items-center justify-center text-center text-silver/50">
              <Search size={32} />
              <p className="mt-3 text-sm font-medium">No search history yet</p>
            </div>
          ) : (
            <ul className="list-none space-y-2 p-0">
              {searchHistory.slice(0, 10).map((item) => (
                <li key={item.id}>
                  <button
                    className="flex w-full items-start gap-3 rounded-2xl border border-transparent px-3 py-3 text-left transition-all hover:border-slate/30 hover:bg-charcoal/60"
                    onClick={() => handleHistoryClickInternal(item.query)}
                  >
                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-slate/35 bg-charcoal/40">
                      <Search size={14} className="text-silver/60" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate overflow-hidden whitespace-nowrap text-[13px] font-medium text-[#e8e8e8]">
                        {item.query}
                      </div>
                      <div className="mt-1.5 flex items-center gap-2">
                        <span className="flex items-center gap-1 text-[10px] text-silver/50">
                          <Clock size={10} />
                          {formatTime(item.timestamp)}
                        </span>
                        <span className="rounded-lg border border-slate/40 bg-charcoal/60 px-2 py-0.5 text-[9px] font-semibold text-silver/50">
                          {item.route || 'LEGAL'}
                        </span>
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Sidebar Footer - Status Information */}
      <div className="flex items-center justify-between border-t border-slate/40 px-6 py-4">
        <span className="text-xs text-silver/60 font-medium">20+ Legal Texts Indexed</span>
        <span className="flex items-center gap-2 text-xs text-silver/60 font-medium">
          <span className="h-2 w-2 rounded-full bg-success" />
          Online
        </span>
      </div>
    </div>
  )
}

export default SidePanel