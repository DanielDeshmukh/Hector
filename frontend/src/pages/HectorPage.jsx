import { useEffect, useRef, useState } from 'react'
import { BookOpen, FileText, Layers, Paperclip, Scale, Search, Send, Shield, X } from 'lucide-react'

const colors = {
  bgApp: '#0f1117',
  bgSidebar: '#161b24',
  bgCard: '#1c2333',
  bgCardHover: '#1e2738',
  bgChipHover: '#232b3d',
  textPrimary: '#e8e6e0',
  textSecondary: '#8a91a8',
  textMuted: '#4a5168',
  gold: '#c9a84c',
  goldDim: '#a08535',
  green: '#4ade80',
}

const recentQueries = [
  { icon: '⚡', title: 'IPC Section 302 to BNS mapping', date: '14 Dec', category: 'CRIMINAL' },
  { icon: '⚡', title: 'Sedition laws under new criminal...', date: '14 Dec', category: 'CRIMINAL' },
  { icon: '📋', title: 'Bail provisions comparison IPC v...', date: '13 Dec', category: 'PROCEDURAL' },
  { icon: '⚡', title: 'Defamation under BNS Section 3...', date: '13 Dec', category: 'CRIMINAL' },
  { icon: '⚡', title: 'Property offences transition guide', date: '12 Dec', category: 'CRIMINAL' },
]

const features = [
  {
    icon: Shield,
    title: 'Intent Routing',
    body: 'Queries classified by legal domain — Criminal, Civil, or Procedural — to prevent data bleeding.',
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

const chips = [
  'What is the BNS equivalent of IPC Section 302?',
  'Compare the punishment for theft under IPC and BNS',
  'What changes were made to sedition laws in BNS?',
  'Explain Section 356 BNS and its IPC counterpart',
]

const sources = [
  {
    title: "Ratanlal & Dhirajlal's The Indian Penal Code",
    author: 'Justice K.T. Thomas & M.A. Rashid',
    quote: 'Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.',
    location: 'Section 302 — Punishment for Murder · Page 1847, ¶3',
    match: '96% match',
    matchStyle: { background: 'rgba(34,197,94,0.15)', color: '#4ade80' },
  },
  {
    title: 'Bharatiya Nyaya Sanhita — A Comprehensive Commentary',
    author: 'Dr. R.K. Sinha',
    quote: 'Section 103(2) introduces a new sub-category addressing mob lynching — when five or more persons acting in concert commit murder on specified grounds.',
    location: 'Section 103 — Punishment for Murder · Page 412, ¶1',
    match: '98% match',
    matchStyle: { background: 'rgba(34,197,94,0.2)', color: '#4ade80' },
  },
  {
    title: 'The Code of Criminal Procedure with Bharatiya Nagarik Suraksha Sanhita',
    author: 'Prof. S.N. Misra',
    quote: 'All cases registered under the erstwhile Indian Penal Code prior to the date of commencement shall continue to be governed by the provisions of the IPC.',
    location: 'Section 1(2) — Commencement and Application · Page 23, ¶2',
    match: '82% match',
    matchStyle: { background: 'rgba(234,179,8,0.15)', color: '#facc15' },
  },
]

const styles = {
  app: {
    minHeight: '100vh',
    background: colors.bgApp,
    color: colors.textPrimary,
    fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    overflow: 'hidden',
  },
  topbar: {
    height: 48,
    background: colors.bgSidebar,
    borderBottom: '1px solid rgba(255,255,255,0.06)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 16px',
    position: 'relative',
  },
  logoBox: {
    width: 36,
    height: 36,
    background: '#1e2738',
    borderRadius: 8,
    border: '1px solid rgba(255,255,255,0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  shell: {
    display: 'flex',
    height: 'calc(100vh - 48px)',
    overflow: 'hidden',
    position: 'relative',
  },
  sidebar: {
    width: 280,
    minWidth: 280,
    height: 'calc(100vh - 48px)',
    background: colors.bgSidebar,
    borderRight: '1px solid rgba(255,255,255,0.06)',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
  },
  main: {
    flex: 1,
    height: 'calc(100vh - 48px)',
    background: colors.bgApp,
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    minWidth: 0,
  },
  label: {
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: '0.15em',
    textTransform: 'uppercase',
    color: colors.textMuted,
  },
}

function HoverButton({ children, style, hoverStyle, ...props }) {
  const [hover, setHover] = useState(false)
  return (
    <button
      {...props}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{ ...style, ...(hover ? hoverStyle : null) }}
    >
      {children}
    </button>
  )
}

function Topbar({ statusText }) {
  return (
    <header style={styles.topbar}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={styles.logoBox}>
          <Scale size={18} color={colors.gold} strokeWidth={1.8} />
        </div>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: '0.12em', color: colors.gold, lineHeight: 1 }}>HECTOR</div>
          <div style={{ fontSize: 9, fontWeight: 500, letterSpacing: '0.18em', textTransform: 'uppercase', color: colors.goldDim, marginTop: 1 }}>
            LEGAL INTELLIGENCE
          </div>
        </div>
      </div>
      <div style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: colors.textSecondary }}>
        <span className="pulse-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: colors.green }} />
        {statusText}
      </div>
      <div style={{ fontSize: 12, color: colors.textSecondary }}>Core Architecture <span style={{ color: colors.textMuted }}> // </span> Hard-RAG Pipeline</div>
    </header>
  )
}

