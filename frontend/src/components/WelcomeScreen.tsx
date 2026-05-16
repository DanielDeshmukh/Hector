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
    <div className="mx-auto flex min-h-full w-full max-w-7xl items-center px-6 py-10 sm:px-8 lg:px-12">
      <div className="grid w-full gap-10 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)] lg:gap-12">
        <div className="flex min-w-0 flex-col justify-center">
          <div className="mb-8 text-left">
            <div className="mb-5 inline-flex items-center justify-center rounded-full border-2 border-gold p-4">
              <Shield className="h-8 w-8 text-gold" />
            </div>
            <h1 className="mb-3 font-serif text-4xl text-gold-light sm:text-5xl">HECTOR</h1>
            <p className="max-w-[560px] text-sm leading-relaxed text-silver sm:text-[15px]">
              Hard-RAG Legal Intelligence System - Your AI-powered companion for Indian legal research.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:max-w-3xl">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="flex min-h-[132px] items-start gap-4 rounded-2xl border border-slate/40 bg-charcoal/50 p-5 transition-all hover:border-gold/30"
              >
                <feature.icon className="mt-0.5 h-[18px] w-[18px] shrink-0 text-gold" />
                <div>
                  <h3 className="mb-1 text-[13px] font-medium text-[#e8e8e8]">{feature.title}</h3>
                  <p className="text-[11.5px] leading-relaxed text-silver/40">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex min-w-0 flex-col justify-center rounded-[28px] border border-slate/40 bg-charcoal/35 p-6 sm:p-8">
          <div className="mb-6">
            <p className="mb-3 text-[10px] uppercase tracking-[0.18em] text-silver/50">Suggested Queries</p>
            <p className="max-w-sm text-sm leading-relaxed text-silver">
              Start with a focused legal question or use one of the prompts below to enter the research flow quickly.
            </p>
          </div>

          <div className="mb-6 flex flex-col gap-3">
            {SUGGESTION_CHIPS.map((query) => (
              <button
                key={query}
                className="w-full rounded-2xl border border-slate/50 bg-charcoal/50 px-5 py-4 text-left text-[13px] text-silver transition-all hover:border-gold hover:bg-charcoal/80 hover:text-gold"
                onClick={() => onQuerySubmit(query)}
              >
                {query}
              </button>
            ))}
          </div>

          <p className="max-w-sm text-[10.5px] text-silver/25">
            HECTOR provides legal information for research purposes only. Not a substitute for professional legal advice.
          </p>
        </div>
      </div>
    </div>
  )
}
