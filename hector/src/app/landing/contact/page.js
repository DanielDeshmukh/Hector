import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Contact" };

export default function Page() {
  return (
    <SubPageLayout title="Contact" description="Get in touch with the HECTOR team.">
      <div className="space-y-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
            <h3 className="font-semibold text-white mb-2">General Inquiries</h3>
            <p className="text-sm text-silver">For general questions about HECTOR, reach out via email.</p>
            <p className="text-sm text-gold mt-2">daniel@hector-legal.ai</p>
          </div>
          <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
            <h3 className="font-semibold text-white mb-2">API Support</h3>
            <p className="text-sm text-silver">For technical issues with the API or integration help.</p>
            <p className="text-sm text-gold mt-2">support@hector-legal.ai</p>
          </div>
        </div>
        <div className="p-6 bg-slate-custom rounded-xl border border-white/5">
          <h3 className="font-semibold text-white mb-3">Connect on Social</h3>
          <div className="flex items-center gap-4">
            <a href="https://x.com/DeshmukhDa71837" target="_blank" rel="noopener noreferrer" className="text-sm text-silver hover:text-gold transition-colors">X (Twitter)</a>
            <a href="https://www.linkedin.com/in/daniel-deshmukh-7b08602b2" target="_blank" rel="noopener noreferrer" className="text-sm text-silver hover:text-gold transition-colors">LinkedIn</a>
            <a href="https://github.com/DanielDeshmukh" target="_blank" rel="noopener noreferrer" className="text-sm text-silver hover:text-gold transition-colors">GitHub</a>
          </div>
        </div>
      </div>
    </SubPageLayout>
  );
}
