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
    <div className="flex h-full w-[440px] shrink-0 flex-col overflow-hidden rounded-[32px] border border-slate/40 bg-cream shadow-[0_32px_96px_rgba(0,0,0,0.32)]">
      <div className="border-b border-slate/40 bg-cream/80 px-7 py-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-gold/70">Source Document</div>
            <h2 className="mb-2 text-[16px] font-serif font-semibold text-gold-light">{source.bookTitle}</h2>
            <p className="text-[12px] font-medium text-silver/50">{source.author}</p>
          </div>
          <button
            className="rounded-lg border border-transparent p-2.5 text-silver/60 transition-all hover:border-slate/40 hover:bg-charcoal/40 hover:text-gold"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      <div className="border-b border-slate/40 bg-charcoal/38 px-7 py-5">
        <div className="mb-4 flex items-center gap-3">
          <span className="rounded-lg border border-gold/40 bg-gold/15 px-3 py-1.5 text-[11px] font-bold text-gold">
            {source.act}
          </span>
          {source.chapter && (
            <span className="truncate text-[12px] font-medium text-silver/60">{source.chapter}</span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2 rounded-2xl border border-slate/35 bg-charcoal/40 px-4 py-3">
            <div className="mb-1 text-[10px] uppercase tracking-[0.16em] text-silver/45">Section</div>
            <div className="flex min-w-0 items-center gap-2.5">
              <FileText className="h-4 w-4 shrink-0 text-gold/60" />
              <span className="truncate text-[13px] font-semibold text-[#e8e8e8]">{source.section || 'Section'}</span>
            </div>
          </div>

          <div className="rounded-2xl border border-slate/35 bg-charcoal/40 px-4 py-3">
            <div className="mb-1 text-[10px] uppercase tracking-[0.16em] text-silver/45">Page</div>
            <div className="text-[13px] font-semibold text-[#e8e8e8]">{source.page}</div>
          </div>

          <div className="rounded-2xl border border-slate/35 bg-charcoal/40 px-4 py-3">
            <div className="mb-1 text-[10px] uppercase tracking-[0.16em] text-silver/45">Paragraph</div>
            <div className="text-[13px] font-semibold text-[#e8e8e8]">{source.paragraph}</div>
          </div>

          {highlightCount > 0 && (
            <div className="col-span-2 rounded-2xl border border-slate/35 bg-charcoal/40 px-4 py-3">
              <div className="mb-1 text-[10px] uppercase tracking-[0.16em] text-silver/45">Highlights</div>
              <div className="text-[13px] font-semibold text-[#e8e8e8]">
                <span className="text-gold">1</span>/{highlightCount}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-7 py-6">
        <div className="rounded-[24px] border border-slate/40 bg-charcoal/60 p-6 font-serif text-[14px] leading-[1.95] tracking-[0.01em] text-silver/75 whitespace-pre-wrap">
          {source.fullText.split('').map((char, index) => {
            const isHighlighted = source.highlightRanges.some(
              range => index >= range.start && index < range.end
            )

            return (
              <span
                key={index}
                className={isHighlighted ? 'bg-gold/20 px-1 [box-shadow:inset_3px_0_0_rgba(201,169,98,0.5)]' : ''}
              >
                {char}
              </span>
            )
          })}
        </div>
      </div>

      <div className="flex items-center justify-between gap-4 border-t border-slate/40 bg-cream/80 px-7 py-5">
        <div className="flex items-center gap-3">
          <span className={`text-[14px] font-bold ${source.relevanceScore >= 95 ? 'text-success' : source.relevanceScore >= 85 ? 'text-gold' : 'text-silver'}`}>
            {source.relevanceScore}%
          </span>
          <span className="rounded-lg border border-slate/40 bg-charcoal/50 px-3 py-1 text-[11px] font-semibold text-silver/70">
            {source.relevanceScore >= 95 ? 'High' : source.relevanceScore >= 85 ? 'Moderate' : 'Partial'} Match
          </span>
        </div>
        <button className="flex items-center gap-2 text-[12px] font-semibold text-gold transition-colors hover:text-gold-light">
          <ExternalLink className="h-4 w-4" />
          View Original
        </button>
      </div>
    </div>
  )
}
