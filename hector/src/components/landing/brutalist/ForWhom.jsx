"use client";

import { Gavel, ScrollText, Landmark, BookOpen } from "lucide-react";
import { Reveal, WideHead, WideSection } from "./ui";

/**
 * The four desks this is built for. The query under each is a question the
 * index is actually asked, phrased the way a desk would phrase it.
 */
const FOR = [
  {
    icon: Gavel,
    who: "The bench & the registry",
    what: "Two provisions opened side by side, the old text and the new, with the counterpart resolved by the index rather than assumed by a summary. Nothing has to be taken on trust.",
    query: "compare IPC 302 ⇄ its BNS counterpart",
  },
  {
    icon: ScrollText,
    who: "Litigation desks",
    what: "Charge frames, bail applications and discharge petitions drafted against the provision in force on the date of the offence — which is often not the one in the current edition.",
    query: "does IPC 302 still apply to offences before the new laws?",
  },
  {
    icon: Landmark,
    who: "Chambers & solo practice",
    what: "A citation checked in seconds rather than in a digest that was last printed before the amendment. The answer arrives with the provision attached, not with a paraphrase of it.",
    query: "what does IPC 124A say about sedition, and what is the punishment?",
  },
  {
    icon: BookOpen,
    who: "In-house & regulatory",
    what: "Statutory obligations traced to the section that imposes them. Where two codes govern the same conduct — an old one and its successor — both stay addressable.",
    query: "what is the BNS provision corresponding to IPC 302?",
  },
];

export function ForWhomSection() {
  return (
    <WideSection id="practice" tint>
      <WideHead
        no="07"
        kicker="Where it sits on the desk"
        title={
          <>
            Built for the part of practice
            <span className="block italic text-gold-light">that is reading, not guessing.</span>
          </>
        }
        lede={
          <>
            Hector does not draft your pleading and does not decide your case. It answers the question a bench
            asks fifteen seconds after you cite a section: where is that written, and what does it say.
          </>
        }
      />
      <div className="mt-10 grid gap-px bg-hair md:grid-cols-2">
        {FOR.map((f, i) => (
          <Reveal key={f.who} delay={i * 70} className="bg-cream">
            <div className="group h-full px-5 py-6 transition-colors duration-300 hover:bg-panel/60">
              <div className="flex items-center gap-3">
                <span className="grid h-8 w-8 place-items-center border border-slate-custom text-gold transition-colors duration-300 group-hover:border-gold/70">
                  <f.icon className="h-4 w-4" strokeWidth={1.4} />
                </span>
                <h3 className="font-display text-[22px] leading-none tracking-tight text-paper">{f.who}</h3>
                <span className="ml-auto font-mono text-[10px] text-muted">{String(i + 1).padStart(2, "0")}</span>
              </div>
              <p className="mt-3 max-w-[54ch] text-[13.5px] leading-[1.7] text-silver">{f.what}</p>
              <p className="mt-4 inline-flex items-center gap-2 border border-hair px-2.5 py-1.5 font-mono text-[11px] text-silver/80 transition-colors duration-300 group-hover:border-gold/50 group-hover:text-gold-light">
                <span className="text-muted">q&gt;</span>
                {f.query}
              </p>
            </div>
          </Reveal>
        ))}
      </div>
      <p className="mt-6 max-w-[76ch] font-mono text-[10.5px] leading-[1.7] text-muted">
        The four questions above are the kind this index is asked. They are not answered on this page by a
        stored response — run any of them in the hero console and you will get whatever the live index returns
        for your wording.
      </p>
    </WideSection>
  );
}
