'use client'

import { Scale, Activity, Bookmark, History } from 'lucide-react'
import { useAppStore } from '@/lib/store'

export function Header() {
  const { activeTab, setActiveTab, searchHistory, bookmarks } = useAppStore()

  return (
    <header className="flex items-center justify-between px-8 py-4 bg-cream border-b border-slate sticky top-0 z-50 shadow-[0_1px_3px_rgba(0,0,0,0.1)]">
      <div className="flex items-center gap-4">
        <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gold/10 border border-gold/20">
          <Scale className="w-6 h-6 text-gold" />
        </div>
        <div className="flex flex-col justify-center">
          <span className="text-lg font-bold tracking-[0.15em] text-gold leading-tight">HECTOR</span>
          <span className="text-xs text-silver uppercase tracking-widest">Legal Intelligence</span>
        </div>
      </div>

      <nav className="flex items-center gap-2">
        <button
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
            activeTab === 'search'
              ? 'text-gold bg-gold/10 border border-gold/20'
              : 'text-silver hover:text-[#e8e8e8] hover:bg-charcoal/60 border border-transparent'
          }`}
          onClick={() => setActiveTab('search')}
        >
          <Activity size={18} />
          Research
        </button>
        <button
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
            activeTab === 'compare'
              ? 'text-gold bg-gold/10 border border-gold/20'
              : 'text-silver hover:text-[#e8e8e8] hover:bg-charcoal/60 border border-transparent'
          }`}
          onClick={() => setActiveTab('compare')}
        >
          <Scale size={18} />
          Compare
        </button>
        <div className="w-px h-7 bg-slate/30 mx-3" />
        <button className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-silver hover:text-[#e8e8e8] hover:bg-charcoal/60 transition-all relative border border-transparent">
          <History size={18} />
          {searchHistory.length > 0 && (
            <span className="absolute -top-2 -right-2 text-[10px] bg-gold text-cream px-2 py-1 rounded-full font-semibold">
              {searchHistory.length}
            </span>
          )}
        </button>
        <button className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-silver hover:text-[#e8e8e8] hover:bg-charcoal/60 transition-all relative border border-transparent">
          <Bookmark size={18} />
          {bookmarks.length > 0 && (
            <span className="absolute -top-2 -right-2 text-[10px] bg-gold text-cream px-2 py-1 rounded-full font-semibold">
              {bookmarks.length}
            </span>
          )}
        </button>
      </nav>

      <div className="flex items-center gap-2 px-4 py-2 bg-charcoal/50 border border-slate/40 rounded-xl">
        <span className="w-2.5 h-2.5 bg-success rounded-full animate-pulse" />
        <span className="text-xs text-silver">API Connected</span>
      </div>
    </header>
  )
}