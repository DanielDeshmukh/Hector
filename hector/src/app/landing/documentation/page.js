import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Documentation" };

export default function Page() {
  return (
    <SubPageLayout title="Documentation" description="Everything you need to get started with HECTOR.">
      <div className="space-y-6">
        {[
          { title: "Getting Started", desc: "Set up your account and run your first legal research query in under 5 minutes.", icon: "01" },
          { title: "Query Syntax", desc: "Learn how to write effective legal queries, use section references, and filter by act.", icon: "02" },
          { title: "Understanding Citations", desc: "How HECTOR verifies citations, confidence scores, and the Chain-of-Verification pipeline.", icon: "03" },
          { title: "IPC-BNS Cross-References", desc: "How cross-referencing works between the Indian Penal Code and Bharatiya Nyaya Sanhita.", icon: "04" },
          { title: "API Reference", desc: "Complete REST API documentation with endpoints, parameters, and response formats.", icon: "05" },
          { title: "Export & Reports", desc: "Generate court-ready documentation and export citation lists.", icon: "06" },
        ].map((doc) => (
          <div key={doc.title} className="p-6 bg-slate-custom rounded-xl border border-white/5 hover:border-gold-light transition-all cursor-pointer">
            <div className="flex items-start gap-4">
              <span className="text-2xl font-serif font-bold text-gold">{doc.icon}</span>
              <div>
                <h3 className="font-semibold text-white mb-1">{doc.title}</h3>
                <p className="text-sm text-silver">{doc.desc}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </SubPageLayout>
  );
}
