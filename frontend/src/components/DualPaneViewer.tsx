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
        <div className="text-accent-gold opacity-50 mb-6">
          <Sparkles size={48} />
        </div>
        <h3 className="text-lg text-text-primary mb-2">Ready for Legal Research</h3>
        <p className="text-text-muted mb-6">Enter a legal query to search the Indian law database</p>
        <div className="flex flex-wrap gap-2 justify-center">
          <span className="px-3 py-1 bg-bg-tertiary border border-border rounded-lg text-sm text-text-secondary cursor-pointer hover:border-accent-gold hover:text-accent-gold transition-all">Section 302 BNS</span>
          <span className="px-3 py-1 bg-bg-tertiary border border-border rounded-lg text-sm text-text-secondary cursor-pointer hover:border-accent-gold hover:text-accent-gold transition-all">murder punishment</span>
          <span className="px-3 py-1 bg-bg-tertiary border border-border rounded-lg text-sm text-text-secondary cursor-pointer hover:border-accent-gold hover:text-accent-gold transition-all">theft IPC</span>
          <span className="px-3 py-1 bg-bg-tertiary border border-border rounded-lg text-sm text-text-secondary cursor-pointer hover:border-accent-gold hover:text-accent-gold transition-all">bail law</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-125 bg-bg-primary">
      {/* Left Pane: AI Summary */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-2 px-6 py-3 bg-bg-secondary border-b border-border">
          <Sparkles className="text-accent-gold" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-text-secondary">AI Summary</h2>
          <div className="flex gap-1 ml-auto">
            <button className="p-1 text-text-muted rounded hover:text-accent-gold hover:bg-bg-tertiary transition-all" onClick={handleCopy} title="Copy to clipboard">
              {copied ? <Check size={16} /> : <Copy size={16} />}
            </button>
            <button className="p-1 text-text-muted rounded hover:text-accent-gold hover:bg-bg-tertiary transition-all" onClick={handleBookmark} title="Bookmark">
              <Bookmark size={16} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {generatedResponse ? (
            <div className="animate-fade-in">
              {generatedResponse.split('\n').map((paragraph, idx) => (
                <p key={idx} className="mb-4 text-text-primary leading-relaxed">
                  {paragraph}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-text-muted italic">No AI-generated summary available. Select a result to view its details.</p>
          )}
        </div>

        {searchResponse && (
          <div className="flex items-center gap-6 px-6 py-2 bg-bg-secondary border-t border-border text-xs">
            <span className="text-text-muted">Route: <strong className="text-text-secondary font-semibold">{searchResponse.route}</strong></span>
            <span className="text-text-muted">Results: <strong className="text-text-secondary font-semibold">{searchResponse.total_results}</strong></span>
            {searchResponse.verification_enabled && (
              <span className="text-success font-medium ml-auto">✓ Verified</span>
            )}
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="w-px bg-border" />

      {/* Right Pane: PDF Source */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-2 px-6 py-3 bg-bg-secondary border-b border-border">
          <FileText className="text-accent-gold" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-text-secondary">Source Document</h2>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {selectedSnippet ? (
            <div className="animate-fade-in">
              <div className="flex flex-wrap gap-2 mb-4">
                {selectedItem?.act ? (
                  <span className="px-2 py-1 bg-accent-gold text-bg-primary text-xs font-semibold rounded">BNS</span>
                ) : null}
                {selectedItem?.metadata?.section_number ? (
                  <span className="px-2 py-1 bg-bg-tertiary text-accent-gold text-xs font-medium border border-accent-gold rounded">Section {String(selectedItem.metadata.section_number)}</span>
                ) : null}
                {selectedItem?.metadata?.chapter ? (
                  <span className="px-2 py-1 bg-bg-card text-text-secondary text-xs rounded">{String(selectedItem.metadata.chapter)}</span>
                ) : null}
              </div>
              <div className="p-4 bg-bg-card border border-border rounded-lg text-text-primary leading-relaxed text-[15px]">
                {selectedSnippet}
              </div>
              {selectedItem?.reasons && selectedItem.reasons.length > 0 && (
                <div className="mt-4 p-3 bg-bg-tertiary rounded-lg">
                  <h4 className="text-xs text-text-secondary uppercase tracking-wider mb-2">Match Reasons:</h4>
                  <ul className="list-none p-0">
                    {selectedItem.reasons.map((reason, idx) => (
                      <li key={idx} className="text-sm text-text-secondary py-1">• {reason}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-50 text-text-muted">
              <FileText size={32} />
              <p className="mt-3 text-sm">Select a result from the list to view its source document</p>
            </div>
          )}
        </div>

        {selectedItem?.metadata?.source ? (
          <div className="flex items-center gap-6 px-6 py-2 bg-bg-secondary border-t border-border text-xs">
            <span className="text-text-muted">Source: <strong className="text-text-secondary font-semibold">{String(selectedItem.metadata.source)}</strong></span>
            {selectedItem?.metadata?.page ? (
              <span className="text-text-muted">Page: <strong className="text-text-secondary font-semibold">{String(selectedItem.metadata.page)}</strong></span>
            ) : null}
            <span className="text-text-muted">Score: <strong className="text-text-secondary font-semibold">{(selectedItem?.score || 0).toFixed(2)}</strong></span>
          </div>
        ) : null}
      </div>
    </div>
  )
}