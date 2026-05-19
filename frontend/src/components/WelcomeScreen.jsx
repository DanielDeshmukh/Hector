import { Shield, Search, Layers, FileCheck } from 'lucide-react'

const FEATURES = [
  {
    icon: Shield,
    title: 'Intent Routing',
    description: 'Classifies your query by legal domain to ensure accurate processing.',
  },
  {
    icon: Search,
    title: 'Hybrid Retrieval',
    description: 'Combines semantic search with keyword matching for comprehensive results.',
  },
  {
    icon: Layers,
    title: 'Hierarchical Context',
    description: 'Resolves parent sections and chapters for complete legal context.',
  },
  {
    icon: FileCheck,
    title: 'Citation Grounding',
    description: 'Verifies every response against source material with traceable citations.',
  },
]

const SUGGESTION_CHIPS = [
  'What is the punishment for murder under BNS?',
  'Difference between IPC and BNS Section 302',
  'Explain the new criminal law reforms in India',
  'What are the provisions for bail in non-bailable offenses?',
]

function WelcomeScreen({ onQuerySubmit }) {
  return (
    <div className="flex h-full w-full flex-col">
      {/* Central Brand & Features Section - Upper Half - Centered */}
      <div className="flex flex-1 flex-col items-center justify-center px-8 py-12">
        {/* Hero Logo - centered at top of this block */}
        <div className="mb-6 inline-flex items-center justify-center rounded-2xl border-2 border-gold/30 bg-gold/5 p-5">
          <Shield className="h-8 w-8 text-gold" />
        </div>

        {/* System Title */}
        <h1 className="mb-4 font-serif text-5xl text-gold-light sm:text-6xl leading-tight">HECTOR</h1>

        {/* System Subtitle/Tagline */}
        <p className="mb-12 max-w-145 text-center text-base leading-relaxed text-silver/80 sm:text-[16px]">
          Hard-RAG Legal Intelligence System - Your AI-powered companion for Indian legal research.
        </p>

        {/* Feature Grid - 2x2 */}
        <div className="grid w-full max-w-3xl grid-cols-2 gap-5">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="flex min-h-35 flex-col items-start gap-4 rounded-2xl border border-slate/40 bg-charcoal/40 p-6 transition-all hover:border-gold/40 hover:bg-charcoal/60"
            >
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gold/10 border border-gold/20">
                <feature.icon className="h-5 w-5 text-gold" />
              </div>
              <div>
                <h3 className="mb-2 text-sm font-semibold text-[#e8e8e8]">{feature.title}</h3>
                <p className="text-[12px] leading-relaxed text-silver/60">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Interactive Input Section - Bottom Half */}
      <div className="border-t border-slate/30 bg-cream/98 px-8 py-6">
        {/* Suggested Queries Row - 2x2 grid */}
        <div className="mb-6 grid grid-cols-2 gap-3 max-w-3xl mx-auto">
          {SUGGESTION_CHIPS.map((query) => (
            <button
              key={query}
              className="rounded-2xl border border-slate/40 bg-charcoal/50 px-6 py-3 text-left text-[13.5px] text-silver/80 transition-all hover:border-gold/50 hover:bg-charcoal/80 hover:text-gold/90 focus:border-gold/60"
              onClick={() => onQuerySubmit(query)}
            >
              {query}
            </button>
          ))}
        </div>

        {/* Main Search Input - 50-60% of screen width */}
        <div className="mx-auto flex max-w-[60%] items-center gap-4 rounded-2xl border border-slate/50 bg-charcoal/60 px-5 py-4 transition-all focus-within:border-gold/60 focus-within:shadow-[0_0_20px_rgba(201,169,98,0.15)]">
          <Search className="h-5 w-5 shrink-0 text-gold/70" />
          <input
            type="text"
            className="flex-1 border-none bg-transparent py-1 text-base text-[#e8e8e8] outline-none placeholder:text-silver/60"
            placeholder="Search Indian legal sections (e.g., 'Section 302 BNS' or 'murder penalty')..."
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                const target = e.target
                if (target.value.trim()) {
                  onQuerySubmit(target.value.trim())
                }
              }
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default WelcomeScreen