"use client";

import { Reveal } from "./ui";

const CLAIMS = [
  [
    "not a paraphrase problem",
    "The model is not inventing the condition. The condition was never in the window it was given.",
  ],
  [
    "not a model-size problem",
    "A larger context window stores the same defect more comfortably. Retrieval still decides what is read.",
  ],
  [
    "a boundary problem",
    "Boundaries in a statute are drawn by text: a number, a marginal note, an em-dash. Regex reads text.",
  ],
];

export function Doctrine() {
  return (
    <section className="relative overflow-hidden border-t border-hair bg-ink">
      <div className="absolute inset-0 rule-grid opacity-60" aria-hidden />
      <div className="relative mx-auto grid max-w-[1400px] gap-10 px-5 py-16 sm:px-8 md:py-20 lg:grid-cols-12">
        <div className="lg:col-span-2">
          <p className="label-xs text-gold">Doctrine</p>
          <p className="mt-3 font-mono text-[10.5px] leading-relaxed text-muted">
            Art. I &mdash;
            <br />
            of the split
          </p>
        </div>
        <div className="lg:col-span-10">
          <Reveal y={false}>
            <p className="font-display text-[clamp(1.9rem,5.2vw,4.4rem)] leading-[0.95] tracking-[-0.03em] text-paper">
              A proviso detached from its section
              <span className="block text-silver/70">
                is <span className="italic text-gold-light">a different law</span> &mdash; and it is still quoted
                as though it were the whole of it.
              </span>
            </p>
          </Reveal>
          <div className="mt-10 grid gap-px bg-hair md:grid-cols-3">
            {CLAIMS.map(([h, b]) => (
              <div key={h} className="group bg-ink px-5 py-5 transition-colors duration-300 hover:bg-panel/70">
                <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-silver transition-colors group-hover:text-gold-light">
                  {h}
                </p>
                <p className="mt-2.5 max-w-[36ch] text-[13.5px] leading-[1.7] text-muted transition-colors group-hover:text-silver">
                  {b}
                </p>
                <span className="mt-4 block h-px w-8 bg-slate-custom transition-all duration-500 group-hover:w-full group-hover:bg-gold/60" />
              </div>
            ))}
          </div>
          <p className="mt-8 max-w-[86ch] border-t border-hair pt-6 text-[14px] leading-[1.8] text-silver/90">
            Retrieval-augmented, stated plainly: a model only ever reads what the index hands it. So the hand-off
            is the whole discipline &mdash; hand over a section, complete, with its provisos and its carve-outs
            and its marginal note attached, and hand over the clause each sentence was taken from.
            <span className="text-gold-light"> Hector exists to make that one step deterministic.</span>
          </p>
        </div>
      </div>
    </section>
  );
}
