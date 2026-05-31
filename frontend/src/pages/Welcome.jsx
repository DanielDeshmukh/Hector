import { Scale } from 'lucide-react'
import { chips, features } from './hectorData'
import { color } from './hectorTheme'
import HoverButton from './HoverButton'

export default function Welcome({ onChip }) {
  return (
    <section style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start', padding: '48px 40px 96px', gap: 28, overflowY: 'auto' }}>
      <div style={{ width: 72, height: 72, background: 'var(--gold-logo-bg)', border: `1px solid ${color.borderInput}`, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Scale size={36} color="var(--gold)" strokeWidth={1.6} />
      </div>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: 36, fontWeight: 700, letterSpacing: '0.15em', color: color.gold, margin: 0 }}>HECTOR</h1>
        <p style={{ fontSize: 14, color: color.textSecondary, textAlign: 'center', lineHeight: 1.6, maxWidth: 480, margin: '16px 0 0' }}>
          Hard-RAG Legal Intelligence System for Indian Law. Zero-hallucination retrieval from IPC to BNS with verifiable citations.
        </p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, background: color.borderSidebar, border: `1px solid ${color.borderSidebar}`, borderRadius: 8, overflow: 'hidden', maxWidth: 720, width: '100%', marginTop: 4 }}>
        {features.map(({ icon: Icon, title, body }) => (
          <div key={title} style={{ background: color.bgApp, padding: '20px 24px', minHeight: 126, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Icon size={20} color="var(--text-muted)" strokeWidth={1.6} />
              <div style={{ fontSize: 14, fontWeight: 600, color: color.textPrimary }}>{title}</div>
            </div>
            <div style={{ fontSize: 12, color: color.textSecondary, lineHeight: 1.5 }}>{body}</div>
          </div>
        ))}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 10, maxWidth: 720, width: '100%', marginTop: 8, marginBottom: 1.5 }}>
        {chips.map((chip) => (
          <HoverButton
            key={chip}
            onClick={() => onChip(chip)}
            style={{
              padding: '10px 14px',
              minHeight: 44,
              background: color.bgChip,
              border: `1px solid ${color.borderCard}`,
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 13,
              lineHeight: 1.35,
              color: color.gold,
              whiteSpace: 'normal',
              overflowWrap: 'anywhere',
              textAlign: 'center',
              font: 'inherit',
              width: '100%',
              minWidth: 0,
            }}
            hoverStyle={{ background: color.bgChipHover, borderColor: 'var(--border-selected)' }}
          >
            {chip}
          </HoverButton>
        ))}
      </div>
    </section>
  )
}
