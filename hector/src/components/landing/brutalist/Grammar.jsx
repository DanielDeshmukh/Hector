"use client";

import { useMemo, useState } from "react";
import { Regex, Braces, ScanLine, FileCode2 } from "lucide-react";
import { cn } from "@/lib/landing/cn";
import { Panel, SectionShell, Tag, CodeBlock } from "./ui";
import { SECTION_HEAD, ANCHOR_KINDS, CUT_RULES, NOISE, CLAIMS } from "@/lib/landing/scannerSource";
import { FIXTURES } from "@/lib/landing/fixtures";
import { frefStrip } from "@/lib/landing/boundary";

const GROUPS = [
  { id: "head", title: "A section head", note: "opens a unit", items: SECTION_HEAD },
  { id: "anchor", title: "Anchors that travel with the rule", note: "never cut across", items: ANCHOR_KINDS },
  { id: "cut", title: "Where a cut is legal", note: "step 4 only", items: Object.values(CUT_RULES) },
  { id: "noise", title: "Removed, not cut at", note: "step 3 / step 6", items: NOISE },
];

const PATTERN_COUNT = GROUPS.reduce((n, g) => n + g.items.length, 0);

/** Classify one printed line using the same predicates the scanner uses. */
function kindOf(line) {
  const t = frefStrip(line).replace(/^\s+/, "");
  if (NUMHEAD.test(t)) return "section";
  if (PROV.test(t)) {
    if (/^Exception/i.test(t)) return "exception";
    if (/^Explanation/i.test(t)) return "explanation";
    if (/^Illustration/i.test(t)) return "illustration";
    return "proviso";
  }
  if (SUBL.test(t) || /—\s*\(|–\s*\(|-\s*\(/.test(t)) return "clause";
  if (PAGE.test(t) || SEP.test(t)) return "noise";
  return "body";
}

const NUMHEAD = SECTION_HEAD[1].js; // QUOTE_NUM_RE — also matches "101. Murder"
const PROV = ANCHOR_KINDS[0].js;
const SUBL = CUT_RULES.sub.js;
const PAGE = NOISE[2].js;
const SEP = NOISE[3].js;

const KIND_TO_GROUP = {
  section: "head",
  proviso: "anchor",
  exception: "anchor",
  explanation: "anchor",
  illustration: "anchor",
  clause: "cut",
  noise: "noise",
  body: null,
};

export function GrammarSection() {
  const [active, setActive] = useState(null); // { group, name }
  const [sampleId, setSampleId] = useState("ipc-124a");

  const fixture = FIXTURES.find((f) => f.id === sampleId) || FIXTURES[0];
  const lines = useMemo(() => fixture.text.split("\n").filter(Boolean), [fixture]);

  const lit = useMemo(() => {
    if (!active) return new Set();
    const set = new Set();
    lines.forEach((l, i) => {
      const k = kindOf(l);
      if (KIND_TO_GROUP[k] === active.group) set.add(i);
    });
    return set;
  }, [active, lines]);

  const counts = useMemo(() => {
    const c = { section: 0, proviso: 0, exception: 0, explanation: 0, illustration: 0, clause: 0, noise: 0, body: 0 };
    lines.forEach((l) => {
      c[kindOf(l)] += 1;
    });
    return c;
  }, [lines]);

  return (
    <SectionShell
      id="grammar"
      no="02"
      kicker="The boundary grammar"
      title={
        <>
          The patterns.
          <span className="block italic text-gold-light">Printed, with their file and line.</span>
        </>
      }
      lede={
        <>
          This panel displays a browser-side copy of regular expressions from the repository's v2 ingestion
          workflow, with source file and line references. That workflow is separate from the current API PDF
          ingestion path, which uses the section-aware chunker in the backend.
        </>
      }
      aside={
        <div className="flex flex-wrap gap-2">
          <Tag tone="gold">{PATTERN_COUNT} patterns</Tag>
          <Tag tone="neutral">python · verbatim</Tag>
          <Tag tone="neutral">deterministic · idempotent</Tag>
        </div>
      }
    >
      <Panel className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hair bg-panel-2 px-4 py-2.5">
          <span className="flex items-center gap-2 label-xs text-silver">
            <Regex className="h-3.5 w-3.5 text-gold" strokeWidth={1.5} />
            v2_scanner.py · step4_segment.py · step6_validate.py
          </span>
          <span className="label-xs text-muted">select a pattern to light it up on the right</span>
        </div>

        <div className="grid lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          {/* the source, grouped by role */}
          <div className="divide-y divide-hair border-b border-hair lg:border-b-0 lg:border-r">
            {GROUPS.map((g) => (
              <div key={g.id}>
                <div className="flex items-center gap-2 bg-panel/60 px-4 py-1.5">
                  <span className="label-xs text-gold">{g.title}</span>
                  <span className="h-px flex-1 bg-hair" />
                  <span className="font-mono text-[10px] text-muted">{g.note}</span>
                </div>
                <ul>
                  {g.items.map((it) => {
                    const on = active?.name === it.name;
                    return (
                      <li
                        key={`${g.id}-${it.name}`}
                        onMouseEnter={() => setActive({ group: g.id, name: it.name })}
                        onFocus={() => setActive({ group: g.id, name: it.name })}
                        onClick={() => setActive({ group: g.id, name: it.name })}
                        tabIndex={0}
                        className={cn(
                          "cursor-default px-4 py-2.5 transition-colors duration-200",
                          on ? "bg-gold/[0.07]" : "hover:bg-panel-2/70",
                        )}
                      >
                        <div className="flex items-center gap-2">
                          <span className={cn("h-1.5 w-1.5 transition-colors", on ? "bg-gold" : "bg-slate-custom")} />
                          <span className={cn("font-mono text-[12px]", on ? "text-gold-light" : "text-paper/85")}>
                            {it.name}
                          </span>
                          <span className="ml-auto font-mono text-[10px] text-muted">
                            {it.file.split("/").pop()}:L{it.line}
                          </span>
                        </div>
                        <p className="mt-1 pl-3.5 text-[12px] leading-[1.6] text-muted">{it.role}</p>
                        <pre className="mt-1.5 ml-3.5 overflow-x-auto border-l border-hair/70 pl-2 font-mono text-[10.5px] leading-[1.6] text-silver/75">
                          <code>{it.python}</code>
                        </pre>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>

          {/* the real extract, classified by those patterns */}
          <div className="relative">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-hair bg-panel-2 px-4 py-2.5">
              <div className="flex flex-wrap gap-1">
                {FIXTURES.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setSampleId(f.id)}
                    className={cn(
                      "border px-2 py-1 font-mono text-[10.5px] transition-colors duration-200",
                      sampleId === f.id
                        ? "border-gold/70 bg-gold/10 text-gold-light"
                        : "border-hair text-muted hover:border-slate-custom hover:text-silver",
                    )}
                    title={`${f.chars.toLocaleString("en-IN")} characters, extracted from the ingest output`}
                  >
                    {f.code} §{f.section}
                  </button>
                ))}
              </div>
              <span className="flex items-center gap-1.5 label-xs text-gold">
                <ScanLine className="h-3 w-3" strokeWidth={1.6} />
                {active?.name ?? "all lines"}
              </span>
            </div>

            <div className="max-h-[460px] overflow-y-auto px-4 py-4">
              {lines.map((l, i) => {
                const k = kindOf(l);
                const on = lit.has(i);
                const dim = active && !on;
                return (
                  <p
                    key={i}
                    className={cn(
                      "whitespace-pre-wrap border-l-2 py-[1px] pl-2 font-mono text-[11.5px] leading-[1.75] transition-all duration-300",
                      on ? "border-gold bg-gold/[0.09] text-gold-light" : "border-transparent",
                      dim ? "text-muted/40" : "text-silver/80",
                    )}
                  >
                    {l}
                  </p>
                );
              })}
            </div>

            <div className="grid grid-cols-4 gap-px border-t border-hair bg-hair">
              {[
                ["proviso", counts.proviso],
                ["exception", counts.exception],
                ["explanation", counts.explanation],
                ["illustration", counts.illustration],
              ].map(([k, v]) => (
                <div key={k} className="bg-panel px-3 py-2.5">
                  <p className="label-xs text-muted">{k}</p>
                  <p className="mt-1 font-mono text-[13px] text-paper">{v}</p>
                </div>
              ))}
            </div>
            <div className="border-t border-hair bg-panel-2 px-4 py-2 font-mono text-[10.5px] text-muted">
              {fixture.code} §{fixture.section} &mdash; {fixture.title} &middot;{" "}
              {fixture.chars.toLocaleString("en-IN")} characters &middot;{" "}
              {counts.clause} clause lines &middot; {counts.noise} removed
            </div>
          </div>
        </div>
      </Panel>

      <div className="mt-4 grid gap-px bg-hair sm:grid-cols-3">
        {[
          {
            t: "What it will not do",
            b: "It never breaks on a blank line, a heading, a page number or a token count. Those are formatting, not law.",
          },
          {
            t: "What it must do",
            b: "It must keep 124A distinct from 124, and 304B distinct from 304 — the letter suffix is part of the identity of the provision.",
          },
          {
            t: "What it yields",
            b: "One unit per section, addressable by act and section number, and stampable with the character offset every sentence was taken from.",
          },
        ].map((c) => (
          <div key={c.t} className="bg-cream px-4 py-4 transition-colors duration-300 hover:bg-panel/70">
            <p className="flex items-center gap-2 label-xs text-gold">
              <Braces className="h-3 w-3" strokeWidth={1.6} />
              {c.t}
            </p>
            <p className="mt-2 text-[12.5px] leading-[1.65] text-silver">{c.b}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {CLAIMS.map((c) => (
          <CodeBlock key={`${c.file}-${c.line}`} file={c.file} line={c.line} python={c.text} compact />
        ))}
      </div>
      <p className="mt-3 flex items-center gap-2 font-mono text-[10.5px] text-muted">
        <FileCode2 className="h-3 w-3" strokeWidth={1.6} />
        {CLAIMS.length} further statements, lifted from the docstrings that ship with the pipeline. They are
        printed because the rules above are only as good as the constraints written beside them.
      </p>
    </SectionShell>
  );
}
