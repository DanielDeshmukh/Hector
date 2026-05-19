import { Shield, Search, Layers, FileCheck, Check, Loader2 } from 'lucide-react'

const ICON_MAP = {
  Shield,
  Search,
  Layers,
  FileCheck,
}

function ProcessingIndicator({ query, currentStage, stages }) {
  return (
    <div className="mx-auto flex min-h-full w-full max-w-7xl items-center px-8 py-12 sm:px-10 lg:px-14">
      <div className="grid w-full gap-10 lg:grid-cols-[minmax(320px,0.95fr)_minmax(0,1.15fr)] lg:gap-12 lg:items-start">
        <div className="rounded-[30px] border border-slate/40 bg-charcoal/50 p-8 sm:p-9 lg:sticky lg:top-8">
          <div className="mb-4 text-[10px] uppercase tracking-[0.2em] text-silver/50 font-semibold">Your Query</div>
          <div className="rounded-2xl border border-slate/40 bg-charcoal/60 p-6">
            <p className="font-serif text-[16px] leading-relaxed text-[#e8e8e8]">{query}</p>
          </div>

          <div className="mt-8 flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-gold animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="h-2.5 w-2.5 rounded-full bg-gold animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="h-2.5 w-2.5 rounded-full bg-gold animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>

        <div className="min-w-0">
          <div className="mb-5 text-[10px] uppercase tracking-[0.2em] text-silver/50 font-semibold">Processing Pipeline</div>
          <div className="flex flex-col gap-4">
          {stages.map((stage, index) => {
            const IconComponent = ICON_MAP[stage.icon] || Shield
            const isActive = index === currentStage - 1
            const isCompleted = index < currentStage - 1

            return (
              <div
                key={stage.id}
                className={`flex items-center gap-5 p-5 rounded-2xl border transition-all ${
                  isActive
                    ? 'bg-gold/10 border-gold/30 shadow-[0_4px_12px_rgba(201,169,98,0.1)]'
                    : isCompleted
                    ? 'bg-charcoal/50 border-slate/40'
                    : 'bg-charcoal/30 border-slate/30'
                }`}
              >
                <div className={`shrink-0 flex items-center justify-center w-10 h-10 rounded-lg transition-all ${isActive ? 'bg-gold/20 border border-gold/30' : isCompleted ? 'bg-success/20 border border-success/30' : 'bg-slate/40 border border-slate/30'}`}>
                  {isCompleted ? (
                    <Check className="w-4 h-4 text-success" />
                  ) : isActive ? (
                    <Loader2 className="w-4 h-4 text-gold animate-spin" />
                  ) : (
                    <IconComponent className={`w-4 h-4 ${isActive ? 'text-gold' : isCompleted ? 'text-success' : 'text-silver/40'}`} />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className={`text-[14px] font-semibold mb-1 ${isActive ? 'text-gold-light' : isCompleted ? 'text-silver/70' : 'text-silver/40'}`}>
                    {stage.name}
                  </div>
                  <div className={`text-[12px] ${isActive ? 'text-gold/80' : isCompleted ? 'text-silver/50' : 'text-silver/30'}`}>
                    {stage.detail}
                  </div>
                </div>

                <div className={`text-[11px] font-bold uppercase tracking-widest whitespace-nowrap px-3 py-1.5 rounded-lg transition-all ${
                  isCompleted ? 'text-success bg-success/10' : isActive ? 'text-gold bg-gold/10' : 'text-silver/40 bg-slate/20'
                }`}>
                  {isCompleted ? 'Done' : isActive ? 'Active' : 'Pending'}
                </div>
              </div>
            )
          })}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProcessingIndicator