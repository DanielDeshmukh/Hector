import { recentQueries } from './hectorData'
import { color, layoutStyles } from './hectorTheme'
import HoverButton from './HoverButton'

export default function Sidebar({ onNewQuery }) {
  return (
    <aside
      style={{
        width: 280,
        minWidth: 280,
        height: 'calc(100vh - 48px)',
        background: color.bgSidebar,
        borderRight: `1px solid ${color.borderSidebar}`,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <HoverButton
        onClick={onNewQuery}
        style={{
          margin: 12,
          padding: '10px 16px',
          background: 'rgba(255,255,255,0.04)',
          border: `1px solid ${color.borderInput}`,
          borderRadius: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          cursor: 'pointer',
          width: 'calc(100% - 24px)',
          color: color.textPrimary,
          font: 'inherit',
        }}
        hoverStyle={{ background: 'rgba(255,255,255,0.07)' }}
      >
        <span style={{ fontSize: 16, color: color.textSecondary }}>+</span>
        <span style={{ fontSize: 13, fontWeight: 500 }}>New Query</span>
      </HoverButton>
      <div style={{ padding: '16px 16px 8px', ...layoutStyles.label, letterSpacing: '0.12em' }}>RECENT QUERIES</div>
      {recentQueries.map((item) => (
        <div key={item.title} style={{ padding: '10px 16px', cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 14, color: color.textMuted, fontSize: 12, flexShrink: 0 }}>{item.icon}</span>
            <span style={{ fontSize: 13, color: color.textPrimary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 210 }}>{item.title}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 22, marginTop: 4 }}>
            <span style={{ fontSize: 11, color: color.textMuted }}>{item.date}</span>
            <span
              style={{
                fontSize: 10,
                fontWeight: 600,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                padding: '2px 6px',
                borderRadius: 3,
                background: item.category === 'CRIMINAL' ? color.badgeCriminalBg : color.badgeProceduralBg,
                color: item.category === 'CRIMINAL' ? color.badgeCriminalText : color.badgeProceduralText,
              }}
            >
              {item.category}
            </span>
          </div>
        </div>
      ))}
      <footer style={{ marginTop: 'auto', padding: '12px 16px', borderTop: `1px solid ${color.borderSidebar}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: color.textMuted }}>20+ Legal Texts Indexed</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: color.textMuted }}>
          <span className="pulse-dot" style={{ width: 5, height: 5, borderRadius: '50%', background: color.green }} />
          Online
        </span>
      </footer>
    </aside>
  )
}
