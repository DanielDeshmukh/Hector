"use client";

import { Shield, Search, Layers, FileCheck } from "lucide-react";

const stages = [
  {
    icon: <Shield size={15} />,
    name: "Intent Routing",
    description: "Classifying legal domain...",
  },
  {
    icon: <Search size={15} />,
    name: "Hybrid Retrieval",
    description: "Searching across legal texts...",
  },
  {
    icon: <Layers size={15} />,
    name: "Hierarchical Context",
    description: "Resolving parent sections & chapters...",
  },
  {
    icon: <FileCheck size={15} />,
    name: "Citation Grounding",
    description: "Verifying against source material...",
  },
];

export default function ProcessingIndicator({
  currentStage,
}) {
  return (
    <div className="animate-fade-in rounded-xl border border-slate-custom/40 bg-charcoal/40 p-6">
      <div className="space-y-3">
        {stages.map((stage, index) => {
          const isActive = index === currentStage;
          const isCompleted = index < currentStage;

          return (
            <div
              key={index}
              className={`flex items-center gap-3 rounded-lg px-3.5 py-2.5 transition-all duration-500 ${
                isActive
                  ? "bg-gold/5 border border-gold/20"
                  : isCompleted
                  ? "opacity-60"
                  : "opacity-25"
              }`}
            >
              <span
                className={`${
                  isActive
                    ? "text-gold"
                    : isCompleted
                    ? "text-success"
                    : "text-silver/30"
                }`}
              >
                {stage.icon}
              </span>
              <div className="flex-1">
                <p
                  className={`text-[12.5px] font-medium ${
                    isActive
                      ? "text-gold-light"
                      : isCompleted
                      ? "text-silver/50"
                      : "text-silver/25"
                  }`}
                >
                  {stage.name}
                </p>
                {isActive && (
                  <p className="text-[11px] text-silver/40 mt-0.5 animate-fade-in">
                    {stage.description}
                  </p>
                )}
              </div>
              {isActive && (
                <div className="flex gap-1">
                  <span
                    className="h-1.5 w-1.5 rounded-full bg-gold animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <span
                    className="h-1.5 w-1.5 rounded-full bg-gold animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <span
                    className="h-1.5 w-1.5 rounded-full bg-gold animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
              )}
              {isCompleted && (
                <span className="text-[10px] text-success font-medium">Done</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
