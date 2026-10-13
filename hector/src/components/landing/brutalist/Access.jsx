"use client";

import Link from "next/link";
import { ArrowRight, KeyRound, Terminal, BookOpen } from "lucide-react";
import { Btn, Reveal, Tag, WideHead, WideSection, LiveCount } from "./ui";

/**
 * Access. There are no pricing tiers on this page and no plan table — the
 * product is used through the application and the API, and both are linked
 * from here rather than described in a column of features that would have to
 * be invented to fill a grid.
 */
export function AccessSection({ records, recordsLoading, recordsFailed }) {
  return (
    <WideSection id="access">
      <WideHead
        no="08"
        kicker="Access"
        title={
          <>
            Open the index.
            <span className="block italic text-gold-light">There is nothing between you and it.</span>
          </>
        }
        lede={
          <>
            This page describes how the corpus is built and lets you watch the segmentation rules run. The
            product itself is a separate application: you ask it questions, it answers with provisions and
            citations. Everything above is the same index that answers there.
          </>
        }
        controls={
          <div className="flex flex-wrap items-center gap-2 lg:justify-end">
            <Tag tone="gold">same index</Tag>
            <Tag tone="neutral">no meter on the statute book</Tag>
          </div>
        }
      />

      <div className="mt-10 grid gap-px bg-hair lg:grid-cols-3">
        {[
          {
            icon: Terminal,
            title: "Ask a question",
            body: "The application. Type a question in plain language or name a section directly; the answer arrives with the provision and the citation it was drawn from.",
            cta: "Open the app",
            href: "/",
          },
          {
            icon: KeyRound,
            title: "API access",
            body: "The same endpoints this page calls — search, compare, status — for integration into a matter management system or a research workflow.",
            cta: "Read the API notes",
            href: "/landing/api-access",
          },
          {
            icon: BookOpen,
            title: "Bare act index",
            body: "The maintained list of statutes and the provisions held under each, kept alongside the ingest registry rather than derived from a figure on this page.",
            cta: "Browse the index",
            href: "/landing/acts",
          },
        ].map((c, i) => (
          <Reveal key={c.title} delay={i * 70} className="bg-cream">
            <div className="group flex h-full flex-col px-5 py-6 transition-colors duration-300 hover:bg-panel/60">
              <div className="flex items-center gap-3">
                <span className="grid h-8 w-8 place-items-center border border-slate-custom text-gold transition-colors duration-300 group-hover:border-gold/70">
                  <c.icon className="h-4 w-4" strokeWidth={1.4} />
                </span>
                <h3 className="font-display text-[22px] leading-none tracking-tight text-paper">{c.title}</h3>
              </div>
              <p className="mt-3 flex-1 max-w-[46ch] text-[13.5px] leading-[1.7] text-silver">{c.body}</p>
              <Link href={c.href} className="mt-5">
                <Btn variant="ghost" className="w-full">
                  {c.cta}
                  <ArrowRight className="h-3 w-3 transition-transform duration-200 group-hover:translate-x-0.5" />
                </Btn>
              </Link>
            </div>
          </Reveal>
        ))}
      </div>

      <Reveal y={false}>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-4 border border-hair bg-panel px-5 py-4">
          <p className="max-w-[64ch] text-[12.5px] leading-[1.7] text-silver">
            The figure the index publishes about itself, read when this page loaded:
          </p>
          <LiveCount records={records} loading={recordsLoading} failed={recordsFailed} />
        </div>
      </Reveal>
    </WideSection>
  );
}
