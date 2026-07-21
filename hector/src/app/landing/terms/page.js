import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Terms of Service" };

export default function Page() {
  return (
    <SubPageLayout title="Terms of Service" description="Terms governing your use of HECTOR Legal Intelligence.">
      <div className="space-y-6 text-silver text-sm">
        <p><strong className="text-white">Last updated:</strong> July 2026</p>
        <div>
          <h3 className="font-semibold text-white mb-2">1. Acceptance of Terms</h3>
          <p>By accessing or using HECTOR, you agree to be bound by these Terms of Service. If you do not agree, do not use the service.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">2. Service Description</h3>
          <p>HECTOR is an AI-powered legal research tool that provides information about Indian law. It indexes 38 bare acts and provides IPC-to-BNS cross-referencing with chain-of-verification technology.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">3. Not Legal Advice</h3>
          <p>HECTOR provides information for research purposes only. It does not constitute legal advice. Always consult a qualified legal professional for specific legal matters.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">4. Citation Accuracy</h3>
          <p>HECTOR uses chain-of-verification to verify citations against primary sources. While we strive for accuracy, users should independently verify critical citations before formal submission.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">5. Limitation of Liability</h3>
          <p>HECTOR is provided &quot;as is&quot; without warranties. We are not liable for any decisions made based on the information provided by the service.</p>
        </div>
      </div>
    </SubPageLayout>
  );
}
