'use client'

import { X, FileText, ExternalLink } from 'lucide-react'
import { SourceReference } from '@/lib/store'

interface DocumentPanelProps {
  source: SourceReference
  onClose: () => void
}

export function DocumentPanel({ source, onClose }: DocumentPanelProps) {
  const highlightCount = source.highlightRanges.length

  return (
    <div className="flex h-full w-[420px] shrink-0 flex-col overflow-hidden rounded-[28px] border border-slate bg-cream shadow-[0_24px_80px_rgba(0,0,0,0.3)]">
      <div className="border-b border-slate/60 p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="mb-1 text-[10px] uppercase tracking-[0.18em] text-gold">Source Document</div>
            <h2 className="mb-1 text-[15px] font-serif text-gold-light">{source.bookTitle}</h2>
            <p className="text-[11px] text-silver/40">{source.author}</p>
          </div>
          <button
            className="rounded-lg p-2 text-silver transition-all hover:bg-charcoal hover:text-[#e8e8e8]"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3 border-b border-slate/40 bg-charcoal/30 px-6 py-4">
        <span className="rounded border border-gold/30 bg-gold/10 px-2 py-1 text-[10px] text-gold">
          {source.act}
        </span>
        {source.chapter && (
          <span className="truncate text-[11px] text-silver/60">{source.chapter}</span>
        )}
      </div>

      <div className="flex items-center justify-between border-b border-slate/40 px-6 py-4">
        <div className="flex min-w-0 items-center gap-2">
          <FileText className="h-4 w-4 text-silver/50" />
          <span className="truncate text-[13px] text-[#e8e8e8]">{source.section || 'Section'}</span>
        </div>
        <div className="ml-4 flex shrink-0 items-center gap-2 text-[11px] text-silver/50">
          <span>Page {source.page}</span>
          <span>Para {source.paragraph}</span>
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

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="rounded-[24px] border border-slate/30 bg-charcoal/18 p-5 font-serif text-[14px] leading-[1.9] tracking-[0.01em] text-silver/70 whitespace-pre-wrap">
          {source.fullText.split('').map((char, index) => {
            const isHighlighted = source.highlightRanges.some(
              range => index >= range.start && index < range.end
            )

            return (
              <span
                key={index}
                className={isHighlighted ? 'border-l-2 border-gold/40 bg-gold/15' : ''}
              >
                {char}
              </span>
            )
          })}
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-slate/40 p-5">
        <div className="flex items-center gap-3">
          <span className={`text-[13px] font-medium ${source.relevanceScore >= 95 ? 'text-success' : source.relevanceScore >= 85 ? 'text-gold' : 'text-silver'}`}>
            {source.relevanceScore}% Match
          </span>
          <span className="rounded bg-charcoal px-2 py-0.5 text-[10px] text-silver/60">
            {source.relevanceScore >= 95 ? 'High' : source.relevanceScore >= 85 ? 'Moderate' : 'Partial'} Confidence
          </span>
        </div>
        <button className="flex items-center gap-1 text-[11px] text-gold transition-colors hover:text-gold-light">
          <ExternalLink className="h-3 w-3" />
          View Original
        </button>
      </div>
    </div>
  )
}
