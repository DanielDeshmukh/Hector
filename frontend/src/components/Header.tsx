'use client'

import { Scale, Activity, Bookmark, History } from 'lucide-react'
import { useAppStore } from '@/lib/store'

export function Header() {
  const { activeTab, setActiveTab, searchHistory, bookmarks } = useAppStore()

  return (
    <header className="flex items-center justify-between px-6 py-3 bg-[#111111] border-b border-[#2a2a2a] sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <Scale className="w-10 h-10 text-[#D4AF37]" />
        <div className="flex flex-col">
          <span className="text-xl font-bold tracking-[0.15em] text-[#D4AF37] leading-tight">HECTOR</span>
          <span className="text-xs text-[#666666] uppercase tracking-[0.1em]">Legal Intelligence</span>
        </div>
      </div>

      <nav className="flex items-center gap-1">
        <button
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'search'
              ? 'text-[#D4AF37] bg-[rgba(212,175,55,0.1)]'
              : 'text-[#a0a0a0] hover:text-[#E8E8E8] hover:bg-[#1a1a1a]'
          }`}
          onClick={() => setActiveTab('search')}
        >
          <Activity size={18} />
          Research
        </button>
        <button
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'compare'
              ? 'text-[#D4AF37] bg-[rgba(212,175,55,0.1)]'
              : 'text-[#a0a0a0] hover:text-[#E8E8E8] hover:bg-[#1a1a1a]'
          }`}
          onClick={() => setActiveTab('compare')}
        >
          <Scale size={18} />
          Compare
        </button>
        <div className="w-px h-6 bg-[#2a2a2a] mx-2" />
        <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-[#a0a0a0] hover:text-[#E8E8E8] hover:bg-[#1a1a1a] transition-all relative">
          <History size={18} />
          {searchHistory.length > 0 && (
            <span className="absolute -top-1 -right-1 text-[10px] bg-[#D4AF37] text-[#0a0a0a] px-1.5 py-0.5 rounded-full font-semibold">
              {searchHistory.length}
            </span>
          )}
        </button>
        <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-[#a0a0a0] hover:text-[#E8E8E8] hover:bg-[#1a1a1a] transition-all relative">
          <Bookmark size={18} />
          {bookmarks.length > 0 && (
            <span className="absolute -top-1 -right-1 text-[10px] bg-[#D4AF37] text-[#0a0a0a] px-1.5 py-0.5 rounded-full font-semibold">
              {bookmarks.length}
            </span>
          )}
        </button>
      </nav>

      <div className="flex items-center gap-2 px-3 py-2 bg-[#1a1a1a] rounded-lg">
        <span className="w-2 h-2 bg-[#22c55e] rounded-full animate-pulse" />
        <span className="text-xs text-[#a0a0a0]">API Connected</span>
      </div>
    </header>
  )
}