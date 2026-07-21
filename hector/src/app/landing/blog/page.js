import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Blog" };

export default function Page() {
  return (
    <SubPageLayout title="Blog" description="Insights on legal technology, Indian law, and AI-powered research.">
      <div className="space-y-6">
        {[
          { title: "Understanding the Bharatiya Nyaya Sanhita: A Complete Guide", date: "July 2026", tag: "Legal" },
          { title: "How Chain-of-Verification Eliminates Legal AI Hallucinations", date: "June 2026", tag: "Technology" },
          { title: "IPC to BNS: What Lawyers Need to Know About the Transition", date: "May 2026", tag: "Legal" },
          { title: "Building Zero-Hallucination Systems for Indian Law", date: "April 2026", tag: "Engineering" },
          { title: "Semantic Search vs Keyword Search for Legal Research", date: "March 2026", tag: "Technology" },
        ].map((post) => (
          <div key={post.title} className="p-6 bg-slate-custom rounded-xl border border-white/5 hover:border-gold-light transition-all cursor-pointer">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs font-medium px-2 py-0.5 bg-gold/20 text-gold rounded-full">{post.tag}</span>
              <span className="text-xs text-silver">{post.date}</span>
            </div>
            <h3 className="font-semibold text-white">{post.title}</h3>
          </div>
        ))}
      </div>
    </SubPageLayout>
  );
}
