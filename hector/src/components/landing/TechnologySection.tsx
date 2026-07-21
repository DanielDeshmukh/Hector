const steps = [
  {
    number: "01",
    title: "Query Parsing",
    description:
      "Your natural language query is analyzed for legal entities, sections, and jurisdictional context.",
    code: 'QUERY: "Section 420 IPC punishment"\nENTITIES: ["Section 420", "IPC"]\nINTENT: "punishment_lookup"',
  },
  {
    number: "02",
    title: "Vector Retrieval",
    description:
      "Semantic search across 13,479+ indexed chunks to find the most relevant statutory provisions.",
    code: "RETRIEVAL: Top-K chunks\nSCORE: 0.947 similarity\nSOURCE: IPC Section 420",
  },
  {
    number: "03",
    title: "Cross-Reference Resolution",
    description:
      "Automatic mapping to current law—IPC sections are mapped to BNS equivalents where applicable.",
    code: "IPC §420 → BNS §318\nSTATUS: Active\nAMENDED: 2023-12-25",
  },
  {
    number: "04",
    title: "Verification Chain",
    description:
      "Each citation is verified against primary sources before inclusion in the response.",
    code: "VERIFY: Source exists\nVERIFY: Text matches\nVERIFY: Citation valid\nSTATUS: APPROVED",
  },
];

export default function TechnologySection() {
  return (
    <section id="technology" className="py-24 lg:py-32 bg-cream">
      <div className="w-full px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="inline-block px-4 py-1.5 bg-slate-custom text-silver text-sm font-medium rounded-full mb-4">
              How It Works
            </span>
            <h2 className="font-serif text-3xl lg:text-5xl font-semibold text-white mb-6">
              Chain-of-Verification Technology
            </h2>
            <p className="text-lg text-silver">
              A multi-layer pipeline that ensures every response is grounded in
              verified legal sources.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {steps.map((step) => (
              <div
                key={step.number}
                className="group bg-charcoal rounded-2xl p-8 border border-white/5 hover:border-gold-light hover:shadow-xl transition-all"
              >
                <div className="flex items-start gap-6">
                  <span className="text-5xl font-serif font-bold text-stone-200 group-hover:text-gold transition-colors">
                    {step.number}
                  </span>
                  <div className="flex-1 space-y-4">
                    <h3 className="font-semibold text-xl text-white">
                      {step.title}
                    </h3>
                    <p className="text-silver">{step.description}</p>
                    <div className="bg-charcoal rounded-lg p-4 font-mono text-sm border border-white/5">
                      <pre className="text-success whitespace-pre-wrap">
                        {step.code}
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
