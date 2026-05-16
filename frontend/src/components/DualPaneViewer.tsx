'use client'

import { FileText, Sparkles, Bookmark, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { useAppStore } from '@/lib/store'

export function DualPaneViewer() {
  const { searchResponse, selectedItem, addBookmark } = useAppStore()
  const [copied, setCopied] = useState(false)

  const generatedResponse = searchResponse?.generated_response || ''
  const selectedSnippet = selectedItem?.snippet || ''

  const handleCopy = async () => {
    if (generatedResponse) {
      await navigator.clipboard.writeText(generatedResponse)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleBookmark = () => {
    if (generatedResponse) {
      addBookmark(searchResponse?.query || '', generatedResponse, selectedItem || undefined)
    }
  }

  if (!searchResponse && !selectedItem) {
    return (
      <div className="flex flex-col items-center justify-center h-full px-8 py-12 text-center">
        <div className="text-gold/40 mb-8">
          <Sparkles size={56} />
        </div>
        <h3 className="text-xl text-[#e8e8e8] mb-3 font-semibold">Ready for Legal Research</h3>
        <p className="text-silver/70 mb-8 max-w-md">Enter a legal query to search the Indian law database</p>
        <div className="flex flex-wrap gap-3 justify-center max-w-2xl">
          <span className="px-4 py-2 bg-charcoal/60 border border-slate/40 rounded-xl text-sm text-silver/70 cursor-pointer hover:border-gold/50 hover:text-gold hover:bg-charcoal transition-all font-medium">Section 302 BNS</span>
          <span className="px-4 py-2 bg-charcoal/60 border border-slate/40 rounded-xl text-sm text-silver/70 cursor-pointer hover:border-gold/50 hover:text-gold hover:bg-charcoal transition-all font-medium">murder punishment</span>
          <span className="px-4 py-2 bg-charcoal/60 border border-slate/40 rounded-xl text-sm text-silver/70 cursor-pointer hover:border-gold/50 hover:text-gold hover:bg-charcoal transition-all font-medium">theft IPC</span>
          <span className="px-4 py-2 bg-charcoal/60 border border-slate/40 rounded-xl text-sm text-silver/70 cursor-pointer hover:border-gold/50 hover:text-gold hover:bg-charcoal transition-all font-medium">bail law</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-125 bg-cream">
      {/* Left Pane: AI Summary */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-4 bg-cream border-b border-slate/40">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gold/10 border border-gold/20">
            <Sparkles className="text-gold w-4 h-4" />
          </div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-silver/70">AI Summary</h2>
          <div className="flex gap-1.5 ml-auto">
            <button className="p-2 text-silver/60 rounded-lg hover:text-gold hover:bg-charcoal/60 transition-all border border-transparent hover:border-gold/30" onClick={handleCopy} title="Copy to clipboard">
              {copied ? <Check size={16} /> : <Copy size={16} />}
            </button>
            <button className="p-2 text-silver/60 rounded-lg hover:text-gold hover:bg-charcoal/60 transition-all border border-transparent hover:border-gold/30" onClick={handleBookmark} title="Bookmark">
              <Bookmark size={16} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-7 py-6">
          {generatedResponse ? (
            <div className="animate-fade-in">
              {generatedResponse.split('\n').map((paragraph, idx) => (
                <p key={idx} className="mb-5 text-[#e8e8e8] leading-relaxed text-[14px]">
                  {paragraph}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-silver/60 italic text-sm">No AI-generated summary available. Select a result to view its details.</p>
          )}
        </div>

        {searchResponse && (
          <div className="flex items-center gap-8 px-6 py-3 bg-cream border-t border-slate/40 text-xs font-medium">
            <span className="text-silver/70">Route: <span className="text-silver font-semibold">{searchResponse.route}</span></span>
            <span className="text-silver/70">Results: <span className="text-silver font-semibold">{searchResponse.total_results}</span></span>
            {searchResponse.verification_enabled && (
              <span className="text-success font-bold ml-auto">✓ Verified</span>
            )}
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="w-px bg-slate/40" />

      {/* Right Pane: PDF Source */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-4 bg-cream border-b border-slate/40">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gold/10 border border-gold/20">
            <FileText className="text-gold w-4 h-4" />
          </div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-silver/70">Source Document</h2>
        </div>

        <div className="flex-1 overflow-y-auto px-7 py-6">
          {selectedSnippet ? (
            <div className="animate-fade-in">
              <div className="flex flex-wrap gap-2.5 mb-5">
                {selectedItem?.act ? (
                  <span className="px-3 py-1.5 bg-gold/20 text-gold text-xs font-bold rounded-lg border border-gold/30">BNS</span>
                ) : null}
                {selectedItem?.metadata?.section_number ? (
                  <span className="px-3 py-1.5 bg-charcoal/60 text-gold/90 text-xs font-bold border border-gold/30 rounded-lg">Section {String(selectedItem.metadata.section_number)}</span>
                ) : null}
                {selectedItem?.metadata?.chapter ? (
                  <span className="px-3 py-1.5 bg-charcoal/60 text-silver/70 text-xs rounded-lg border border-slate/30">{String(selectedItem.metadata.chapter)}</span>
                ) : null}
              </div>
              <div className="p-5 bg-charcoal/60 border border-slate/40 rounded-2xl text-[#e8e8e8] leading-relaxed text-[14px]">
                {selectedSnippet}
              </div>
              {selectedItem?.reasons && selectedItem.reasons.length > 0 && (
                <div className="mt-6 p-5 bg-charcoal/50 rounded-2xl border border-slate/40">
                  <h4 className="text-xs text-silver/70 uppercase tracking-wider mb-3 font-semibold">Match Reasons:</h4>
                  <ul className="list-none p-0 space-y-2">
                    {selectedItem.reasons.map((reason, idx) => (
                      <li key={idx} className="text-sm text-silver/70">• {reason}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-50 text-silver/50">
              <FileText size={36} />
              <p className="mt-4 text-sm font-medium">Select a result from the list to view its source document</p>
            </div>
          )}
        </div>

        {selectedItem?.metadata?.source ? (
          <div className="flex items-center gap-8 px-6 py-3 bg-cream border-t border-slate/40 text-xs font-medium">
            <span className="text-silver/70">Source: <span className="text-silver font-semibold">{String(selectedItem.metadata.source)}</span></span>
            {selectedItem?.metadata?.page ? (
              <span className="text-silver/70">Page: <span className="text-silver font-semibold">{String(selectedItem.metadata.page)}</span></span>
            ) : null}
            <span className="text-silver/70">Score: <span className="text-silver font-semibold">{(selectedItem?.score || 0).toFixed(2)}</span></span>
          </div>
        ) : null}
      </div>
    </div>
  )
}