function Sidebar({ onNewQuery }) {
  return (
    <aside style={styles.sidebar}>
      <HoverButton
        onClick={onNewQuery}
        style={{
          margin: 12,
          padding: '10px 16px',
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          cursor: 'pointer',
          width: 'calc(100% - 24px)',
          color: colors.textPrimary,
          font: 'inherit',
        }}
        hoverStyle={{ background: 'rgba(255,255,255,0.07)' }}
      >
        <span style={{ fontSize: 16, color: colors.textSecondary }}>+</span>
        <span style={{ fontSize: 13, fontWeight: 500 }}>New Query</span>
      </HoverButton>
      <div style={{ padding: '16px 16px 8px', ...styles.label, letterSpacing: '0.12em' }}>RECENT QUERIES</div>
      {recentQueries.map((item) => (
        <div key={item.title} style={{ padding: '10px 16px', cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 14, color: colors.textMuted, fontSize: 12, flexShrink: 0 }}>{item.icon}</span>
            <span style={{ fontSize: 13, color: colors.textPrimary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 210 }}>{item.title}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 22, marginTop: 4 }}>
            <span style={{ fontSize: 11, color: colors.textMuted }}>{item.date}</span>
            <span
              style={{
                fontSize: 10,
                fontWeight: 600,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                padding: '2px 6px',
                borderRadius: 3,
                background: item.category === 'CRIMINAL' ? 'rgba(239,68,68,0.15)' : 'rgba(59,130,246,0.15)',
                color: item.category === 'CRIMINAL' ? '#f87171' : '#60a5fa',
              }}
            >
              {item.category}
            </span>
          </div>
        </div>
      ))}
      <footer style={{ marginTop: 'auto', padding: '12px 16px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: colors.textMuted }}>20+ Legal Texts Indexed</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: colors.textMuted }}>
          <span className="pulse-dot" style={{ width: 5, height: 5, borderRadius: '50%', background: colors.green }} />
          Online
        </span>
      </footer>
    </aside>
  )
}

