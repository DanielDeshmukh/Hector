import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Careers" };

export default function Page() {
  return (
    <SubPageLayout title="Careers" description="Help us build the future of legal research in India.">
      <div className="space-y-6">
        <p className="text-silver">
          We&apos;re looking for passionate individuals who want to make legal research
          more reliable and accessible. If you care about AI accuracy and Indian law,
          we&apos;d love to hear from you.
        </p>
        <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
          <h3 className="font-semibold text-white mb-2">Open Positions</h3>
          <p className="text-sm text-silver mb-4">No open positions at this time. Check back later or reach out directly.</p>
        </div>
        <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
          <h3 className="font-semibold text-white mb-2">General Inquiry</h3>
          <p className="text-sm text-silver">Interested in contributing? Send your portfolio to <span className="text-gold">daniel@hector-legal.ai</span></p>
        </div>
      </div>
    </SubPageLayout>
  );
}
