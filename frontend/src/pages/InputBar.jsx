import { useEffect, useRef } from 'react'
import { Paperclip, Send } from 'lucide-react'
import { color } from './hectorTheme'

export default function InputBar({ inputText, setInputText, onSubmit }) {
  const textareaRef = useRef(null)
  const hasText = inputText.trim().length > 0

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [inputText])

  return (
    <div style={{ padding: '16px 40px 20px', background: color.bgApp, borderTop: `1px solid ${color.borderSidebar}`, flexShrink: 0 }}>
      <div className="hector-input-box" style={{ background: color.bgInput, border: `1px solid ${color.borderInput}`, borderRadius: 10, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
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
          placeholder={'Enter your legal query - e.g., "What is the BNS equivalent of IPC Section 302?"'}
          rows={1}
          className="hector-query-input"
          style={{
            background: 'transparent',
            border: 'none',
            outline: 'none',
            resize: 'none',
            width: '100%',
            fontSize: 14,
            color: color.gold,
            caretColor: color.gold,
            lineHeight: 1.5,
            fontFamily: 'var(--font-body)',
            overflow: 'hidden',
          }}
        />
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Paperclip size={16} color="var(--text-muted)" style={{ cursor: 'pointer' }} />
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span style={{ fontSize: 11, color: color.textMuted, marginRight: 8 }}>Enter to submit</span>
            <button
              onClick={onSubmit}
              disabled={!hasText}
              style={{ width: 32, height: 32, background: hasText ? color.gold : color.sourceNumBg, borderRadius: 6, border: 'none', cursor: hasText ? 'pointer' : 'not-allowed', display: 'flex', alignItems: 'center', justifyContent: 'center', color: color.bgApp }}
            >
              <Send size={14} fill="var(--bg-app)" strokeWidth={2.3} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
