'use client'

import { X, FileText, BookOpen, ChevronUp, ChevronDown, ExternalLink } from 'lucide-react'
import { SourceReference } from '@/lib/store'

interface DocumentPanelProps {
  source: SourceReference
  onClose: () => void
}

export function DocumentPanel({ source, onClose }: DocumentPanelProps) {
  const highlightCount = source.highlightRanges.length

  return (
    <div className="w-[420px] shrink-0 bg-cream border-l border-slate flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-slate/60">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-gold mb-1">Source Document</div>
            <h2 className="text-[15px] font-serif text-gold-light mb-1">{source.bookTitle}</h2>
            <p className="text-[11px] text-silver/40">{source.author}</p>
          </div>
          <button
            className="p-2 rounded-lg text-silver hover:text-[#e8e8e8] hover:bg-charcoal transition-all"
            onClick={onClose}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Metadata Bar */}
      <div className="px-5 py-3 bg-charcoal/30 border-b border-slate/40 flex items-center gap-3">
        <span className="px-2 py-1 text-[10px] bg-gold/10 text-gold border border-gold/30 rounded">
          {source.act}
        </span>
        {source.chapter && (
          <span className="text-[11px] text-silver/60">{source.chapter}</span>
        )}
      </div>

      {/* Section Navigation */}
      <div className="px-5 py-3 border-b border-slate/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-silver/50" />
          <span className="text-[13px] text-[#e8e8e8]">{source.section || 'Section'}</span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-silver/50">
          <span>Page {source.page}</span>
          <span>¶ {source.paragraph}</span>
          {highlightCount > 0 && (
            <>
              <span className="text-silver/30">|</span>
              <span className="flex items-center gap-1">
                <span className="text-gold">1</span>/{highlightCount}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Document Content */}
      <div className="flex-1 overflow-y-auto p-5">
        <div className="font-serif text-[14px] leading-[1.9] tracking-[0.01em] text-silver/70 whitespace-pre-wrap">
          {source.fullText.split('').map((char, index) => {
            // Check if this index is in any highlight range
            const isHighlighted = source.highlightRanges.some(
              range => index >= range.start && index < range.end
            )
            return (
              <span
                key={index}
                className={isHighlighted ? 'bg-gold/15 border-l-2 border-gold/40' : ''}
              >
                {char}
              </span>
            )
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate/40 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`text-[13px] font-medium ${source.relevanceScore >= 95 ? 'text-success' : source.relevanceScore >= 85 ? 'text-gold' : 'text-silver'}`}>
            {source.relevanceScore}% Match
          </span>
          <span className="px-2 py-0.5 text-[10px] bg-charcoal rounded text-silver/60">
            {source.relevanceScore >= 95 ? 'High' : source.relevanceScore >= 85 ? 'Moderate' : 'Partial'} Confidence
          </span>
        </div>
        <button className="flex items-center gap-1 text-[11px] text-gold hover:text-gold-light transition-colors">
          <ExternalLink className="w-3 h-3" />
          View Original
        </button>
      </div>
    </div>
  )
}