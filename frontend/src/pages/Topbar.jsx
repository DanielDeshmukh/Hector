import { Scale } from 'lucide-react'
import { color } from './hectorTheme'

export default function Topbar({ statusText }) {
  return (
    <header
      style={{
        height: 48,
        background: color.bgTopbar,
        borderBottom: `1px solid ${color.borderSidebar}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        position: 'relative',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div
          style={{
            width: 36,
            height: 36,
            background: 'var(--gold-logo-bg)',
            borderRadius: 8,
            border: `1px solid ${color.borderInput}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <Scale size={18} color="var(--gold)" strokeWidth={1.8} />
        </div>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: '0.12em', color: color.gold, lineHeight: 1 }}>HECTOR</div>
          <div style={{ fontSize: 9, fontWeight: 500, letterSpacing: '0.18em', textTransform: 'uppercase', color: color.goldDim, marginTop: 1 }}>
            LEGAL INTELLIGENCE
          </div>
        </div>
      </div>
      <div style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: color.textSecondary }}>
        <span className="pulse-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: color.green }} />
        {statusText}
      </div>
      <div style={{ fontSize: 12, color: color.textSecondary }}>Core Architecture <span style={{ color: color.textMuted }}> // </span> Hard-RAG Pipeline</div>
    </header>
  )
}
