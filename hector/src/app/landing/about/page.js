import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "About" };

export default function Page() {
  return (
    <SubPageLayout title="About HECTOR" description="Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval.">
      <div className="space-y-6 text-silver">
        <p>
          HECTOR is an AI-powered legal research engine built specifically for Indian law.
          It combines semantic search, chain-of-verification technology, and IPC-to-BNS
          cross-referencing to deliver zero-hallucination cited responses.
        </p>
        <p>
          The system indexes 38 bare acts into 13,479 searchable chunks, covering both
          the legacy Indian Penal Code and the new Bharatiya Nyaya Sanhita. Every citation
          is verified against primary legal sources before being presented.
        </p>
        <p>
          HECTOR was created by Daniel Deshmukh as a research project to explore how
          AI can be reliably used for legal research without fabricating citations or
          hallucinating legal provisions.
        </p>
        <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
          <h3 className="font-semibold text-white mb-3">Key Numbers</h3>
          <div className="grid grid-cols-2 gap-4">
            <div><span className="text-2xl font-bold text-gold">38</span><p className="text-sm text-silver">Bare Acts Indexed</p></div>
            <div><span className="text-2xl font-bold text-gold">13,479</span><p className="text-sm text-silver">Searchable Chunks</p></div>
            <div><span className="text-2xl font-bold text-gold">496</span><p className="text-sm text-silver">IPC-BNS Mappings</p></div>
            <div><span className="text-2xl font-bold text-gold">94%</span><p className="text-sm text-silver">Evaluation Accuracy</p></div>
          </div>
        </div>
      </div>
    </SubPageLayout>
  );
}
