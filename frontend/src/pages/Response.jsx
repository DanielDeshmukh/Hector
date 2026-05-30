import { BookOpen } from 'lucide-react'
import { sources } from './hectorData'
import { color, layoutStyles } from './hectorTheme'
import HoverButton from './HoverButton'

export default function Response({ selectedSource, onSourceClick }) {
  return (
    <section style={{ flex: 1, overflowY: 'auto', padding: '24px 40px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ ...layoutStyles.label, marginBottom: -8 }}>RESPONSE</div>
      <div style={{ background: color.bgCard, border: `1px solid ${color.borderCard}`, borderRadius: 8, padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ ...layoutStyles.label, letterSpacing: '0.12em' }}>CHAIN OF VERIFICATION</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 0, flexWrap: 'wrap' }}>
          {['Intent Routing', 'Hybrid Retrieval', 'Hierarchical Context', 'Citation Grounding'].map((pill, index) => (
            <span key={pill} style={{ display: 'flex', alignItems: 'center' }}>
              {index > 0 && <span style={{ color: color.textMuted, fontSize: 12, padding: '0 8px' }}>--</span>}
              <span style={{ padding: '5px 12px', background: 'var(--pill-verified-bg)', border: '1px solid var(--pill-verified-border)', borderRadius: 4, display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--pill-verified-text)', fontWeight: 500 }}>
                <span style={{ fontSize: 11 }}>✓</span>
                {pill}
              </span>
            </span>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ padding: '5px 12px', background: 'var(--badge-criminal-law-bg)', border: '1px solid var(--badge-criminal-law-border)', borderRadius: 4, fontSize: 12, color: 'var(--badge-criminal-law-text)' }}># Criminal Law</span>
        <span style={{ padding: '5px 12px', background: 'var(--badge-confidence-bg)', border: '1px solid var(--badge-confidence-border)', borderRadius: 4, fontSize: 12, color: 'var(--badge-confidence-text)' }}>▥ Confidence: 97.3%</span>
        <span style={{ fontSize: 12, color: color.textMuted, marginLeft: 4 }}>14 Dec 2024, 04:02 pm</span>
      </div>
      <div className="hector-strong" style={{ fontSize: 14, lineHeight: 1.75, color: color.textPrimary }}>
        <p><strong>Section 302 of the Indian Penal Code (IPC)</strong> - which deals with the punishment for murder - has been replaced by <strong>Section 103 of the Bharatiya Nyaya Sanhita (BNS), 2023</strong>.</p>
        <p><strong>IPC Section 302 - Punishment for Murder:</strong><br />Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.</p>
        <p><strong>BNS Section 103 - Punishment for Murder:</strong><br /><strong>Section 103(1)</strong> of the BNS retains the same punishment framework as <strong>IPC Section 302</strong>. The offender shall be punished with death, or imprisonment for life, and shall also be liable to fine.</p>
        <p><strong>Key Differences & Additions under BNS:</strong><br /><strong>Section 103(2)</strong> of BNS introduces a new sub-category not present in <strong>IPC Section 302</strong>. It prescribes that when a group of five or more persons acting in concert commits murder on the ground of race, caste, community, sex, place of birth, language, personal belief, or any other similar ground, each member of such group shall be punished with -<br />* Death, or<br />* Imprisonment for life, and fine.</p>
      </div>
      <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.15em', textTransform: 'uppercase', color: color.textSecondary, marginTop: 8 }}>VERIFIED SOURCES (3)</div>
      {sources.map((source, index) => (
        <HoverButton
          key={source.title}
          onClick={() => onSourceClick(index)}
          style={{
            textAlign: 'left',
            background: selectedSource === index ? color.bgSelectedSource : color.bgCard,
            border: selectedSource === index ? '1px solid var(--border-selected)' : `1px solid ${color.borderCard}`,
            borderRadius: 8,
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            cursor: 'pointer',
            font: 'inherit',
          }}
          hoverStyle={{ background: color.bgCardHover }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <span style={{ width: 22, height: 22, background: color.sourceNumBg, borderRadius: 4, fontSize: 11, fontWeight: 600, color: color.sourceNumText, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{index + 1}</span>
                <span style={{ fontSize: 14, fontWeight: 600, color: color.textPrimary, marginLeft: 10 }}>{source.title}</span>
              </div>
              <div style={{ fontSize: 12, color: color.textSecondary, marginLeft: 32, marginTop: 2 }}>{source.author}</div>
            </div>
            <span style={{ fontSize: 14, color: color.textMuted, flexShrink: 0 }}>↗</span>
          </div>
          <div style={{ fontSize: 13, color: color.textSecondary, lineHeight: 1.6, fontStyle: 'italic' }}>"{source.quote}"</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            <BookOpen size={11} color="var(--text-muted)" />
            <span style={{ fontSize: 11, color: color.textMuted }}>{source.location}</span>
            <span style={{ color: color.textMuted }}>·</span>
            <span style={{ fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 3, ...source.matchStyle }}>{source.match}</span>
          </div>
        </HoverButton>
      ))}
    </section>
  )
}
