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
            Explore verified legal research across 38 bare acts with
            IPC-to-BNS cross-referencing. No account needed.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-charcoal text-white font-semibold rounded-xl hover:bg-slate-custom transition-colors border border-white/10"
            >
              Try HECTOR Now
              <Icons.ArrowRight />
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
