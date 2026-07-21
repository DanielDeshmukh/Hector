import { Icons } from "./Icons";

export default function CTASection() {
  return (
    <section
      id="demo"
      className="py-24 lg:py-32 bg-charcoal border-t border-white/5"
    >
      <div className="w-full px-6 lg:px-12">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="font-serif text-3xl lg:text-5xl font-semibold text-white mb-6">
            Start Your Zero-Hallucination Research Today
          </h2>
          <p className="text-lg text-silver mb-10 max-w-2xl mx-auto">
            Join hundreds of legal professionals who trust HECTOR for verified
            legal research. Start your free 14-day trial—no credit card
            required.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="#"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-charcoal text-white font-semibold rounded-xl hover:bg-slate-custom transition-colors border border-white/10"
            >
              Get Started Free
              <Icons.ArrowRight />
            </a>
            <a
              href="#"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-transparent text-white font-medium rounded-xl border-2 border-white/30 hover:border-white/60 transition-colors"
            >
              Schedule Demo
            </a>
          </div>

          <p className="text-sm text-silver mt-6">
            Built for Indian law practitioners, researchers, and legal teams
          </p>
        </div>
      </div>
    </section>
  );
}
