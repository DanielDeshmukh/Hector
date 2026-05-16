'use client'

import { Check, Loader2, Circle, Tag, BarChart3, ExternalLink, BookOpen, FileText, ArrowRight } from 'lucide-react'
import { useAppStore, QueryResponse } from '@/lib/store'

interface ResponseDisplayProps {
  response: QueryResponse
  onSourceClick: (source: any) => void
}

function formatResponseText(text: string): JSX.Element {
  // Simple markdown-like formatting
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|- .*?$)/g)
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={i} className="text-gold-light font-semibold">{part.slice(2, -2)}</strong>
        }
        if (part.startsWith('*') && part.endsWith('*')) {
          return <em key={i} className="text-silver italic">{part.slice(1, -1)}</em>
        }
        if (part.startsWith('- ')) {
          return (
            <div key={i} className="flex items-start gap-2 ml-4">
              <span className="text-gold mt-1">•</span>
              <span>{part.slice(2)}</span>
            </div>
          )
        }
        return part
      })}
    </>
  )
}

function getScoreColor(score: number): string {
  if (score >= 95) return 'text-success'
  if (score >= 85) return 'text-gold'
  return 'text-silver'
}

function getScoreBg(score: number): string {
  if (score >= 95) return 'bg-success/10 border-success/30'
  if (score >= 85) return 'bg-gold/10 border-gold/30'
  return 'bg-slate/30 border-slate/40'
}

export function ResponseDisplay({ response, onSourceClick }: ResponseDisplayProps) {
  const { activeSourceId } = useAppStore()

  return (
    <div className="px-6 py-6 overflow-auto">
      {/* Pipeline Status Bar */}
      <div className="mb-6">
        <div className="text-[10px] uppercase tracking-[0.18em] text-silver/50 mb-3">Chain of Verification</div>
        <div className="flex items-center gap-2 flex-wrap">
          {response.pipeline.map((stage, index) => (
            <div key={stage.id} className="flex items-center">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs ${
                stage.status === 'completed'
                  ? 'bg-success/10 border-success/30 text-success'
                  : stage.status === 'active'
                  ? 'bg-gold/10 border-gold/30 text-gold'
                  : 'bg-slate/30 border-slate/40 text-silver/40'
              }`}>
                {stage.status === 'completed' && <Check className="w-3 h-3" />}
                {stage.status === 'active' && <Loader2 className="w-3 h-3 animate-spin" />}
                {stage.status === 'pending' && <Circle className="w-3 h-3" />}
                <span className="hidden sm:inline">{stage.name}</span>
              </div>
              {index < response.pipeline.length - 1 && (
                <ArrowRight className="w-4 h-4 text-silver/30 mx-1" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Domain & Confidence Badges */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center gap-1.5 px-3 py-1 border border-gold/40 rounded-full">
          <Tag className="w-3 h-3 text-gold" />
          <span className="text-xs text-gold">{response.domain}</span>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 border border-success/40 rounded-full">
          <BarChart3 className="w-3 h-3 text-success" />
          <span className="text-xs text-success">{Math.round(response.confidence * 100)}%</span>
        </div>
        <span className="text-[10px] text-silver/30">
          {new Date(response.timestamp).toLocaleString('en-IN', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </span>
      </div>

      {/* Main Response */}
      <div className="mb-8 p-5 bg-charcoal/40 border border-slate/40 rounded-lg">
        <div className="text-[14.5px] text-[#e8e8e8] font-serif leading-relaxed whitespace-pre-wrap">
          {formatResponseText(response.answer)}
        </div>
      </div>

      {/* Source Citations */}
      <div>
        <div className="text-[10px] uppercase tracking-[0.18em] text-silver/50 mb-4">
          Verified Sources ({response.sources.length})
        </div>
        <div className="grid grid-cols-1 gap-3">
          {response.sources.map((source, index) => {
            const isActive = activeSourceId === source.id
            return (
              <button
                key={source.id}
                className={`w-full text-left p-4 rounded-lg border transition-all ${
                  isActive
                    ? 'bg-gold/5 border-gold/40'
                    : 'bg-charcoal/30 border-slate/40 hover:border-gold/30 hover:bg-charcoal/50'
                }`}
                onClick={() => onSourceClick(source)}
              >
                <div className="flex items-start gap-3">
                  {/* Index Badge */}
                  <div className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-mono ${
                    isActive ? 'bg-gold text-cream' : 'bg-slate/50 text-silver'
                  }`}>
                    {index + 1}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className={`text-[13px] font-medium ${isActive ? 'text-gold-light' : 'text-[#e8e8e8]'}`}>
                      {source.bookTitle}
                    </div>
                    <div className="text-[11px] text-silver/40 mb-2">{source.author}</div>
                    <div className="text-[11.5px] text-silver/50 line-clamp-2 mb-2">
                      {source.matchedText}
                    </div>
                    <div className="flex items-center gap-3 text-[10px] text-silver/40">
                      {source.section && (
                        <span className="flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          {source.section}
                        </span>
                      )}
                      {source.chapter && (
                        <span className="flex items-center gap-1">
                          <BookOpen className="w-3 h-3" />
                          {source.chapter}
                        </span>
                      )}
                      <span>Page {source.page}</span>
                      <span>¶ {source.paragraph}</span>
                    </div>
                  </div>

                  {/* Score Badge */}
                  <div className={`shrink-0 px-2 py-1 rounded text-[10px] font-medium border ${getScoreBg(source.relevanceScore)} ${getScoreColor(source.relevanceScore)}`}>
                    {source.relevanceScore}%
                  </div>

                  <ExternalLink className="w-4 h-4 text-silver/40 shrink-0" />
                </div>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}