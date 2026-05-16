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
    <div className="mx-auto flex min-h-full w-full max-w-7xl items-center px-8 py-12 sm:px-10 lg:px-14">
      <div className="grid w-full gap-12 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.95fr)] lg:gap-14">
        <div className="flex min-w-0 flex-col justify-center">
          <div className="mb-10 text-left">
            <div className="mb-6 inline-flex items-center justify-center rounded-2xl border-2 border-gold/30 bg-gold/5 p-5">
              <Shield className="h-8 w-8 text-gold" />
            </div>
            <h1 className="mb-4 font-serif text-5xl text-gold-light sm:text-6xl leading-tight">HECTOR</h1>
            <p className="max-w-[580px] text-base leading-relaxed text-silver/80 sm:text-[16px]">
              Hard-RAG Legal Intelligence System - Your AI-powered companion for Indian legal research.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:max-w-3xl">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="flex min-h-[140px] flex-col items-start gap-4 rounded-2xl border border-slate/40 bg-charcoal/40 p-6 transition-all hover:border-gold/40 hover:bg-charcoal/60"
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

        <div className="flex min-w-0 flex-col justify-center rounded-[32px] border border-slate/40 bg-charcoal/35 p-8 sm:p-10">
          <div className="mb-8">
            <p className="mb-3 text-[10px] uppercase tracking-[0.2em] text-silver/50 font-semibold">Suggested Queries</p>
            <p className="max-w-sm text-sm leading-relaxed text-silver/70">
              Start with a focused legal question or use one of the prompts below to enter the research flow quickly.
            </p>
          </div>

          <div className="mb-8 flex flex-col gap-3">
            {SUGGESTION_CHIPS.map((query) => (
              <button
                key={query}
                className="w-full rounded-2xl border border-slate/40 bg-charcoal/50 px-6 py-4 text-left text-[13.5px] text-silver/80 transition-all hover:border-gold/50 hover:bg-charcoal/80 hover:text-gold/90 focus:border-gold/60"
                onClick={() => onQuerySubmit(query)}
              >
                {query}
              </button>
            ))}
          </div>

          <p className="max-w-sm text-[11px] text-silver/40 leading-relaxed">
            HECTOR provides legal information for research purposes only. Not a substitute for professional legal advice.
          </p>
        </div>
      </div>
    </div>
  )
}