function Welcome({ onChip }) {
  return (
    <section style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 40px 120px', gap: 32, overflowY: 'auto' }}>
      <div style={{ width: 72, height: 72, background: '#1e2738', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Scale size={36} color={colors.gold} strokeWidth={1.6} />
      </div>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: 36, fontWeight: 700, letterSpacing: '0.15em', color: colors.gold, margin: 0 }}>HECTOR</h1>
        <p style={{ fontSize: 14, color: colors.textSecondary, textAlign: 'center', lineHeight: 1.6, maxWidth: 480, margin: '16px 0 0' }}>
          Hard-RAG Legal Intelligence System for Indian Law. Zero-hallucination retrieval from IPC to BNS with verifiable citations.
        </p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8, overflow: 'hidden', maxWidth: 720, width: '100%' }}>
        {features.map(({ icon: Icon, title, body }) => (
          <div key={title} style={{ background: colors.bgApp, padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Icon size={20} color={colors.textMuted} strokeWidth={1.6} />
              <div style={{ fontSize: 14, fontWeight: 600, color: colors.textPrimary }}>{title}</div>
            </div>
            <div style={{ fontSize: 12, color: colors.textSecondary, lineHeight: 1.5 }}>{body}</div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center', maxWidth: 720, width: '100%' }}>
        {[chips.slice(0, 2), chips.slice(2)].map((row, rowIndex) => (
          <div key={rowIndex} style={{ display: 'flex', gap: 8, justifyContent: 'center', width: '100%', flexWrap: 'wrap' }}>
            {row.map((chip) => (
              <HoverButton
                key={chip}
                onClick={() => onChip(chip)}
                style={{ padding: '10px 18px', background: colors.bgCard, border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6, cursor: 'pointer', fontSize: 13, color: colors.gold, whiteSpace: 'nowrap', font: 'inherit' }}
                hoverStyle={{ background: colors.bgChipHover, borderColor: 'rgba(201,168,76,0.25)' }}
              >
                {chip}
              </HoverButton>
            ))}
          </div>
        ))}
      </div>
    </section>
  )
}

function Response({ selectedSource, onSourceClick }) {
  return (
    <section style={{ flex: 1, overflowY: 'auto', padding: '24px 40px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ ...styles.label, marginBottom: -8 }}>RESPONSE</div>
      <div style={{ background: colors.bgCard, border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ ...styles.label, letterSpacing: '0.12em' }}>CHAIN OF VERIFICATION</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 0, flexWrap: 'wrap' }}>
          {['Intent Routing', 'Hybrid Retrieval', 'Hierarchical Context', 'Citation Grounding'].map((pill, index) => (
            <span key={pill} style={{ display: 'flex', alignItems: 'center' }}>
              {index > 0 && <span style={{ color: colors.textMuted, fontSize: 12, padding: '0 8px' }}>——</span>}
              <span style={{ padding: '5px 12px', background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 4, display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: colors.green, fontWeight: 500 }}>
                <span style={{ fontSize: 11 }}>✓</span>
                {pill}
              </span>
            </span>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ padding: '5px 12px', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 4, fontSize: 12, color: '#f87171' }}># Criminal Law</span>
        <span style={{ padding: '5px 12px', background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.25)', borderRadius: 4, fontSize: 12, color: '#60a5fa' }}>▥ Confidence: 97.3%</span>
        <span style={{ fontSize: 12, color: colors.textMuted, marginLeft: 4 }}>14 Dec 2024, 04:02 pm</span>
      </div>
      <div style={{ fontSize: 14, lineHeight: 1.75, color: colors.textPrimary }}>
        <p><strong>Section 302 of the Indian Penal Code (IPC)</strong> — which deals with the punishment for murder — has been replaced by <strong>Section 103 of the Bharatiya Nyaya Sanhita (BNS), 2023</strong>.</p>
        <p><strong>IPC Section 302 — Punishment for Murder:</strong><br />Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.</p>
        <p><strong>BNS Section 103 — Punishment for Murder:</strong><br /><strong>Section 103(1)</strong> of the BNS retains the same punishment framework as <strong>IPC Section 302</strong>. The offender shall be punished with death, or imprisonment for life, and shall also be liable to fine.</p>
        <p><strong>Key Differences & Additions under BNS:</strong><br /><strong>Section 103(2)</strong> of BNS introduces a new sub-category not present in <strong>IPC Section 302</strong>. It prescribes that when a group of five or more persons acting in concert commits murder on the ground of race, caste, community, sex, place of birth, language, personal belief, or any other similar ground, each member of such group shall be punished with —<br />• Death, or<br />• Imprisonment for life, and fine.</p>
      </div>
      <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.15em', textTransform: 'uppercase', color: colors.textSecondary, marginTop: 8 }}>VERIFIED SOURCES (3)</div>
      {sources.map((source, index) => (
        <HoverButton
          key={source.title}
          onClick={() => onSourceClick(index)}
          style={{
            textAlign: 'left',
            background: selectedSource === index ? colors.bgCardHover : colors.bgCard,
            border: selectedSource === index ? '1px solid rgba(201,168,76,0.25)' : '1px solid rgba(255,255,255,0.07)',
            borderRadius: 8,
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            cursor: 'pointer',
            font: 'inherit',
          }}
          hoverStyle={{ background: colors.bgCardHover }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <span style={{ width: 22, height: 22, background: '#2a3347', borderRadius: 4, fontSize: 11, fontWeight: 600, color: colors.textPrimary, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{index + 1}</span>
                <span style={{ fontSize: 14, fontWeight: 600, color: colors.textPrimary, marginLeft: 10 }}>{source.title}</span>
              </div>
              <div style={{ fontSize: 12, color: colors.textSecondary, marginLeft: 32, marginTop: 2 }}>{source.author}</div>
            </div>
            <span style={{ fontSize: 14, color: colors.textMuted, flexShrink: 0 }}>↗</span>
          </div>
          <div style={{ fontSize: 13, color: colors.textSecondary, lineHeight: 1.6, fontStyle: 'italic' }}>"{source.quote}"</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            <BookOpen size={11} color={colors.textMuted} />
            <span style={{ fontSize: 11, color: colors.textMuted }}>{source.location}</span>
            <span style={{ color: colors.textMuted }}>·</span>
            <span style={{ fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 3, ...source.matchStyle }}>{source.match}</span>
          </div>
        </HoverButton>
      ))}
    </section>
  )
}

function SourcePanel({ source, onClose }) {
  if (source == null) return null
  const active = sources[source]
  return (
    <aside style={{ width: 380, minWidth: 380, height: 'calc(100vh - 48px)', background: colors.bgSidebar, borderLeft: '1px solid rgba(255,255,255,0.06)', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <FileText size={14} color={colors.textMuted} />
          <span style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: colors.textMuted, marginLeft: 6 }}>SOURCE DOCUMENT</span>
        </div>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: colors.textMuted, cursor: 'pointer', padding: '2px 6px', display: 'flex' }}><X size={18} /></button>
      </div>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: colors.textPrimary, lineHeight: 1.4 }}>{active.title}</div>
        <div style={{ fontSize: 12, color: colors.textSecondary, marginTop: 4 }}>{active.author}</div>
      </div>
      <div style={{ padding: '12px 20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        {[
          ['Indian Penal Code, 1860', 'Chapter XVI — Of Offences Affecting the Human Body'],
          ['Section 302 — Punishment for Murder', 'Page 1847, ¶2 · 2 matches'],
        ].map(([label, value]) => (
          <div key={label} style={{ background: colors.bgCard, border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6, padding: '10px 12px' }}>
            <div style={{ fontSize: 10, color: colors.textMuted, marginBottom: 3 }}>{label}</div>
            <div style={{ fontSize: 12, color: colors.textPrimary, fontWeight: 500, lineHeight: 1.35 }}>{value}</div>
          </div>
        ))}
      </div>
      <div style={{ padding: '8px 20px', textAlign: 'center', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: colors.textMuted, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>PAGE 1847</div>
      <div style={{ padding: 20, fontSize: 13, lineHeight: 1.85, color: colors.textSecondary, flex: 1 }}>
        Section 302. Punishment for murder.—Whoever commits murder shall be punished with death, or imprisonment for lif
        <mark style={highlight}>e, and shall</mark>
        {' '}also be liable to fine. COMMENT This section provides the punishment for murder. The sentence of death is the rule and imprisonment for life is an exception. The court has to state reasons why the sentence of death is not being imposed in a case of murder. The normal rule is that the offence of murder shall be punished with the sentence of death. The court{' '}
        <mark style={highlight}>is, however, permitted in its discretion to impose the lesser penalty of imprisonment for life. When the murder is committed in an extremely brutal, grot</mark>
        esque, diabolical, revolting or dastardly manner so as to arouse intense and extreme indignation of the community, the court may impose the death sentence. Where the accused does not act on any spur-of-the-moment provocation and there are no mitigating circumstances, the extreme penalty of death can be awarded. The scope and applicability of this section has been extensively discussed by the Supreme Court...
      </div>
      <div style={{ padding: '12px 20px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: colors.textMuted }}>Relevance: 96%</span>
        <span style={{ marginLeft: 8, padding: '3px 10px', background: 'rgba(201,168,76,0.12)', border: '1px solid rgba(201,168,76,0.25)', borderRadius: 3, fontSize: 10, fontWeight: 600, color: colors.gold, letterSpacing: '0.06em' }}>High Confidence</span>
      </div>
    </aside>
  )
}

const highlight = {
  background: 'rgba(201,168,76,0.2)',
  color: colors.gold,
  fontWeight: 600,
  borderRadius: 2,
  padding: '0 2px',
}

function InputBar({ inputText, setInputText, onSubmit }) {
  const textareaRef = useRef(null)
  const hasText = inputText.trim().length > 0

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [inputText])

  return (
    <div style={{ padding: '16px 40px 20px', background: colors.bgApp, borderTop: '1px solid rgba(255,255,255,0.06)', flexShrink: 0 }}>
      <div className="hector-input-box" style={{ background: colors.bgCard, border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <textarea
          ref={textareaRef}
          value={inputText}
          onChange={(event) => setInputText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              onSubmit()
            }
          }}
          placeholder={'Enter your legal query — e.g., "What is the BNS equivalent of IPC Section 302?"'}
          rows={1}
          className="hector-query-input"
          style={{
            background: 'transparent',
            border: 'none',
            outline: 'none',
            resize: 'none',
            width: '100%',
            fontSize: 14,
            color: colors.gold,
            caretColor: colors.gold,
            lineHeight: 1.5,
            fontFamily: 'Inter, system-ui, sans-serif',
            overflow: 'hidden',
          }}
        />
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Paperclip size={16} color={colors.textMuted} style={{ cursor: 'pointer' }} />
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span style={{ fontSize: 11, color: colors.textMuted, marginRight: 8 }}>↵ to submit</span>
            <button
              onClick={onSubmit}
              disabled={!hasText}
              style={{ width: 32, height: 32, background: hasText ? colors.gold : '#2a3347', borderRadius: 6, border: 'none', cursor: hasText ? 'pointer' : 'not-allowed', display: 'flex', alignItems: 'center', justifyContent: 'center', color: colors.bgApp }}
            >
              <Send size={14} fill={colors.bgApp} strokeWidth={2.3} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function HectorPage() {
  const [view, setView] = useState('welcome')
  const [inputText, setInputText] = useState('')
  const [selectedSource, setSelectedSource] = useState(null)
  const [statusText, setStatusText] = useState('Ready for queries')

  const submit = (text = inputText) => {
    if (!text.trim()) return
    setInputText(text)
    setView('response')
    setStatusText('Query Resolved')
  }

  const newQuery = () => {
    setView('welcome')
    setInputText('')
    setSelectedSource(null)
    setStatusText('Ready for queries')
  }

  return (
    <div style={styles.app}>
      <style>{`
        * { box-sizing: border-box; }
        body { margin: 0; background: #0f1117; }
        strong { font-weight: 700; color: #e8e6e0; }
        @keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .pulse-dot { animation: pulse-dot 2s ease-in-out infinite; }
        .hector-query-input::placeholder { color: #4a5168; }
        .hector-input-box:focus-within { border-color: rgba(255,255,255,0.15) !important; background: #1e2738; }
      `}</style>
      <Topbar statusText={statusText} />
      <div style={styles.shell}>
        <Sidebar onNewQuery={newQuery} />
        <button style={{ width: 20, height: 40, background: colors.bgCard, border: '1px solid rgba(255,255,255,0.07)', borderRadius: '0 4px 4px 0', position: 'absolute', left: 280, top: '50%', transform: 'translateY(-50%)', zIndex: 10, color: colors.textMuted, cursor: 'pointer', padding: 0 }}>{'<'}</button>
        <main style={styles.main}>
          <div style={{ display: 'flex', flexDirection: 'row', flex: 1, overflow: 'hidden', minHeight: 0 }}>
            <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
              {view === 'welcome' ? <Welcome onChip={submit} /> : <Response selectedSource={selectedSource} onSourceClick={setSelectedSource} />}
            </div>
            <SourcePanel source={selectedSource} onClose={() => setSelectedSource(null)} />
          </div>
          <InputBar inputText={inputText} setInputText={setInputText} onSubmit={() => submit()} />
        </main>
      </div>
    </div>
  )
}
