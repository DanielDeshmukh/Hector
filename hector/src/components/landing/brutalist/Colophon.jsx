"use client";

import Link from "next/link";
import { ArrowDown } from "lucide-react";
import { Btn } from "./ui";

export function Colophon({ records, recordsLoading, recordsFailed }) {
  return (
    <footer className="relative border-t border-hair bg-ink">
      <div className="mx-auto max-w-[1400px] px-5 py-16 sm:px-8">
        <div className="grid gap-12 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <p className="label-xs text-gold">Ad finem</p>
            <p className="mt-5 font-display text-[clamp(1.9rem,3.6vw,3rem)] leading-[1.02] tracking-[-0.02em] text-paper">
              The statute says what it says.
              <span className="block text-silver/70 italic">Hector only refuses to cut it up.</span>
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a href="#chunking">
                <Btn>
                  See the cut rules
                  <ArrowDown className="h-3 w-3" />
                </Btn>
              </a>
              <Link href="/">
                <Btn variant="ghost">Open the app</Btn>
              </Link>
            </div>
            {!(recordsLoading || recordsFailed || records === null) && (
              <p className="mt-6 font-mono text-[11px] text-muted">
                index reading at page load:{" "}
                <span className="tabular-nums text-gold">{records.toLocaleString("en-IN")}</span> records
              </p>
            )}
          </div>

          <div className="grid gap-8 sm:grid-cols-3 lg:col-span-7">
            <FooterCol
              title="On this page"
              links={[
                ["Corpus architecture", "#corpus", true],
                ["The regex grammar", "#grammar", true],
                ["Chunking lab", "#chunking", true],
                ["Batch ledger", "#batch", true],
              ]}
            />
            <FooterCol
              title="Product"
              links={[
                ["Ask a question", "/", false],
                ["Compare a section", "/", false],
                ["Bare Act index", "/landing/acts", false],
                ["API access", "/landing/api-access", false],
              ]}
            />
            <FooterCol
              title="Reference"
              links={[
                ["Documentation", "/landing/documentation", false],
                ["IPC–BNS guide", "/landing/ipc-bns-guide", false],
                ["Changelog", "/landing/changelog", false],
                ["Disclaimer", "/landing/disclaimer", false],
              ]}
            />
          </div>
        </div>

        <div className="mt-14 grid gap-6 border-t border-hair pt-8 lg:grid-cols-12">
          <p className="text-[12px] leading-relaxed text-muted lg:col-span-7">
            Hector is a retrieval instrument for bare acts. Every provision it returns is printed with its
            act, section and clause, and must be read against the authoritative text published by the
            Legislative Department before it is relied on in any proceeding. Nothing on this page is legal
            advice, and nothing on this page is a substitute for the statute. Section text shown here is
            extracted verbatim from ingested PDFs and is displayed only where it is used to demonstrate the
            segmentation rules.
          </p>
          <div className="flex flex-col justify-between gap-4 lg:col-span-5 lg:items-end">
            <div className="flex items-center gap-3 font-mono text-[11px] text-muted">
              <span>Hector</span>
              <span className="h-3 w-px bg-hair" />
              <span>Hierarchical Evaluation of Civil-Criminal Textual&rsquo;s Orchestrator &amp; Retrieval</span>
            </div>
            <div className="flex flex-wrap items-center gap-4 label-xs text-muted">
              <span>&copy; {new Date().getFullYear()} Hector Legal Systems</span>
              <span className="hidden h-3 w-px bg-slate-custom/40 sm:block" />
              <Link href="#top" className="text-silver transition-colors hover:text-gold">
                Back to the top
              </Link>
              <span className="hidden h-3 w-px bg-slate-custom/40 sm:block" />
              <Link href="/landing/terms" className="transition-colors hover:text-gold">Terms</Link>
              <Link href="/landing/privacy" className="transition-colors hover:text-gold">Privacy</Link>
            </div>
          </div>
        </div>
      </div>
      <div className="overflow-hidden border-t border-hair py-3">
        <p
          aria-hidden
          className="whitespace-nowrap text-center font-display text-[13vw] leading-[0.8] tracking-[-0.04em] text-silver/[0.055] select-none"
        >
          BARE ACTS, RETRIEVED WHOLE
        </p>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }) {
  return (
    <div>
      <p className="label-xs text-gold">{title}</p>
      <ul className="mt-4 space-y-0">
        {links.map(([label, href, isAnchor]) => (
          <li key={label}>
            <a
              href={href}
              className="group flex items-baseline gap-2 border-b border-hair/50 py-2 text-[13px] text-silver transition-colors hover:text-gold-light"
            >
              <span className="h-px w-0 bg-gold transition-all duration-300 group-hover:w-3" />
              {label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
