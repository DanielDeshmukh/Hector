import { Check, Loader2, Circle, Tag, BarChart3, ExternalLink, BookOpen, FileText, ArrowRight } from 'lucide-react'
import useAppStore from '../lib/store'

function formatResponseText(text) {
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

function getScoreColor(score) {
  if (score >= 95) return 'text-success'
  if (score >= 85) return 'text-gold'
  return 'text-silver'
}

function getScoreBg(score) {
  if (score >= 95) return 'bg-success/10 border-success/30'
  if (score >= 85) return 'bg-gold/10 border-gold/30'
  return 'bg-slate/30 border-slate/40'
}

function ResponseDisplay({ response, onSourceClick }) {
  const { activeSourceId } = useAppStore()

  return (
    <div className="mx-auto w-full max-w-7xl px-8 py-8 sm:px-10 lg:px-14">
      <div className="grid gap-10 xl:grid-cols-[minmax(0,1.1fr)_340px] xl:items-start">
        <div className="min-w-0">
          <div className="mb-10">
            <div className="mb-4 text-[10px] uppercase tracking-[0.2em] text-silver/50 font-semibold">Chain of Verification</div>
            <div className="flex flex-wrap items-center gap-3">
              {response.pipeline.map((stage, index) => (
                <div key={stage.id} className="flex items-center">
                  <div
                    className={`flex items-center gap-2.5 rounded-full border px-4 py-2 text-xs font-medium transition-all ${
                      stage.status === 'completed'
                        ? 'bg-success/15 border-success/40 text-success'
                        : stage.status === 'active'
                          ? 'bg-gold/15 border-gold/40 text-gold'
                          : 'bg-slate/20 border-slate/30 text-silver/40'
                    }`}
                  >
                    {stage.status === 'completed' && <Check className="h-3.5 w-3.5" />}
                    {stage.status === 'active' && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                    {stage.status === 'pending' && <Circle className="h-3.5 w-3.5" />}
                    <span className="hidden sm:inline font-medium">{stage.name}</span>
                  </div>
                  {index < response.pipeline.length - 1 && (
                    <ArrowRight className="mx-2 h-4 w-4 text-silver/25" />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="mb-10 rounded-[30px] border border-slate/40 bg-charcoal/50 p-8 sm:p-9">
            <div className="font-serif text-[15px] leading-relaxed text-[#e8e8e8] whitespace-pre-wrap">
              {formatResponseText(response.answer)}
            </div>
          </div>

          <div>
            <div className="mb-5 text-[10px] uppercase tracking-[0.2em] text-silver/50 font-semibold">
              Verified Sources ({response.sources.length})
            </div>
            <div className="grid grid-cols-1 gap-4">
              {response.sources.map((source, index) => {
                const isActive = activeSourceId === source.id
                return (
                  <button
                    key={source.id}
                    className={`w-full rounded-2xl border p-5 text-left transition-all ${
                      isActive
                        ? 'bg-gold/8 border-gold/50 shadow-[0_4px_12px_rgba(201,169,98,0.08)]'
                        : 'bg-charcoal/40 border-slate/40 hover:border-gold/40 hover:bg-charcoal/60'
                    }`}
                    onClick={() => onSourceClick(source)}
                  >
                    <div className="flex items-start gap-4">
                      <div
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[12px] font-bold font-mono transition-all ${
                          isActive ? 'bg-gold/25 text-gold border border-gold/30' : 'bg-slate/50 text-silver/70 border border-slate/30'
                        }`}
                      >
                        {index + 1}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className={`text-[14px] font-semibold mb-1 ${isActive ? 'text-gold-light' : 'text-[#e8e8e8]'}`}>
                          {source.bookTitle}
                        </div>
                        <div className="mb-2 text-[11px] text-silver/50 font-medium">{source.author}</div>
                        <div className="mb-3 line-clamp-2 text-[12px] text-silver/60">
                          {source.matchedText}
                        </div>
                        <div className="flex flex-wrap items-center gap-4 text-[11px] text-silver/50">
                          {source.section && (
                            <span className="flex items-center gap-1.5">
                              <FileText className="h-3.5 w-3.5" />
                              {source.section}
                            </span>
                          )}
                          {source.chapter && (
                            <span className="flex items-center gap-1.5">
                              <BookOpen className="h-3.5 w-3.5" />
                              {source.chapter}
                            </span>
                          )}
                          <span>Page {source.page}</span>
                          <span>Para {source.paragraph}</span>
                        </div>
                      </div>

                      <div className="flex shrink-0 items-start gap-3">
                        <div
                          className={`rounded-lg border px-3 py-1.5 text-[11px] font-semibold transition-all ${getScoreBg(source.relevanceScore)} ${getScoreColor(source.relevanceScore)}`}
                        >
                          {source.relevanceScore}%
                        </div>
                        <ExternalLink className="h-4 w-4 shrink-0 text-silver/50 mt-0.5" />
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        <aside className="xl:sticky xl:top-8">
          <div className="rounded-[30px] border border-slate/40 bg-charcoal/50 p-6 sm:p-7">
            <div className="mb-5 text-[10px] uppercase tracking-[0.2em] text-silver/50 font-semibold">Response Metadata</div>
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 rounded-full border border-gold/40 bg-gold/5 px-4 py-2">
                <Tag className="h-3.5 w-3.5 text-gold" />
                <span className="text-xs font-medium text-gold">{response.domain}</span>
              </div>
              <div className="flex items-center gap-2 rounded-full border border-success/40 bg-success/5 px-4 py-2">
                <BarChart3 className="h-3.5 w-3.5 text-success" />
                <span className="text-xs font-medium text-success">{Math.round(response.confidence * 100)}%</span>
              </div>
            </div>
            <div className="mt-6 text-[11px] leading-relaxed text-silver/50 font-medium">
              {new Date(response.timestamp).toLocaleString('en-IN', {
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </div>
            <div className="mt-7 rounded-2xl border border-slate/40 bg-charcoal/50 p-5">
              <div className="text-[10px] uppercase tracking-[0.2em] text-silver/50 font-semibold">Sources Ready</div>
              <div className="mt-3 font-serif text-4xl text-gold-light font-bold">{response.sources.length}</div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}

export default ResponseDisplay