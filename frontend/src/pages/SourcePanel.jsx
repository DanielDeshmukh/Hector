import { FileText, X } from 'lucide-react'
import { sources } from './hectorData'
import { color } from './hectorTheme'

const highlight = {
  background: 'var(--gold-bg)',
  color: color.gold,
  fontWeight: 600,
  borderRadius: 2,
  padding: '0 2px',
}

export default function SourcePanel({ source, onClose }) {
  if (source == null) return null

  const active = sources[source]

  return (
    <aside style={{ width: 380, minWidth: 380, height: 'calc(100vh - 48px)', background: color.bgSourcePanel, borderLeft: `1px solid ${color.borderSidebar}`, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '14px 20px', borderBottom: `1px solid ${color.borderSidebar}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <FileText size={14} color="var(--text-muted)" />
          <span style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: color.textMuted, marginLeft: 6 }}>SOURCE DOCUMENT</span>
        </div>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: color.textMuted, cursor: 'pointer', padding: '2px 6px', display: 'flex' }}><X size={18} /></button>
      </div>
      <div style={{ padding: '16px 20px', borderBottom: `1px solid ${color.borderSidebar}` }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: color.textPrimary, lineHeight: 1.4 }}>{active.title}</div>
        <div style={{ fontSize: 12, color: color.textSecondary, marginTop: 4 }}>{active.author}</div>
      </div>
      <div style={{ padding: '12px 20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, borderBottom: `1px solid ${color.borderSidebar}` }}>
        {[
          ['Indian Penal Code, 1860', 'Chapter XVI - Of Offences Affecting the Human Body'],
          ['Section 302 - Punishment for Murder', 'Page 1847, ¶2 · 2 matches'],
        ].map(([label, value]) => (
          <div key={label} style={{ background: color.bgCard, border: `1px solid ${color.borderCard}`, borderRadius: 6, padding: '10px 12px' }}>
            <div style={{ fontSize: 10, color: color.textMuted, marginBottom: 3 }}>{label}</div>
            <div style={{ fontSize: 12, color: color.textPrimary, fontWeight: 500, lineHeight: 1.35 }}>{value}</div>
          </div>
        ))}
      </div>
      <div style={{ padding: '8px 20px', textAlign: 'center', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: color.textMuted, borderBottom: `1px solid ${color.borderSidebar}` }}>PAGE 1847</div>
      <div style={{ padding: 20, fontSize: 13, lineHeight: 1.85, color: color.textSecondary, flex: 1 }}>
        Section 302. Punishment for murder.-Whoever commits murder shall be punished with death, or imprisonment for lif
        <mark style={highlight}>e, and shall</mark>
        {' '}also be liable to fine. COMMENT This section provides the punishment for murder. The sentence of death is the rule and imprisonment for life is an exception. The court has to state reasons why the sentence of death is not being imposed in a case of murder. The normal rule is that the offence of murder shall be punished with the sentence of death. The court{' '}
        <mark style={highlight}>is, however, permitted in its discretion to impose the lesser penalty of imprisonment for life. When the murder is committed in an extremely brutal, grot</mark>
        esque, diabolical, revolting or dastardly manner so as to arouse intense and extreme indignation of the community, the court may impose the death sentence. Where the accused does not act on any spur-of-the-moment provocation and there are no mitigating circumstances, the extreme penalty of death can be awarded. The scope and applicability of this section has been extensively discussed by the Supreme Court...
      </div>
      <div style={{ padding: '12px 20px', borderTop: `1px solid ${color.borderSidebar}`, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: color.textMuted }}>Relevance: 96%</span>
        <span style={{ marginLeft: 8, padding: '3px 10px', background: 'var(--gold-bg)', border: '1px solid var(--border-selected)', borderRadius: 3, fontSize: 10, fontWeight: 600, color: color.gold, letterSpacing: '0.06em' }}>High Confidence</span>
      </div>
    </aside>
  )
}
