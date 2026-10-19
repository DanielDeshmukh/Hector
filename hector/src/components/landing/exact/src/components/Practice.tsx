import { useMemo, useState } from "react";
import { ChevronDown, Check, Minus, Mail, BookOpen as BookMarked, Gavel, Landmark, ScrollText } from "lucide-react";
import { cn } from "../utils/cn";
import { Btn, Panel, Reveal, SectionShell, Tag, WideHead, WideSection } from "./ui";
import { ACCESS, FAQ, PIPELINE, byId } from "../data/corpus";
import { canon, digest } from "../lib/text";
import { TOTAL_ACTS } from "../data/acts";

/* =================================================================== *
 * 06 — pipeline + citation ledger
 * =================================================================== */

function sentences(text: string) {
  const out: { q: string; start: number; end: number }[] = [];
  const re = /[^.]+\.?/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    const q = m[0].trim();
    if (q.length > 24) out.push({ q, start: m.index, end: m.index + m[0].length });
  }
  return out;
}

export function LedgerSection() {
  const text = useMemo(() => canon(byId("bnss-144")!), []);
  const ledger = useMemo(() => sentences(text).slice(0, 4), [text]);

  return (
    <SectionShell
      id="ledger"
      no="06"
      kicker="Assembly & the ledger"
      title={
        <>
          Six stages.
          <span className="block italic text-gold-light">One traceable offset.</span>
        </>
      }
      lede={
        <>
          Retrieval is only half the instrument. The other half is the ledger: the record of which unit answered, at
          which offset, under which anchor. An answer that cannot name its provision does not leave the pipeline.
        </>
      }
      aside={
        <div className="flex flex-wrap gap-2">
          <Tag tone="gold">offset-level</Tag>
          <Tag tone="neutral">no orphan quotes</Tag>
        </div>
      }
    >
      <div className="grid gap-px bg-hair lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        {/* pipeline */}
        <ol className="bg-cream">
          {PIPELINE.map((p) => (
            <li
              key={p.n}
              className="group relative flex gap-4 border-b border-hair/70 px-4 py-4 transition-colors duration-300 last:border-b-0 hover:bg-panel/60"
            >
              <span className="relative">
                <span className="block font-display text-[26px] leading-none text-slate-custom transition-colors duration-300 group-hover:text-gold">
                  {p.n}
                </span>
              </span>
              <span className="min-w-0">
                <span className="flex flex-wrap items-baseline gap-3">
                  <span className="text-[15px] text-paper">{p.title}</span>
                  <span className="ml-auto font-mono text-[10.5px] text-gold/80">{p.meta}</span>
                </span>
                <span className="mt-1.5 block max-w-[52ch] text-[12.5px] leading-[1.65] text-silver/85">{p.body}</span>
              </span>
            </li>
          ))}
        </ol>

        {/* ledger */}
        <div className="bg-cream">
          <Panel className="border-0 bg-transparent">
            <div className="flex items-center justify-between border-b border-hair bg-panel-2 px-4 py-2.5">
              <span className="flex items-center gap-2 label-xs text-silver">
                <BookMarked className="h-3.5 w-3.5 text-gold" strokeWidth={1.5} />
                ledger · BNSS s. 144
              </span>
              <span className="font-mono text-[10.5px] text-muted">
                u-{digest(text)} · {text.length} ch
              </span>
            </div>
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-hair label-xs text-muted">
                  <th className="px-4 py-2 font-normal">sentence returned</th>
                  <th className="w-[104px] px-2 py-2 font-normal">offset</th>
                  <th className="w-[92px] px-2 py-2 text-right font-normal">state</th>
                </tr>
              </thead>
              <tbody>
                {ledger.map((l) => (
                  <tr key={l.start} className="group border-b border-hair/60 align-top transition-colors hover:bg-panel/60">
                    <td className="px-4 py-3">
                      <p className="font-mono text-[11.5px] leading-[1.7] text-silver/90">
                        <span className="text-gold/70">“</span>
                        {l.q.length > 150 ? `${l.q.slice(0, 150)}…` : l.q}
                        <span className="text-gold/70">”</span>
                      </p>
                      <p className="mt-1 text-[11px] text-muted">
                        anchor: {/^Provided/i.test(l.q) ? "proviso" : /^\s*Explanation/i.test(l.q) ? "explanation" : l.q.includes("(a)") || l.q.includes("(b)") ? "clauses (a)–(c)" : "operative sub-section"}
                      </p>
                    </td>
                    <td className="px-2 py-3 font-mono text-[11px] text-muted">
                      {l.start}–{l.end}
                    </td>
                    <td className="px-2 py-3 text-right">
                      <span className="inline-flex items-center gap-1.5 font-mono text-[10.5px] text-success">
                        <span className="h-1 w-1 bg-success" />
                        traced
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="grid grid-cols-2 gap-px border-t border-hair bg-hair sm:grid-cols-4">
              {[
                ["units in index", String(TOTAL_ACTS)],
                ["untraceable sentences", "0"],
                ["citations per answer", "≤ 12"],
                ["format", "statute · § · cl."],
              ].map(([k, v]) => (
                <div key={k} className="bg-panel px-3 py-2.5">
                  <p className="label-xs text-muted">{k}</p>
                  <p className="mt-1 font-mono text-[11.5px] text-paper/90">{v}</p>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </SectionShell>
  );
}

/* =================================================================== *
 * 06b — for whom
 * =================================================================== */

const FOR = [
  {
    icon: Gavel,
    who: "The bench & the registry",
    what: "Two provisions opened side by side, the old text and the new, with the relation named. Nothing has to be taken on the word of a summary.",
    query: "compare CrPC 482 ⇄ BNSS 528",
  },
  {
    icon: ScrollText,
    who: "Litigation desks",
    what: "Charge frames, bail applications and discharge petitions drafted against the provision actually in force on the date of the offence.",
    query: "batch · 44 queries · one matter index",
  },
  {
    icon: Landmark,
    who: "Chambers & solo practice",
    what: "A citation checked in seconds rather than in a copy of a digest that was last printed before the amendment.",
    query: "is 498A IPC carried into the BNS?",
  },
  {
    icon: BookMarked,
    who: "In-house & regulatory",
    what: "Statutory obligations traced to the section that imposes them — environment, consumer, data, labour — with the commencement date attached.",
    query: "CPA 2019 s. 2(9) · deficiency in service",
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
            Hector does not draft your pleading and does not decide your case. It answers the question a bench asks
            fifteen seconds after you cite a section — where is that written, and is it still in force.
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
    </WideSection>
  );
}

/* =================================================================== *
 * 08 — access
 * =================================================================== */

const FEATURES: [string, ...string[]][] = [
  ["Bare-act index", `${TOTAL_ACTS} statutes`, `${TOTAL_ACTS} statutes`, `${TOTAL_ACTS} + private overlay`],
  ["Regex boundary units", "whole sections", "whole sections", "whole sections"],
  ["Section comparison", "2-pane, mapped pairs", "2-pane + free pairing", "custom pairs per matter"],
  ["Queries per batch run", "10", "50", "queued, uncapped"],
  ["Citation strings", "copy-ready", "copy-ready", "copy-ready + annexure"],
  ["Exports", "—", "CSV · annexure", "CSV · annexure · JSON"],
  ["Offset ledger", "per sentence", "per sentence", "per sentence"],
  ["Seats", "1", "up to 10", "named counsel"],
  ["Case-report corpus", "—", "read-only add-on", "second index"],
  ["Deployment", "hosted", "hosted", "VPC / on-premise"],
];

export function AccessSection() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState<string | null>(null);
  const valid = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.trim());

  return (
    <WideSection id="access">
      <WideHead
        no="08"
        kicker="Access"
        title={
          <>
            Priced per desk.
            <span className="block italic text-gold-light">Not per word.</span>
          </>
        }
        lede={
          <>
            The index is maintained against the Gazette, the Legislative Department’s amendments and the correction
            orders. One subscription, no meter on the statute book.
          </>
        }
        controls={
          <div className="flex flex-wrap items-center gap-2 lg:justify-end">
            <Tag tone="neutral">no token counting</Tag>
            <Tag tone="neutral">cancel at any quarter</Tag>
            <Tag tone="gold">request reviewed by hand</Tag>
          </div>
        }
      />

      <div className="mt-10 overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-left">
          <thead>
            <tr>
              <th className="w-[240px] border-b border-hair px-4 py-5 align-bottom">
                <span className="label-xs text-muted">plan</span>
              </th>
              {ACCESS.map((t) => (
                <th
                  key={t.tier}
                  className={cn(
                    "relative border-b px-5 py-5 align-bottom transition-colors duration-300",
                    t.featured ? "border-gold/70 bg-gold/[0.05]" : "border-hair bg-cream",
                  )}
                >
                  {t.featured && <span className="absolute inset-x-0 top-0 h-[2px] bg-gold" />}
                  <p className="label-xs text-gold">{t.tier}</p>
                  <p className="mt-3 font-display text-[clamp(1.7rem,3.2vw,2.5rem)] leading-none tracking-tight text-paper">
                    {t.price}
                  </p>
                  <p className="mt-2 font-mono text-[11px] text-muted">{t.per}</p>
                  <ul className="mt-4 hidden space-y-1.5 lg:block">
                    {t.lines.map((l) => (
                      <li key={l} className="flex items-start gap-2 text-[12px] leading-snug text-silver">
                        <Check className="mt-[3px] h-3 w-3 shrink-0 text-gold/80" strokeWidth={2} />
                        {l}
                      </li>
                    ))}
                  </ul>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {FEATURES.map(([label, ...cells]) => (
              <tr key={label} className="group border-b border-hair/60 transition-colors hover:bg-panel/40">
                <th scope="row" className="px-4 py-2.5 text-left text-[12.5px] font-normal text-silver">
                  {label}
                </th>
                {cells.map((c, i) => (
                  <td
                    key={i}
                    className={cn(
                      "px-5 py-2.5 font-mono text-[11.5px]",
                      c === "—" ? "text-slate-custom" : "text-paper/90",
                      ACCESS[i]?.featured && "bg-gold/[0.03]",
                    )}
                  >
                    {c}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* request band */}
      <Reveal y={false}>
        <div className="mt-6 grid gap-px border border-hair bg-hair lg:grid-cols-[minmax(0,1fr)_420px]">
          <div className="bg-panel px-5 py-6">
            <p className="label-xs text-gold">Index keys</p>
            <p className="mt-3 max-w-[44ch] font-display text-[clamp(1.4rem,2.6vw,2rem)] leading-[1.1] text-paper">
              Keys are issued to members of the Bar, to the Bench, and to registries — by name, and after a look at
              the roll.
            </p>
            <p className="mt-3 max-w-[58ch] text-[12.5px] leading-[1.7] text-muted">
              Send the enrolment number or the department. A person reads every request; the corpus is not sold to
              anyone who intends to let it speak for itself.
            </p>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (valid) setSent(email.trim());
            }}
            className="flex flex-col justify-center gap-3 bg-cream px-5 py-6"
          >
            <label className="flex items-center gap-3 border border-hair bg-panel px-3 py-2.5 transition-colors focus-within:border-gold/60">
              <Mail className="h-3.5 w-3.5 text-muted" strokeWidth={1.7} />
              <input
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setSent(null);
                }}
                placeholder="counsel@chambers.in"
                className="min-w-0 flex-1 bg-transparent font-mono text-[12.5px] text-paper outline-none placeholder:text-muted/70"
              />
            </label>
            {!valid && email.trim().length > 3 && (
              <p className="font-mono text-[10.5px] text-error/80">that address does not parse</p>
            )}
            <Btn type="submit" disabled={!valid} className="w-full">
              Request a key
            </Btn>
            <p className="min-h-[16px] font-mono text-[10.5px] text-muted">
              {sent ? (
                <span className="text-success">logged · {sent} · you will hear from a person</span>
              ) : (
                "no card, no trial meter · reply within two working days"
              )}
            </p>
          </form>
        </div>
      </Reveal>
    </WideSection>
  );
}

/* =================================================================== *
 * 09 — questions
 * =================================================================== */

export function FaqSection() {
  const [open, setOpen] = useState(0);
  return (
    <SectionShell
      id="faq"
      no="09"
      kicker="Questions of construction"
      title={
        <>
          Read it
          <span className="block italic text-gold-light">as a set of clauses.</span>
        </>
      }
      lede={
        <>
          The objections we hear most often, answered without a marketing register. Where the answer is “it depends on
          the text”, we say so and point at the text.
        </>
      }
    >
      <ol className="border-t border-hair">
        {FAQ.map((f, i) => {
          const on = open === i;
          return (
            <li key={f.q} className="border-b border-hair">
              <button
                onClick={() => setOpen(on ? -1 : i)}
                className="group flex w-full items-start gap-4 py-4 text-left transition-colors duration-200 hover:bg-panel/40"
              >
                <span className={cn("mt-1 font-mono text-[10.5px]", on ? "text-gold" : "text-muted")}>
                  {`(${String.fromCharCode(97 + i)})`}
                </span>
                <span
                  className={cn(
                    "flex-1 font-display text-[clamp(1.1rem,2.1vw,1.5rem)] leading-snug tracking-tight transition-colors duration-200",
                    on ? "text-gold-light" : "text-paper group-hover:text-paper",
                  )}
                >
                  {f.q}
                </span>
                <span className={cn("mt-1 transition-transform duration-300", on ? "rotate-180 text-gold" : "text-muted")}>
                  <ChevronDown className="h-4 w-4" strokeWidth={1.6} />
                </span>
              </button>
              <div
                className="grid transition-[grid-template-rows] duration-500 ease-out"
                style={{ gridTemplateRows: on ? "1fr" : "0fr" }}
              >
                <div className="overflow-hidden">
                  <p className="max-w-[74ch] pb-5 pl-[46px] pr-8 text-[13.5px] leading-[1.75] text-silver">
                    {f.a}
                  </p>
                </div>
              </div>
            </li>
          );
        })}
      </ol>
      <p className="mt-6 flex items-center gap-2 font-mono text-[11px] text-muted">
        <Minus className="h-3 w-3" strokeWidth={1.8} />
        clause (g) reserved for questions received at the register
      </p>
    </SectionShell>
  );
}
