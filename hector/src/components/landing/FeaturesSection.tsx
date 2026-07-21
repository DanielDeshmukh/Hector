"use client";

import { useState } from "react";
import { Icons } from "./Icons";

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

const features = [
  {
    icon: Icons.Search,
    title: "Intelligent Legal Search",
    description:
      "Natural language queries across 38+ bare acts with semantic understanding of legal terminology and context.",
    details: [
      "Semantic search across 13,479+ legal chunks",
      "Context-aware query interpretation",
      "Cross-reference detection",
      "Section and clause extraction",
    ],
  },
  {
    icon: Icons.Link,
    title: "IPC to BNS Cross-Referencing",
    description:
      "Seamless mapping between Indian Penal Code sections and their equivalents in the Bharatiya Nyaya Sanhita 2023.",
    details: [
      "Complete IPC-to-BNS mapping",
      "Amendment tracking since 2023",
      "Transitional provision alerts",
      "Dual-code compatibility mode",
    ],
  },
  {
    icon: Icons.Shield,
    title: "Chain-of-Verification",
    description:
      "Every citation is verified against primary sources before being presented in your research results.",
    details: [
      "Multi-layer verification pipeline",
      "Primary source validation",
      "Citation existence checking",
      "Auto-flagging of anomalies",
    ],
  },
  {
    icon: Icons.FileText,
    title: "Cited Responses Only",
    description:
      "Receive answers with precise citations to bare acts, sections, and subsections—never fabricated references.",
    details: [
      "Hyperlinked citations to source",
      "Exportable citation lists",
      "Batch verification reports",
      "Court-ready documentation",
    ],
  },
];

export default function FeaturesSection() {
  const [activeFeature, setActiveFeature] = useState(0);

  return (
    <section id="features" className="py-24 lg:py-32 bg-charcoal">
      <div className="w-full px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="inline-block px-4 py-1.5 bg-gold-light/50 text-gold text-sm font-medium rounded-full mb-4">
              Core Capabilities
            </span>
            <h2 className="font-serif text-3xl lg:text-5xl font-semibold text-white mb-6">
              Built for Legal Precision
            </h2>
            <p className="text-lg text-silver">
              HECTOR combines advanced AI with rigorous verification protocols
              to deliver research you can confidently cite in court.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8 lg:gap-16">
            <div className="space-y-4">
              {features.map((feature, index) => (
                <button
                  key={feature.title}
                  onClick={() => setActiveFeature(index)}
                  className={cn(
                    "w-full text-left p-6 rounded-xl transition-all duration-300",
                    activeFeature === index
                      ? "bg-slate-custom border-2 border-gold-light shadow-lg"
                      : "bg-charcoal border-2 border-white/5 hover:bg-slate-custom"
                  )}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={cn(
                        "w-12 h-12 rounded-xl flex items-center justify-center transition-colors",
                        activeFeature === index
                          ? "bg-gold text-charcoal"
                          : "bg-slate-custom text-silver"
                      )}
                    >
                      <feature.icon />
                    </div>
                    <div className="flex-1">
                      <h3
                        className={cn(
                          "font-semibold text-lg mb-1",
                          activeFeature === index ? "text-white" : "text-silver"
                        )}
                      >
                        {feature.title}
                      </h3>
                      <p className="text-silver text-sm">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="lg:sticky lg:top-24 h-fit">
              <div className="bg-gradient-to-br from-slate-custom to-charcoal rounded-2xl p-8 text-white border border-white/5">
                <div className="w-14 h-14 rounded-xl bg-gold flex items-center justify-center mb-6">
                  {(() => {
                    const IconComponent = features[activeFeature].icon;
                    return <IconComponent />;
                  })()}
                </div>
                <h3 className="font-serif text-2xl font-semibold mb-4">
                  {features[activeFeature].title}
                </h3>
                <p className="text-silver mb-8 leading-relaxed">
                  {features[activeFeature].description}
                </p>

                <div className="space-y-3">
                  {features[activeFeature].details.map((detail, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className="w-5 h-5 rounded-full bg-success/20 flex items-center justify-center flex-shrink-0">
                        <Icons.Check />
                      </div>
                      <span className="text-white/80">{detail}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
