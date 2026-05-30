import { FileText, Layers, Search, Shield } from 'lucide-react'

export const recentQueries = [
  { icon: '!', title: 'IPC Section 302 to BNS mapping', date: '14 Dec', category: 'CRIMINAL' },
  { icon: '!', title: 'Sedition laws under new criminal...', date: '14 Dec', category: 'CRIMINAL' },
  { icon: '#', title: 'Bail provisions comparison IPC v...', date: '13 Dec', category: 'PROCEDURAL' },
  { icon: '!', title: 'Defamation under BNS Section 3...', date: '13 Dec', category: 'CRIMINAL' },
  { icon: '!', title: 'Property offences transition guide', date: '12 Dec', category: 'CRIMINAL' },
]

export const features = [
  {
    icon: Shield,
    title: 'Intent Routing',
    body: 'Queries classified by legal domain - Criminal, Civil, or Procedural - to prevent data bleeding.',
  },
  {
    icon: Search,
    title: 'Hybrid Retrieval',
    body: 'Dual-search combining semantic understanding with keyword precision across 20+ legal texts.',
  },
  {
    icon: Layers,
    title: 'Hierarchical Context',
    body: 'Sub-clauses automatically pull parent Section, Chapter, and Act titles for complete context.',
  },
  {
    icon: FileText,
    title: 'Citation Grounding',
    body: 'Every response verified against source material. Unverified claims are refused, not guessed.',
  },
]

export const chips = [
  'What is the BNS equivalent of IPC Section 302?',
  'Compare the punishment for theft under IPC and BNS',
  'What changes were made to sedition laws in BNS?',
  'Explain Section 356 BNS and its IPC counterpart',
]

export const sources = [
  {
    title: "Ratanlal & Dhirajlal's The Indian Penal Code",
    author: 'Justice K.T. Thomas & M.A. Rashid',
    quote: 'Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.',
    location: 'Section 302 - Punishment for Murder · Page 1847, ¶3',
    match: '96% match',
    matchStyle: { background: 'var(--match-96-bg)', color: 'var(--match-96-text)' },
  },
  {
    title: 'Bharatiya Nyaya Sanhita - A Comprehensive Commentary',
    author: 'Dr. R.K. Sinha',
    quote: 'Section 103(2) introduces a new sub-category addressing mob lynching - when five or more persons acting in concert commit murder on specified grounds.',
    location: 'Section 103 - Punishment for Murder · Page 412, ¶1',
    match: '98% match',
    matchStyle: { background: 'var(--match-98-bg)', color: 'var(--match-98-text)' },
  },
  {
    title: 'The Code of Criminal Procedure with Bharatiya Nagarik Suraksha Sanhita',
    author: 'Prof. S.N. Misra',
    quote: 'All cases registered under the erstwhile Indian Penal Code prior to the date of commencement shall continue to be governed by the provisions of the IPC.',
    location: 'Section 1(2) - Commencement and Application · Page 23, ¶2',
    match: '82% match',
    matchStyle: { background: 'var(--match-82-bg)', color: 'var(--match-82-text)' },
  },
]
