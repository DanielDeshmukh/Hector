import { useState } from 'react'
import InputBar from './InputBar'
import Response from './Response'
import Sidebar from './Sidebar'
import SourcePanel from './SourcePanel'
import Topbar from './Topbar'
import Welcome from './Welcome'
import { color, layoutStyles } from './hectorTheme'

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
    <div style={layoutStyles.app}>
      <Topbar statusText={statusText} />
      <div style={layoutStyles.shell}>
        <Sidebar onNewQuery={newQuery} />
        <button
          style={{
            width: 20,
            height: 40,
            background: color.bgCard,
            border: `1px solid ${color.borderCard}`,
            borderRadius: '0 4px 4px 0',
            position: 'absolute',
            left: 280,
            top: '50%',
            transform: 'translateY(-50%)',
            zIndex: 10,
            color: color.textMuted,
            cursor: 'pointer',
            padding: 0,
          }}
        >
          {'<'}
        </button>
        <main style={layoutStyles.main}>
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
