"use client";

import Link from "next/link";
import { ArrowRight, FileSearch, Trash2, ShieldCheck } from "lucide-react";
import { Reveal, Tag, WideHead, WideSection, Panel } from "./ui";
import { INGEST_STEPS, VALIDATION_GATES } from "@/lib/landing/samples";
import { LiveCount } from "./ui";

const EXCLUSIONS = [
  {
    label: "commentary",
    why: "A digest sentence is an editor's opinion of an enactment. It must not be able to answer as though it were the enactment.",
  },
  {
    label: "headnotes",
    why: "A headnote is written after the fact, from the judgment, not from the statute. It would retrieve as though the legislature had drafted it.",
  },
  {
    label: "schedules of forms, abridged",
    why: "Where a schedule is forms or tables, it is indexed whole or not at all. A half-schedule is not a source.",
  },
  {
    label: "amendment notes, as body text",
    why: "Amendment markers are preserved inside the unit, but the marginal note that records them is not treated as operative text.",
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
            A bare act is a printed object: a long title, chapters, sections, sub-sections, provisos, exceptions,
            explanations, illustrations, schedules. The index preserves that object and then verifies that nothing
            was lost between the PDF and the record. Seven steps, and the seventh only runs if the sixth passes.
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
            what is kept out, on purpose
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
            For the list of statutes and the provisions held under each, the{" "}
            <Link href="/landing/acts" className="text-gold-light underline underline-offset-4 hover:text-gold">
              bare act index
            </Link>{" "}
            is the reference. It is maintained alongside the ingest registry, not derived from a number on this
            page.
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
