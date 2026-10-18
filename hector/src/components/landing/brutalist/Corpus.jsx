"use client";

import Link from "next/link";
import { ArrowRight, FileSearch, Trash2, ShieldCheck } from "lucide-react";
import { Reveal, Tag, WideHead, WideSection, Panel } from "./ui";
import { INGEST_STEPS, VALIDATION_GATES } from "@/lib/landing/samples";
import { LiveCount } from "./ui";

const EXCLUSIONS = [
  {
    label: "commentary, headnotes",
    why: "The sources are bare acts, not digests. An editor's paraphrase is not in the text to begin with; nothing has to be filtered out.",
  },
  {
    label: "schedule table rows",
    why: "A schedule heading is recognised so its numbered table rows are never mistaken for sections. Schedules are not cut into section units.",
  },
  {
    label: "amendment footnotes as sections",
    why: "Footnote lines that cite an amendment are rejected as section heads and accounted for by gate G9; the in-text amendment markers stay with their section.",
  },
];

/**
 * Index architecture. No act list, no coverage table, no count of statutes —
 * only the steps that run, the gates that must pass, and the one figure the
 * index publishes about itself.
 */
export function CorpusSection({ records, recordsLoading, recordsFailed }) {
  return (
    <WideSection id="corpus">
      <WideHead
        no="01"
        kicker="How the corpus is made"
        title={
          <>
            Not sliced.
            <span className="block italic text-gold-light">Disassembled, then checked.</span>
          </>
        }
        lede={
          <>
            The seven-step display below documents the repository's v2 ingestion workflow; it is not a live trace
            of the current API ingestion path. The API uses EnhancedHectorIngestor and SectionAwareChunker, which
            identify section boundaries, split long sections, and can merge very short sections.
          </>
        }
        controls={
          <div className="flex flex-wrap items-center gap-2 lg:justify-end">
            <Tag tone="gold">7 ingest steps</Tag>
            <Tag tone="active">9 gates, all mandatory</Tag>
          </div>
        }
      />

      {/* the pipeline, as it actually runs */}
      <div className="mt-10 grid gap-px bg-hair md:grid-cols-2 xl:grid-cols-4">
        {INGEST_STEPS.map((s, i) => (
          <Reveal key={s.n} delay={i * 55} className="bg-cream">
            <div className="group h-full px-4 py-5 transition-colors duration-300 hover:bg-panel/60">
              <div className="flex items-baseline gap-2">
                <span className="font-display text-[28px] leading-none text-gold/70 transition-colors duration-300 group-hover:text-gold">
                  {s.n}
                </span>
                <span className="text-[15px] text-paper">{s.name}</span>
              </div>
              <p className="mt-1 font-mono text-[10px] text-muted">{s.file}</p>
              <p className="mt-3 text-[12.5px] leading-[1.65] text-silver">{s.detail}</p>
              <p className="mt-3 border-t border-hair/60 pt-2 font-mono text-[10px] text-muted">
                writes &rarr; {s.writes}
              </p>
            </div>
          </Reveal>
        ))}

        <Reveal delay={INGEST_STEPS.length * 55} className="bg-cream">
          <div className="flex h-full flex-col px-4 py-5">
            <p className="flex items-center gap-2 label-xs text-gold">
              <ShieldCheck className="h-3.5 w-3.5" strokeWidth={1.6} />
              what step six checks
            </p>
            <ul className="mt-3 space-y-1">
              {VALIDATION_GATES.map((g, i) => (
                <li key={g} className="flex items-baseline gap-2 font-mono text-[11px] text-silver">
                  <span className="text-success/80">{String(i + 1).padStart(2, "0")}</span>
                  {g}
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>

      {/* what is deliberately not in the index */}
      <div className="mt-4 grid gap-px bg-hair lg:grid-cols-2">
        <div className="bg-cream px-5 py-5">
          <p className="flex items-center gap-2 label-xs text-gold">
            <Trash2 className="h-3.5 w-3.5" strokeWidth={1.6} />
            what is not in the index, and why
          </p>
          <ul className="mt-4 space-y-3">
            {EXCLUSIONS.map((e) => (
              <li key={e.label} className="border-b border-hair/60 pb-3 last:border-b-0">
                <p className="font-mono text-[12px] text-paper">{e.label}</p>
                <p className="mt-1 max-w-[62ch] text-[12.5px] leading-[1.65] text-silver">{e.why}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-cream px-5 py-5">
          <p className="flex items-center gap-2 label-xs text-gold">
            <FileSearch className="h-3.5 w-3.5" strokeWidth={1.6} />
            the index reports its own size
          </p>
          <p className="mt-4 font-display text-[clamp(2.4rem,6vw,4rem)] leading-none text-paper">
            {recordsLoading ? (
              <span className="text-muted">…</span>
            ) : recordsFailed || records === null ? (
              <span className="text-muted">—</span>
            ) : (
              <span className="tabular-nums">{records.toLocaleString("en-IN")}</span>
            )}
          </p>
          <p className="mt-2 label-xs text-silver">records, read live</p>
          <p className="mt-4 max-w-[54ch] text-[12.5px] leading-[1.7] text-silver">
            The figure above is a single unauthenticated request to the service&rsquo;s readiness probe, issued
            when this page loaded. It is not typed into the source and it is not cached in the markup. If the
            index is unreachable the line is blank rather than stale.
          </p>
          <p className="mt-4 max-w-[54ch] text-[12.5px] leading-[1.7] text-silver">
            The{" "}
            <Link href="/landing/acts" className="text-gold-light underline underline-offset-4 hover:text-gold">
              bare act index
            </Link>{" "}
            page is a catalogue of the statutes the project is oriented around, not a live coverage report of
            the index. The record count above is what the index actually holds.
          </p>
          <div className="mt-5">
            <LiveCount records={records} loading={recordsLoading} failed={recordsFailed} />
          </div>
          <a href="#grammar" className="group mt-5 inline-flex items-center gap-1.5 label-xs text-gold hover:text-gold-light">
            see what divides it
            <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
          </a>
        </div>
      </div>
    </WideSection>
  );
}
