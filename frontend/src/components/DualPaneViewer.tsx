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
      <div className="flex flex-col items-center justify-center h-full px-6 py-8 text-center">
        <div className="text-gold opacity-50 mb-6">
          <Sparkles size={48} />
        </div>
        <h3 className="text-lg text-[#e8e8e8] mb-2">Ready for Legal Research</h3>
        <p className="text-silver mb-6">Enter a legal query to search the Indian law database</p>
        <div className="flex flex-wrap gap-2 justify-center">
          <span className="px-3 py-1 bg-charcoal border border-slate rounded-lg text-sm text-silver cursor-pointer hover:border-gold hover:text-gold transition-all">Section 302 BNS</span>
          <span className="px-3 py-1 bg-charcoal border border-slate rounded-lg text-sm text-silver cursor-pointer hover:border-gold hover:text-gold transition-all">murder punishment</span>
          <span className="px-3 py-1 bg-charcoal border border-slate rounded-lg text-sm text-silver cursor-pointer hover:border-gold hover:text-gold transition-all">theft IPC</span>
          <span className="px-3 py-1 bg-charcoal border border-slate rounded-lg text-sm text-silver cursor-pointer hover:border-gold hover:text-gold transition-all">bail law</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-125 bg-cream">
      {/* Left Pane: AI Summary */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-2 px-6 py-3 bg-cream border-b border-slate">
          <Sparkles className="text-gold" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-silver">AI Summary</h2>
          <div className="flex gap-1 ml-auto">
            <button className="p-1 text-silver rounded hover:text-gold hover:bg-charcoal transition-all" onClick={handleCopy} title="Copy to clipboard">
              {copied ? <Check size={16} /> : <Copy size={16} />}
            </button>
            <button className="p-1 text-silver rounded hover:text-gold hover:bg-charcoal transition-all" onClick={handleBookmark} title="Bookmark">
              <Bookmark size={16} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {generatedResponse ? (
            <div className="animate-fade-in">
              {generatedResponse.split('\n').map((paragraph, idx) => (
                <p key={idx} className="mb-4 text-[#e8e8e8] leading-relaxed">
                  {paragraph}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-silver italic">No AI-generated summary available. Select a result to view its details.</p>
          )}
        </div>

        {searchResponse && (
          <div className="flex items-center gap-6 px-6 py-2 bg-cream border-t border-slate text-xs">
            <span className="text-silver">Route: <strong className="text-silver font-semibold">{searchResponse.route}</strong></span>
            <span className="text-silver">Results: <strong className="text-silver font-semibold">{searchResponse.total_results}</strong></span>
            {searchResponse.verification_enabled && (
              <span className="text-success font-medium ml-auto">✓ Verified</span>
            )}
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="w-px bg-slate" />

      {/* Right Pane: PDF Source */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-2 px-6 py-3 bg-cream border-b border-slate">
          <FileText className="text-gold" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-silver">Source Document</h2>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {selectedSnippet ? (
            <div className="animate-fade-in">
              <div className="flex flex-wrap gap-2 mb-4">
                {selectedItem?.act ? (
                  <span className="px-2 py-1 bg-gold text-cream text-xs font-semibold rounded">BNS</span>
                ) : null}
                {selectedItem?.metadata?.section_number ? (
                  <span className="px-2 py-1 bg-charcoal text-gold text-xs font-medium border border-gold rounded">Section {String(selectedItem.metadata.section_number)}</span>
                ) : null}
                {selectedItem?.metadata?.chapter ? (
                  <span className="px-2 py-1 bg-charcoal text-silver text-xs rounded">{String(selectedItem.metadata.chapter)}</span>
                ) : null}
              </div>
              <div className="p-4 bg-charcoal border border-slate rounded-lg text-[#e8e8e8] leading-relaxed text-[15px]">
                {selectedSnippet}
              </div>
              {selectedItem?.reasons && selectedItem.reasons.length > 0 && (
                <div className="mt-4 p-3 bg-charcoal rounded-lg">
                  <h4 className="text-xs text-silver uppercase tracking-wider mb-2">Match Reasons:</h4>
                  <ul className="list-none p-0">
                    {selectedItem.reasons.map((reason, idx) => (
                      <li key={idx} className="text-sm text-silver py-1">• {reason}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-50 text-silver">
              <FileText size={32} />
              <p className="mt-3 text-sm">Select a result from the list to view its source document</p>
            </div>
          )}
        </div>

        {selectedItem?.metadata?.source ? (
          <div className="flex items-center gap-6 px-6 py-2 bg-cream border-t border-slate text-xs">
            <span className="text-silver">Source: <strong className="text-silver font-semibold">{String(selectedItem.metadata.source)}</strong></span>
            {selectedItem?.metadata?.page ? (
              <span className="text-silver">Page: <strong className="text-silver font-semibold">{String(selectedItem.metadata.page)}</strong></span>
            ) : null}
            <span className="text-silver">Score: <strong className="text-silver font-semibold">{(selectedItem?.score || 0).toFixed(2)}</strong></span>
          </div>
        ) : null}
      </div>
    </div>
  )
}