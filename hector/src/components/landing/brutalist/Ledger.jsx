"use client";

import { useMemo } from "react";
import { BookOpen, Layers } from "lucide-react";
import { Panel, SectionShell, Tag } from "./ui";
import { FIXTURES } from "@/lib/landing/fixtures";
import { scanUnits, planParts } from "@/lib/landing/boundary";
import { QUERY_STAGES } from "@/lib/landing/samples";

/** Split a unit into sentences and report the character span of each. */
function sentences(text) {
  const out = [];
  const re = /[^.]+\.?/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const q = m[0].trim();
    if (q.length > 28) out.push({ q, start: m.index, end: m.index + m[0].length });
  }
  return out;
}

function anchorOf(s) {
  if (/^Provided/i.test(s)) return "proviso";
  if (/^\s*Explanation/i.test(s)) return "explanation";
  if (/^\s*Exception/i.test(s)) return "exception";
  if (/^\s*Illustration/i.test(s)) return "illustration";
  if (/\(\s*[a-z]\s*\)/.test(s.slice(0, 40))) return "clause";
  return "operative text";
}

export function LedgerSection() {
  const fixture = FIXTURES.find((f) => f.id === "bnss-144") || FIXTURES[0];
  const scan = useMemo(() => scanUnits(fixture.text), [fixture]);
  const unit = scan.units[0];
  const plan = useMemo(() => (unit ? planParts(unit.lines) : null), [unit]);
  const ledger = useMemo(() => sentences(fixture.text).slice(0, 5), [fixture]);

  return (
    <SectionShell
      id="ledger"
      no="06"
      kicker="Example ledger"
      title={
        <>
          A sample provision.
          <span className="block italic text-gold-light">A local trace.</span>
        </>
      }
      lede={
        <>
          The right-hand table computes sentence offsets and labels from bundled sample text in this browser.
          It is an illustration, not a live API response or a record read from the deployed index.
        </>
      }
      aside={
        <div className="flex flex-wrap gap-2">
          <Tag tone="gold">browser-computed</Tag>
          <Tag tone="neutral">bundled fixture</Tag>
        </div>
      }
    >
      <div className="grid gap-px bg-hair lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        {/* Search service flow for uncached legal-research requests. */}
        <ol className="bg-cream">
          {QUERY_STAGES.map((p, i) => (
            <li
              key={p.id}
              className="group relative flex gap-4 border-b border-hair/70 px-4 py-4 transition-colors duration-300 last:border-b-0 hover:bg-panel/60"
            >
              <span className="relative">
                <span className="block font-display text-[26px] leading-none text-slate-custom transition-colors duration-300 group-hover:text-gold">
                  {String(i + 1).padStart(2, "0")}
                </span>
              </span>
              <span className="min-w-0">
                <span className="flex flex-wrap items-baseline gap-3">
                  <span className="text-[15px] text-paper">{p.name}</span>
                  <span className="ml-auto font-mono text-[10.5px] text-gold/80">{p.id}</span>
                </span>
                <span className="mt-1.5 block max-w-[52ch] text-[12.5px] leading-[1.65] text-silver/85">
                  {p.detail}
                </span>
              </span>
            </li>
          ))}
          <li className="border-t border-hair bg-panel/40 px-4 py-4">
            <p className="text-[12.5px] leading-[1.7] text-muted">
              The search service returns route, retrieval and generation timings, plus a confidence value and
              hallucination summary. Cached responses may follow a shorter path.
            </p>
          </li>
        </ol>

        {/* A local ledger computed from bundled fixture text. */}
        <div className="bg-cream">
          <Panel className="border-0 bg-transparent">
            <div className="flex items-center justify-between border-b border-hair bg-panel-2 px-4 py-2.5">
              <span className="flex items-center gap-2 label-xs text-silver">
                <BookOpen className="h-3.5 w-3.5 text-gold" strokeWidth={1.5} />
                example · {fixture.code} s. {fixture.section}
              </span>
              <span className="font-mono text-[10.5px] text-muted">
                {unit?.chars?.toLocaleString("en-IN")} ch · {unit?.lines?.length} lines
              </span>
            </div>
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-hair label-xs text-muted">
                  <th className="px-4 py-2 font-normal">sentence in sample text</th>
                  <th className="w-[104px] px-2 py-2 font-normal">offset</th>
                  <th className="w-[110px] px-2 py-2 text-right font-normal">anchor</th>
                </tr>
              </thead>
              <tbody>
                {ledger.map((l) => (
                  <tr key={l.start} className="border-b border-hair/60 align-top transition-colors hover:bg-panel/60">
                    <td className="px-4 py-3">
                      <p className="font-mono text-[11.5px] leading-[1.7] text-silver/90">
                        <span className="text-gold/70">&ldquo;</span>
                        {l.q.length > 140 ? `${l.q.slice(0, 140)}…` : l.q}
                        <span className="text-gold/70">&rdquo;</span>
                      </p>
                    </td>
                    <td className="px-2 py-3 font-mono text-[11px] text-muted">
                      {l.start}–{l.end}
                    </td>
                    <td className="px-2 py-3 text-right">
                      <span className="font-mono text-[10.5px] text-gold/85">{anchorOf(l.q)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="grid grid-cols-2 gap-px border-t border-hair bg-hair sm:grid-cols-4">
              {[
                ["unit", `${fixture.code} §${fixture.section}`],
                ["head recognised by", unit?.via ?? "—"],
                ["safe cuts found", plan ? String(Math.max(0, plan.parts - 1)) : "—"],
                ["longest part", plan?.longUnsplit ? "whole unit" : plan ? `${plan.parts} parts` : "—"],
              ].map(([k, v]) => (
                <div key={k} className="bg-panel px-3 py-2.5">
                  <p className="label-xs text-muted">{k}</p>
                  <p className="mt-1 font-mono text-[11.5px] text-paper/90">{v}</p>
                </div>
              ))}
            </div>
          </Panel>
          <p className="flex items-start gap-2 border-t border-hair bg-panel px-4 py-2.5 font-mono text-[10.5px] leading-relaxed text-muted">
            <Layers className="mt-0.5 h-3 w-3 shrink-0 text-gold/70" strokeWidth={1.6} />
            the offsets above were computed in this browser from bundled sample text. They do not describe the
            source positions or citations in a live search response.
          </p>
        </div>
      </div>
    </SectionShell>
  );
}
