'use client'

import { Shield, Search, Layers, FileCheck, Check, Loader2 } from 'lucide-react'

interface ProcessingStage {
  id: string
  name: string
  detail: string
  icon: string
}

interface ProcessingIndicatorProps {
  query: string
  currentStage: number
  stages: ProcessingStage[]
}

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Shield,
  Search,
  Layers,
  FileCheck,
}

export function ProcessingIndicator({ query, currentStage, stages }: ProcessingIndicatorProps) {
  return (
    <div className="mx-auto flex min-h-full w-full max-w-7xl items-center px-6 py-10 sm:px-8 lg:px-12">
      <div className="grid w-full gap-8 lg:grid-cols-[minmax(320px,0.9fr)_minmax(0,1.1fr)] lg:items-start">
        <div className="rounded-[28px] border border-slate/40 bg-charcoal/35 p-6 sm:p-8 lg:sticky lg:top-8">
          <div className="mb-3 text-[10px] uppercase tracking-[0.18em] text-silver/50">Your Query</div>
          <div className="rounded-2xl border border-slate/40 bg-charcoal/60 p-5">
            <p className="font-serif text-[15px] leading-relaxed text-[#e8e8e8]">{query}</p>
          </div>

          <div className="mt-8 flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>

        <div className="min-w-0">
          <div className="mb-4 text-[10px] uppercase tracking-[0.18em] text-silver/50">Processing Pipeline</div>
          <div className="flex flex-col gap-3">
          {stages.map((stage, index) => {
            const IconComponent = ICON_MAP[stage.icon] || Shield
            const isActive = index === currentStage - 1
            const isCompleted = index < currentStage - 1
            const isPending = index > currentStage - 1

            return (
              <div
                key={stage.id}
                className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                  isActive
                    ? 'bg-gold/5 border-gold/20'
                    : isCompleted
                    ? 'bg-charcoal/30 border-slate/30'
                    : 'bg-charcoal/20 border-slate/20'
                }`}
              >
                {/* Icon */}
                <div className={`shrink-0 ${isActive ? 'text-gold' : isCompleted ? 'text-success' : 'text-silver/30'}`}>
                  {isCompleted ? (
                    <Check className="w-[15px] h-[15px]" />
                  ) : isActive ? (
                    <Loader2 className="w-[15px] h-[15px] animate-spin" />
                  ) : (
                    <IconComponent className="w-[15px] h-[15px]" />
                  )}
                </div>

                {/* Stage Info */}
                <div className="flex-1">
                  <div className={`text-[13px] font-medium ${isActive ? 'text-gold-light' : isCompleted ? 'text-silver/60' : 'text-silver/25'}`}>
                    {stage.name}
                  </div>
                  <div className={`text-[11px] ${isActive ? 'text-gold/70' : 'text-silver/40'}`}>
                    {stage.detail}
                  </div>
                </div>

                {/* Status Label */}
                <div className={`text-[10px] uppercase tracking-wider ${
                  isCompleted ? 'text-success' : isActive ? 'text-gold' : 'text-silver/25'
                }`}>
                  {isCompleted ? 'Done' : isActive ? 'Processing...' : 'Pending'}
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
