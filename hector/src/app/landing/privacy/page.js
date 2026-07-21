import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Privacy Policy" };

export default function Page() {
  return (
    <SubPageLayout title="Privacy Policy" description="How HECTOR collects, uses, and protects your data.">
      <div className="space-y-6 text-silver text-sm">
        <p><strong className="text-white">Last updated:</strong> July 2026</p>
        <div>
          <h3 className="font-semibold text-white mb-2">1. Data We Collect</h3>
          <p>HECTOR collects search queries you submit, account information (if you create an account), and usage analytics to improve the service.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">2. How We Use Your Data</h3>
          <p>Your queries are processed to provide search results. We do not sell your data to third parties. Aggregated, anonymized usage data may be used to improve the service.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">3. Data Storage</h3>
          <p>HECTOR uses secure cloud infrastructure. Your data is encrypted in transit and at rest. We retain your query history for the duration of your account.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">4. Third-Party Services</h3>
          <p>HECTOR uses NVIDIA NIM API for AI inference and Pinecone for vector search. These services process data according to their own privacy policies.</p>
        </div>
        <div>
          <h3 className="font-semibold text-white mb-2">5. Your Rights</h3>
          <p>You can request deletion of your data at any time by contacting us. You can also export your query history.</p>
        </div>
      </div>
    </SubPageLayout>
  );
}
