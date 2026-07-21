import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "API Access" };

export default function Page() {
  return (
    <SubPageLayout title="API Access" description="Integrate HECTOR's legal research capabilities into your own applications.">
      <div className="space-y-8">
        <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
          <h3 className="font-semibold text-white mb-2">REST API</h3>
          <p className="text-silver text-sm mb-4">Query HECTOR programmatically via a simple REST interface. Returns verified legal citations with confidence scores.</p>
          <div className="bg-charcoal rounded-lg p-4 font-mono text-sm border border-white/5">
            <pre className="text-success whitespace-pre-wrap">{`POST /api/search
Authorization: Bearer YOUR_API_KEY

{
  "query": "What is the punishment for Section 420 IPC?",
  "format": "detailed"
}`}</pre>
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
            <h3 className="font-semibold text-white mb-2">Rate Limits</h3>
            <ul className="space-y-2 text-sm text-silver">
              <li>Starter: 50 requests/day</li>
              <li>Professional: 1,000 requests/day</li>
              <li>Enterprise: Custom limits</li>
            </ul>
          </div>
          <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
            <h3 className="font-semibold text-white mb-2">Response Format</h3>
            <ul className="space-y-2 text-sm text-silver">
              <li>JSON with verified citations</li>
              <li>Confidence scores for each result</li>
              <li>IPC-to-BNS cross-references</li>
            </ul>
          </div>
        </div>
      </div>
    </SubPageLayout>
  );
}
