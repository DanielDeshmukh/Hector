"use client";

import { Backdrop } from "./brutalist/Backdrop";
import { Masthead } from "./brutalist/Masthead";
import { Colophon } from "./brutalist/Colophon";
import { Hero } from "./brutalist/Hero";
import { CorpusSection } from "./brutalist/Corpus";
import { Doctrine } from "./brutalist/Doctrine";
import { GrammarSection } from "./brutalist/Grammar";
import { ChunkingSection } from "./brutalist/Chunking";
import { TesterSection } from "./brutalist/Tester";
import { ComparisonSection } from "./brutalist/Comparison";
import { BatchSection } from "./brutalist/Batch";
import { LedgerSection } from "./brutalist/Ledger";
import { ForWhomSection } from "./brutalist/ForWhom";
import { AccessSection } from "./brutalist/Access";
import { FaqSection } from "./brutalist/Faq";
import { useIndexRecords } from "@/lib/landing/hooks";

/**
 * The landing page.
 *
 * Everything below is rendered inside the `.brutalist` scope, which overrides
 * the font tokens and adds the ruled ground without touching the application
 * routes at /, /compare and /analytics.
 */
export default function LandingPage() {
  const { records, loading, failed } = useIndexRecords();

  return (
    <div className="brutalist relative min-h-screen">
      <Backdrop />
      <Masthead records={records} recordsLoading={loading} recordsFailed={failed} />
      <main className="relative">
        <Hero records={records} recordsLoading={loading} recordsFailed={failed} />
        <CorpusSection records={records} recordsLoading={loading} recordsFailed={failed} />
        <Doctrine />
        <GrammarSection />
        <ChunkingSection />
        <TesterSection />
        <ComparisonSection />
        <BatchSection />
        <LedgerSection />
        <ForWhomSection />
        <AccessSection records={records} recordsLoading={loading} recordsFailed={failed} />
        <FaqSection />
      </main>
      <Colophon records={records} recordsLoading={loading} recordsFailed={failed} />
    </div>
  );
}
