import { Check, Loader2, Circle, Shield, Search, Layers, FileCheck } from "lucide-react";

const stageIcons = {
  "Intent Routing": <Shield size={13} />,
  "Hybrid Retrieval": <Search size={13} />,
  "Hierarchical Context": <Layers size={13} />,
  "Citation Grounding": <FileCheck size={13} />,
};

export default function PipelineStatus({ stages }) {
  return (
    <div className="rounded-lg border border-slate-custom/40 bg-cream/80 px-4 py-3">
      <div className="mb-2.5 flex items-center gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-silver/50">
          Chain of Verification
        </span>
      </div>
      <div className="flex items-center gap-1">
        {stages.map((stage, index) => (
          <div key={stage.id} className="flex items-center gap-1">
            <div
              className={`group relative flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] transition-all ${
                stage.status === "completed"
                  ? "bg-success/8 text-success border border-success/15"
                  : stage.status === "active"
                  ? "bg-gold/8 text-gold border border-gold/20"
                  : "bg-slate-custom/20 text-silver/40 border border-transparent"
              }`}
            >
              {stage.status === "completed" ? (
                <Check size={11} strokeWidth={2.5} />
              ) : stage.status === "active" ? (
                <Loader2 size={11} className="animate-spin" />
              ) : (
                <Circle size={11} />
              )}
              <span className="hidden md:inline font-medium">{stage.name}</span>
              {stage.timing != null && (
                <span className="hidden md:inline text-[9px] font-mono opacity-60">
                  {Math.round(stage.timing)}ms
                </span>
              )}
              <span className="md:hidden">{stageIcons[stage.name]}</span>
              
              {/* Tooltip */}
              <div className="invisible group-hover:visible absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 rounded-lg border border-slate-custom/60 bg-charcoal p-2.5 shadow-xl z-20">
                <p className="text-[11px] font-medium text-gold-light mb-1">{stage.name}</p>
                <p className="text-[10px] text-silver leading-relaxed">{stage.detail}</p>
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 h-2 w-2 border-r border-b border-slate-custom/60 bg-charcoal"></div>
              </div>
            </div>
            {index < stages.length - 1 && (
              <div
                className={`h-px w-4 ${
                  stages[index + 1].status !== "pending"
                    ? "bg-success/30"
                    : "bg-slate-custom/30"
                }`}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
