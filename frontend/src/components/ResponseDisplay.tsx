'use client'

import { Check, Loader2, Circle, Tag, BarChart3, ExternalLink, BookOpen, FileText, ArrowRight } from 'lucide-react'
import { useAppStore, QueryResponse } from '@/lib/store'

interface ResponseDisplayProps {
  response: QueryResponse
  onSourceClick: (source: any) => void
}

function formatResponseText(text: string): JSX.Element {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|- .*?$)/g)
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={i} className="font-semibold text-gold-light">{part.slice(2, -2)}</strong>
        }
        if (part.startsWith('*') && part.endsWith('*')) {
          return <em key={i} className="italic text-silver">{part.slice(1, -1)}</em>
        }
        if (part.startsWith('- ')) {
          return (
            <div key={i} className="ml-4 flex items-start gap-2">
              <span className="mt-1 text-gold">-</span>
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
    <div className="mx-auto w-full max-w-7xl px-6 py-6 sm:px-8 lg:px-12">
      <div className="grid gap-8 xl:grid-cols-[minmax(0,1.05fr)_320px] xl:items-start">
        <div className="min-w-0">
          <div className="mb-8">
            <div className="mb-3 text-[10px] uppercase tracking-[0.18em] text-silver/50">Chain of Verification</div>
            <div className="flex flex-wrap items-center gap-2">
              {response.pipeline.map((stage, index) => (
                <div key={stage.id} className="flex items-center">
                  <div
                    className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs ${
                      stage.status === 'completed'
                        ? 'bg-success/10 border-success/30 text-success'
                        : stage.status === 'active'
                          ? 'bg-gold/10 border-gold/30 text-gold'
                          : 'bg-slate/30 border-slate/40 text-silver/40'
                    }`}
                  >
                    {stage.status === 'completed' && <Check className="h-3 w-3" />}
                    {stage.status === 'active' && <Loader2 className="h-3 w-3 animate-spin" />}
                    {stage.status === 'pending' && <Circle className="h-3 w-3" />}
                    <span className="hidden sm:inline">{stage.name}</span>
                  </div>
                  {index < response.pipeline.length - 1 && (
                    <ArrowRight className="mx-1 h-4 w-4 text-silver/30" />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="mb-8 rounded-[28px] border border-slate/40 bg-charcoal/40 p-6 sm:p-7">
            <div className="font-serif text-[14.5px] leading-relaxed text-[#e8e8e8] whitespace-pre-wrap">
              {formatResponseText(response.answer)}
            </div>
          </div>

          <div>
            <div className="mb-4 text-[10px] uppercase tracking-[0.18em] text-silver/50">
              Verified Sources ({response.sources.length})
            </div>
            <div className="grid grid-cols-1 gap-3">
              {response.sources.map((source, index) => {
                const isActive = activeSourceId === source.id
                return (
                  <button
                    key={source.id}
                    className={`w-full rounded-2xl border p-4 text-left transition-all ${
                      isActive
                        ? 'bg-gold/5 border-gold/40'
                        : 'bg-charcoal/30 border-slate/40 hover:border-gold/30 hover:bg-charcoal/50'
                    }`}
                    onClick={() => onSourceClick(source)}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[11px] font-mono ${
                          isActive ? 'bg-gold text-cream' : 'bg-slate/50 text-silver'
                        }`}
                      >
                        {index + 1}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className={`text-[13px] font-medium ${isActive ? 'text-gold-light' : 'text-[#e8e8e8]'}`}>
                          {source.bookTitle}
                        </div>
                        <div className="mb-2 text-[11px] text-silver/40">{source.author}</div>
                        <div className="mb-2 line-clamp-2 text-[11.5px] text-silver/50">
                          {source.matchedText}
                        </div>
                        <div className="flex flex-wrap items-center gap-3 text-[10px] text-silver/40">
                          {source.section && (
                            <span className="flex items-center gap-1">
                              <FileText className="h-3 w-3" />
                              {source.section}
                            </span>
                          )}
                          {source.chapter && (
                            <span className="flex items-center gap-1">
                              <BookOpen className="h-3 w-3" />
                              {source.chapter}
                            </span>
                          )}
                          <span>Page {source.page}</span>
                          <span>Para {source.paragraph}</span>
                        </div>
                      </div>

                      <div className="flex shrink-0 items-start gap-3">
                        <div
                          className={`rounded border px-2 py-1 text-[10px] font-medium ${getScoreBg(source.relevanceScore)} ${getScoreColor(source.relevanceScore)}`}
                        >
                          {source.relevanceScore}%
                        </div>
                        <ExternalLink className="h-4 w-4 shrink-0 text-silver/40" />
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        <aside className="xl:sticky xl:top-6">
          <div className="rounded-[28px] border border-slate/40 bg-charcoal/28 p-5">
            <div className="mb-4 text-[10px] uppercase tracking-[0.18em] text-silver/50">Response Metadata</div>
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1.5 rounded-full border border-gold/40 px-3 py-1">
                <Tag className="h-3 w-3 text-gold" />
                <span className="text-xs text-gold">{response.domain}</span>
              </div>
              <div className="flex items-center gap-1.5 rounded-full border border-success/40 px-3 py-1">
                <BarChart3 className="h-3 w-3 text-success" />
                <span className="text-xs text-success">{Math.round(response.confidence * 100)}%</span>
              </div>
            </div>
            <div className="mt-5 text-[11px] leading-relaxed text-silver/45">
              {new Date(response.timestamp).toLocaleString('en-IN', {
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </div>
            <div className="mt-6 rounded-2xl border border-slate/30 bg-charcoal/35 p-4">
              <div className="text-[10px] uppercase tracking-[0.18em] text-silver/40">Sources Ready</div>
              <div className="mt-2 font-serif text-3xl text-gold-light">{response.sources.length}</div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
