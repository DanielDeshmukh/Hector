'use client'

import { useEffect, useState } from 'react'
import { Header, SearchBar, DualPaneViewer, ResultList, ComparePanel, ErrorMessage, SidePanel } from '@/components'
import { useAppStore } from '@/lib/store'
import { apiClient } from '@/lib/api'

export default function Home() {
  const { activeTab, compareResult, setStatus, setIsLoadingStatus, isLoadingStatus, status } = useAppStore()
  const [statusError, setStatusError] = useState<string | null>(null)

  useEffect(() => {
    const loadStatus = async () => {
      setIsLoadingStatus(true)
      try {
        const statusData = await apiClient.status()
        setStatus(statusData)
      } catch (err) {
        setStatusError(err instanceof Error ? err.message : 'Failed to connect to API')
        setStatus(null)
      } finally {
        setIsLoadingStatus(false)
      }
    }

    loadStatus()
    const interval = setInterval(loadStatus, 30000)
    return () => clearInterval(interval)
  }, [setStatus, setIsLoadingStatus])

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header />
      <ErrorMessage />
      <SidePanel />

      {activeTab === 'search' ? (
        <>
          <SearchBar />
          <div className="flex flex-1 overflow-hidden">
            <ResultList />
            <DualPaneViewer />
          </div>
        </>
      ) : (
        <div className="flex flex-col flex-1 overflow-hidden">
          <ComparePanel />
          {compareResult && (
            <div className="flex-1 px-6 py-4 overflow-auto bg-cream">
              <pre className="font-mono text-[13px] leading-relaxed text-[#e8e8e8] whitespace-pre-wrap wrap-break-word">{compareResult}</pre>
            </div>
          )}
        </div>
      )}

      {/* Status Bar */}
      <footer className="flex items-center justify-between px-6 py-2 bg-cream border-t border-slate text-xs text-silver">
        <div className="flex gap-6">
          {isLoadingStatus ? (
            <span>Loading status...</span>
          ) : status ? (
            <>
              <span>Collection: <strong className="text-silver font-medium">{status.collection_name}</strong></span>
              <span>Documents: <strong className="text-silver font-medium">{status.document_count.toLocaleString()}</strong></span>
              <span>Router: <strong className="text-silver font-medium">{status.router_model}</strong></span>
            </>
          ) : statusError ? (
            <span className="text-error">⚠ {statusError}</span>
          ) : (
            <span>Connecting to API...</span>
          )}
        </div>
        <div className="text-gold font-semibold tracking-wide">HECTOR v9.0.0</div>
      </footer>
    </div>
  )
}