import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Changelog" };

export default function Page() {
  return (
    <SubPageLayout title="Changelog" description="Track every improvement, fix, and new feature in HECTOR.">
      <div className="space-y-8">
        {[
          { version: "v1.4.0", date: "July 2026", changes: ["Nemotron neural reranker via NIM API", "LLM-primary answer synthesis", "Smart template filtering", "Vehicle theft query expansion"] },
          { version: "v1.3.0", date: "July 2026", changes: ["Pinecone Cloud vector database migration", "13,479 chunks indexed across 38 bare acts", "IPC-to-BNS cross-reference map (496 entries)", "CI pipeline with Ruff lint + pytest"] },
          { version: "v1.2.0", date: "June 2026", changes: ["Chain-of-Verification pipeline", "Multi-layer citation verification", "BNS 2023, BNSS, BSA ingestion", "Hindi multilingual support"] },
          { version: "v1.1.0", date: "May 2026", changes: ["Hybrid BM25 + semantic retrieval", "Query intelligence classifier", "Entity extraction for legal terms", "IPC section parsing"] },
          { version: "v1.0.0", date: "April 2026", changes: ["Initial release", "38 bare acts ingested", "Basic legal research queries", "IPC-to-BNS cross-referencing"] },
        ].map((release) => (
          <div key={release.version} className="relative pl-8 border-l-2 border-gold/30">
            <div className="absolute -left-2 top-0 w-3 h-3 rounded-full bg-gold" />
            <div className="flex items-baseline gap-3 mb-2">
              <h3 className="font-semibold text-white">{release.version}</h3>
              <span className="text-sm text-silver">{release.date}</span>
            </div>
            <ul className="space-y-1">
              {release.changes.map((c) => (
                <li key={c} className="text-sm text-silver flex items-start gap-2">
                  <span className="w-1 h-1 rounded-full bg-silver mt-2 flex-shrink-0" />
                  {c}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </SubPageLayout>
  );
}
