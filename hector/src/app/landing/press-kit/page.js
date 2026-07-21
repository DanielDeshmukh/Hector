import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Press Kit" };

export default function Page() {
  return (
    <SubPageLayout title="Press Kit" description="Brand assets and media resources for HECTOR Legal Intelligence.">
      <div className="space-y-6">
        <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
          <h3 className="font-semibold text-white mb-3">Brand Name</h3>
          <p className="text-sm text-silver">HECTOR — Hierarchical Evaluation of Civil-Criminal Textual&apos;s Orchestrator &amp; Retrieval</p>
        </div>
        <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
          <h3 className="font-semibold text-white mb-3">Tagline</h3>
          <p className="text-sm text-silver">Zero-Hallucination Legal Research for Indian Law</p>
        </div>
        <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
          <h3 className="font-semibold text-white mb-3">Description</h3>
          <p className="text-sm text-silver">AI-powered legal research engine with 38 bare acts, 13,479 chunks, IPC-to-BNS cross-referencing, and chain-of-verification for zero-hallucination cited responses.</p>
        </div>
        <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
          <h3 className="font-semibold text-white mb-3">Logo</h3>
          <p className="text-sm text-silver mb-3">The HECTOR logo is available at /tab-icon.png. Please use it as-is without modification.</p>
          <img src="/tab-icon.png" alt="HECTOR Logo" className="w-16 h-16 rounded-lg" />
        </div>
        <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
          <h3 className="font-semibold text-white mb-3">Creator</h3>
          <p className="text-sm text-silver">Daniel Deshmukh</p>
          <div className="flex items-center gap-3 mt-2">
            <a href="https://github.com/DanielDeshmukh" target="_blank" rel="noopener noreferrer" className="text-xs text-gold hover:text-gold-light transition-colors">GitHub</a>
            <a href="https://www.linkedin.com/in/daniel-deshmukh-7b08602b2" target="_blank" rel="noopener noreferrer" className="text-xs text-gold hover:text-gold-light transition-colors">LinkedIn</a>
            <a href="https://x.com/DeshmukhDa71837" target="_blank" rel="noopener noreferrer" className="text-xs text-gold hover:text-gold-light transition-colors">X</a>
          </div>
        </div>
      </div>
    </SubPageLayout>
  );
}
