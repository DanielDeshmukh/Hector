'use client'

import { Shield, Search, Layers, FileCheck } from 'lucide-react'

interface WelcomeScreenProps {
  onQuerySubmit: (query: string) => void
}

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

export function WelcomeScreen({ onQuerySubmit }: WelcomeScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-full px-6 py-12">
      {/* Logo & Title Section */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full border-2 border-gold mb-4">
          <Shield className="w-8 h-8 text-gold" />
        </div>
        <h1 className="font-serif text-4xl text-gold-light mb-2">HECTOR</h1>
        <p className="text-silver text-sm max-w-[432px] leading-relaxed">
          Hard-RAG Legal Intelligence System — Your AI-powered companion for Indian legal research.
        </p>
      </div>

      {/* Feature Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mb-12">
        {FEATURES.map((feature) => (
          <div
            key={feature.title}
            className="flex items-start gap-3 p-4 bg-charcoal/50 border border-slate/40 rounded-lg hover:border-gold/30 transition-all"
          >
            <feature.icon className="w-[18px] h-[18px] text-gold shrink-0 mt-0.5" />
            <div>
              <h3 className="text-[13px] font-medium text-[#e8e8e8] mb-1">{feature.title}</h3>
              <p className="text-[11.5px] text-silver/40 leading-relaxed">{feature.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Suggestion Chips */}
      <div className="flex flex-wrap justify-center gap-2 mb-8">
        {SUGGESTION_CHIPS.map((query) => (
          <button
            key={query}
            className="px-4 py-2 text-[13px] text-silver border border-slate/50 bg-charcoal/50 rounded-full hover:border-gold hover:text-gold hover:bg-charcoal/80 transition-all"
            onClick={() => onQuerySubmit(query)}
          >
            {query}
          </button>
        ))}
      </div>

      {/* Disclaimer */}
      <p className="text-[10.5px] text-silver/25 text-center max-w-lg">
        HECTOR provides legal information for research purposes only. Not a substitute for professional legal advice.
      </p>
    </div>
  )
}