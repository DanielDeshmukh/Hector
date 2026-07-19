"use client";

import { Scale, Shield, Search, Layers, FileCheck } from "lucide-react";

export default function WelcomeScreen() {
  const features = [
    {
      icon: <Shield size={18} />,
      title: "Intent Routing",
      desc: "Queries classified by legal domain - Criminal, Civil, or Procedural - to prevent data bleeding.",
    },
    {
      icon: <Search size={18} />,
      title: "Hybrid Retrieval",
      desc: "Dual-search combining semantic understanding with keyword precision across 20+ legal texts.",
    },
    {
      icon: <Layers size={18} />,
      title: "Hierarchical Context",
      desc: "Sub-clauses automatically pull parent Section, Chapter, and Act titles for complete context.",
    },
    {
      icon: <FileCheck size={18} />,
      title: "Citation Grounding",
      desc: "Every response verified against source material. Unverified claims are refused, not guessed.",
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      {/* Logo & Title */}
      <div className="mb-10 text-center animate-fade-in">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-xl border border-gold/25 bg-gold/8">
          <Scale size={28} className="text-gold" />
        </div>
        <h1 className="font-serif text-3xl font-semibold tracking-wide text-gold-light">
          HECTOR
        </h1>
        <p className="mt-2 max-w-md text-[13px] leading-relaxed text-silver/50">
          Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval
        </p>
      </div>

      {/* Feature Grid */}
      <div className="grid w-full max-w-2xl grid-cols-1 sm:grid-cols-2 gap-3 animate-fade-in-delay-1">
        {features.map((feature, i) => (
          <div
            key={i}
            className="rounded-xl border border-slate-custom/30 bg-charcoal/30 p-4 transition-colors hover:border-slate-custom/50"
          >
            <div className="flex items-start gap-3">
              <span className="mt-0.5 text-gold/60">{feature.icon}</span>
              <div>
                <p className="text-[13px] font-medium text-silver/80">
                  {feature.title}
                </p>
                <p className="mt-1 text-[11.5px] leading-relaxed text-silver/40">
                  {feature.desc}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Disclaimer */}
      <div className="mt-10 max-w-lg text-center animate-fade-in-delay-3">
        <p className="text-[10.5px] leading-relaxed text-silver/25">
          HECTOR retrieves information exclusively from its curated library of legal
          commentaries and Bare Acts. Responses are not legal advice. Always verify
          with authorised legal counsel.
        </p>
      </div>
    </div>
  );
}
