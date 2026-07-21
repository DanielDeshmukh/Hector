import SubPageLayout from "@/components/landing/SubPageLayout";

export const metadata = { title: "Pricing" };

export default function Page() {
  return (
    <SubPageLayout title="Pricing" description="Simple, transparent pricing for legal professionals.">
      <div className="grid md:grid-cols-3 gap-6">
        {[
          { name: "Starter", price: "Free", period: "14-day trial", features: ["50 queries/month", "All 38 bare acts", "IPC-BNS cross-referencing", "Basic citation verification", "Email support"], cta: "Start Free Trial" },
          { name: "Professional", price: "\u20B9999", period: "/month", features: ["Unlimited queries", "All 38 bare acts", "Advanced CoVe verification", "Exportable reports", "Priority support", "API access"], cta: "Get Started" },
          { name: "Enterprise", price: "Custom", period: "tailored to your firm", features: ["Everything in Professional", "Custom bare act ingestion", "Dedicated support", "SLA guarantee", "On-premise deployment option", "Team management"], cta: "Contact Sales" },
        ].map((plan) => (
          <div key={plan.name} className="p-6 bg-slate-custom rounded-xl border border-white/5 hover:border-gold-light transition-all">
            <h3 className="font-serif text-xl font-semibold text-white mb-2">{plan.name}</h3>
            <div className="flex items-baseline gap-1 mb-1">
              <span className="text-3xl font-bold text-gold">{plan.price}</span>
              {plan.period !== "14-day trial" && <span className="text-sm text-silver">{plan.period}</span>}
            </div>
            {plan.period === "14-day trial" && <p className="text-xs text-silver mb-4">No credit card required</p>}
            <ul className="space-y-2 my-6">
              {plan.features.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-silver">
                  <span className="w-1.5 h-1.5 rounded-full bg-success flex-shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
            <button className="w-full py-3 rounded-lg bg-gold text-charcoal font-medium hover:bg-gold-light transition-colors">{plan.cta}</button>
          </div>
        ))}
      </div>
    </SubPageLayout>
  );
}
