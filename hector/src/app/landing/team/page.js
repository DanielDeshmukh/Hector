import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Team" };

export default function Page() {
  return (
    <SubPageLayout title="Team" description="The people building zero-hallucination legal research.">
      <div className="grid md:grid-cols-2 gap-6">
        <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
          <div className="w-16 h-16 rounded-full bg-gold/20 flex items-center justify-center text-gold text-xl font-bold mb-4">DD</div>
          <h3 className="font-semibold text-white mb-1">Daniel Deshmukh</h3>
          <p className="text-sm text-gold mb-3">Creator &amp; Lead Developer</p>
          <p className="text-sm text-silver">Built HECTOR as a research project exploring reliable AI for Indian legal research. Designed the full-stack architecture from ingestion pipeline to zero-hallucination response generation.</p>
          <div className="flex items-center gap-3 mt-4">
            <a href="https://github.com/DanielDeshmukh" target="_blank" rel="noopener noreferrer" className="text-xs text-silver hover:text-gold transition-colors">GitHub</a>
            <a href="https://www.linkedin.com/in/daniel-deshmukh-7b08602b2" target="_blank" rel="noopener noreferrer" className="text-xs text-silver hover:text-gold transition-colors">LinkedIn</a>
            <a href="https://x.com/DeshmukhDa71837" target="_blank" rel="noopener noreferrer" className="text-xs text-silver hover:text-gold transition-colors">X</a>
          </div>
        </div>
      </div>
    </SubPageLayout>
  );
}
