'use client'

import { Scale, Activity, Bookmark, History } from 'lucide-react'
import { useAppStore } from '@/lib/store'

export function Header() {
  const { activeTab, setActiveTab, searchHistory, bookmarks } = useAppStore()

  return (
    <header className="flex items-center justify-between px-6 py-3 bg-cream border-b border-slate sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <Scale className="w-10 h-10 text-gold" />
        <div className="flex flex-col">
          <span className="text-xl font-bold tracking-[0.15em] text-gold leading-tight">HECTOR</span>
          <span className="text-xs text-silver uppercase tracking-widest">Legal Intelligence</span>
        </div>
      </div>

      <nav className="flex items-center gap-1">
        <button
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'search'
              ? 'text-gold bg-[rgba(201,169,98,0.1)]'
              : 'text-silver hover:text-[#e8e8e8] hover:bg-charcoal'
          }`}
          onClick={() => setActiveTab('search')}
        >
          <Activity size={18} />
          Research
        </button>
        <button
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'compare'
              ? 'text-gold bg-[rgba(201,169,98,0.1)]'
              : 'text-silver hover:text-[#e8e8e8] hover:bg-charcoal'
          }`}
          onClick={() => setActiveTab('compare')}
        >
          <Scale size={18} />
          Compare
        </button>
        <div className="w-px h-6 bg-slate mx-2" />
        <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-silver hover:text-[#e8e8e8] hover:bg-charcoal transition-all relative">
          <History size={18} />
          {searchHistory.length > 0 && (
            <span className="absolute -top-1 -right-1 text-[10px] bg-gold text-cream px-1.5 py-0.5 rounded-full font-semibold">
              {searchHistory.length}
            </span>
          )}
        </button>
        <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-silver hover:text-[#e8e8e8] hover:bg-charcoal transition-all relative">
          <Bookmark size={18} />
          {bookmarks.length > 0 && (
            <span className="absolute -top-1 -right-1 text-[10px] bg-gold text-cream px-1.5 py-0.5 rounded-full font-semibold">
              {bookmarks.length}
            </span>
          )}
        </button>
      </nav>

      <div className="flex items-center gap-2 px-3 py-2 bg-charcoal rounded-lg">
        <span className="w-2 h-2 bg-success rounded-full animate-pulse" />
        <span className="text-xs text-silver">API Connected</span>
      </div>
    </header>
  )
}