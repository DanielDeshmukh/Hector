import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Disclaimer" };

export default function Page() {
  return (
    <SubPageLayout title="Disclaimer" description="Important disclaimers regarding HECTOR's legal research output.">
      <div className="space-y-6 text-silver text-sm">
        <div>
          <h3 className="font-semibold text-white mb-2">Not Legal Advice</h3>
          <p>HECTOR is an AI-powered research tool. The information provided through HECTOR is for general informational and research purposes only. Nothing on this platform constitutes legal advice.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">Citation Verification</h3>
          <p>While HECTOR uses chain-of-verification technology to verify citations against primary legal sources, users are strongly advised to independently verify all citations before relying on them in legal proceedings, court filings, or formal documentation.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">Accuracy Limitations</h3>
          <p>HECTOR indexes 38 bare acts and maintains 496 IPC-to-BNS cross-references. While we strive for completeness, the database may not include all amendments, notifications, or judicial interpretations. Legal information is subject to change.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">No Attorney-Client Relationship</h3>
          <p>Use of HECTOR does not create an attorney-client relationship between the user and HECTOR or its creator.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">AI Limitations</h3>
          <p>HECTOR uses artificial intelligence for research and response generation. While designed to minimize hallucinations, AI systems can produce errors. Always cross-reference with official legal texts.</p>
        </div>
      </div>
    </SubPageLayout>
  );
}
