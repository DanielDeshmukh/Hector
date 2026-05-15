import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'HECTOR | Legal Intelligence System',
  description: 'Hierarchical Evaluation of Civil-Criminal Textual\'s Orchestrator & Retrieval - Zero-hallucination legal research for Indian Law',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}