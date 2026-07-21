"use client";

import { useEffect, useState } from "react";
import { Icons } from "./Icons";

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

export default function HeroSection() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <section className="relative min-h-screen flex items-center pt-20 overflow-hidden bg-cream">
      <div className="relative w-full px-6 lg:px-12 py-20 lg:py-32">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            <div
              className={cn(
                "space-y-8 transition-all duration-1000",
                isVisible
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-8"
              )}
            >
              <div className="space-y-4">
                <h1 className="font-serif text-4xl sm:text-5xl lg:text-6xl font-semibold text-white leading-[1.1] tracking-tight">
                  Zero-Hallucination
                  <span className="block text-gold">Legal Research</span>
                  <span className="block text-stone-500 text-3xl sm:text-4xl lg:text-5xl font-normal mt-2">
                    for Indian Law
                  </span>
                </h1>
                <p className="font-serif italic text-xl text-silver">
                  Hierarchical Evaluation of Civil-Criminal Textual&apos;s
                  Orchestrator &amp; Retrieval
                </p>
              </div>

              <p className="text-lg text-silver leading-relaxed max-w-xl">
                AI-powered legal research engine with chain-of-verification
                technology. Access 13,479+ chunks across 45 bare acts with
                IPC-to-BNS cross-referencing and guaranteed citation accuracy.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <a
                  href="#demo"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gold text-charcoal font-medium rounded-xl hover:bg-gold-light transition-all hover:shadow-xl hover:shadow-gold/20"
                >
                  Start Free Trial
                  <Icons.ArrowRight />
                </a>
                <a
                  href="#technology"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-charcoal text-white font-medium rounded-xl border-2 border-white/10 hover:border-gold-light hover:bg-gold-light/10 transition-all"
                >
                  Learn How It Works
                </a>
              </div>

              <div className="flex items-center gap-6 pt-4 text-sm text-silver">
                <div className="flex items-center gap-2">
                  <Icons.Check />
                  <span>No credit card required</span>
                </div>
                <div className="flex items-center gap-2">
                  <Icons.Check />
                  <span>14-day free trial</span>
                </div>
              </div>
            </div>

            <div
              className={cn(
                "relative transition-all duration-1000 delay-300",
                isVisible
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-8"
              )}
            >
              <div className="relative bg-charcoal rounded-2xl shadow-2xl shadow-black/20 border border-white/10 overflow-hidden">
                <div className="bg-gradient-to-r from-stone-900 to-stone-800 px-6 py-4 flex items-center gap-3">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-400" />
                    <div className="w-3 h-3 rounded-full bg-amber-400" />
                    <div className="w-3 h-3 rounded-full bg-emerald-400" />
                  </div>
                  <div className="flex-1 text-center">
                    <span className="text-silver text-sm font-mono">
                      hector.ai/query
                    </span>
                  </div>
                </div>

                <div className="p-6 space-y-6">
                  <div className="bg-slate-custom rounded-xl p-4 border border-white/5">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-gold-light flex items-center justify-center flex-shrink-0">
                        <Icons.Search />
                      </div>
                      <div>
                        <p className="text-white font-medium">
                          What are the recent amendments to Section 302 IPC
                          under BNS?
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-sm text-silver">
                      <img
                        src="/tab-icon.png"
                        alt="H"
                        className="w-6 h-6 rounded"
                      />
                      <span className="font-medium">HECTOR Response</span>
                      <span className="text-xs bg-success/20 text-success px-2 py-0.5 rounded-full">
                        Verified
                      </span>
                    </div>

                    <div className="bg-slate-custom rounded-xl p-4 space-y-3">
                      <p className="text-white leading-relaxed text-sm">
                        Under the Bharatiya Nyaya Sanhita (BNS) 2023,{" "}
                        <span className="font-semibold text-gold">
                          Section 302 IPC
                        </span>{" "}
                        has been renumbered as{" "}
                        <span className="font-semibold text-gold">
                          Section 103(1)
                        </span>
                        .
                      </p>
                      <div className="bg-charcoal rounded-lg p-3 border-l-4 border-gold text-sm">
                        <p className="text-silver italic">
                          &quot;Whoever commits murder shall be punished with
                          death, or imprisonment for life, and shall also be
                          liable to fine.&quot;
                        </p>
                        <p className="text-xs text-silver/60 mt-2 font-mono">
                          — BNS Section 103(1)
                        </p>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-silver">
                        <Icons.Shield />
                        <span>
                          Citations verified against official BNS 2023 text
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="absolute -bottom-6 -left-6 bg-charcoal rounded-xl shadow-xl border border-white/10 p-4 hidden lg:block">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-success/20 flex items-center justify-center text-success">
                    <Icons.Shield />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">99.7%</p>
                    <p className="text-xs text-silver">Citation Accuracy</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
