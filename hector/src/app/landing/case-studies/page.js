import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Case Studies" };

export default function Page() {
  return (
    <SubPageLayout title="Case Studies" description="See how legal professionals use HECTOR for verified research.">
      <div className="space-y-6">
        {[
          { title: "Criminal Law Firm, Mumbai", desc: "Reduced citation verification time by 70% using HECTOR's Chain-of-Verification pipeline for IPC-to-BNS cross-referencing during the code transition period.", result: "70% faster verification" },
          { title: "Corporate Legal Team, Delhi", desc: "Used HECTOR's API to automate compliance research across 38 bare acts, integrating legal intelligence directly into their case management system.", result: "Automated compliance research" },
          { title: "Solo Practitioner, Pune", desc: "Leveraged HECTOR's zero-hallucination guarantee to confidently cite BNS sections in court filings, with every citation verified against primary sources.", result: "100% verified citations" },
        ].map((study) => (
          <div key={study.title} className="p-6 bg-slate-custom rounded-xl border border-white/5">
            <h3 className="font-semibold text-white mb-2">{study.title}</h3>
            <p className="text-sm text-silver mb-4">{study.desc}</p>
            <span className="inline-block text-xs font-medium px-3 py-1 bg-success/20 text-success rounded-full">{study.result}</span>
          </div>
        ))}
      </div>
    </SubPageLayout>
  );
}
