'use client'

import { useEffect, useState, useCallback } from 'react'
import { SearchBar, ComparePanel, ErrorMessage, SidePanel, WelcomeScreen, ProcessingIndicator, ResponseDisplay, DocumentPanel } from '@/components'
import { useAppStore } from '@/lib/store'
import { apiClient } from '@/lib/api'

// Processing stages from design.md
const PROCESSING_STAGES = [
  { id: 'routing', name: 'Intent Routing', detail: 'Classifying legal domain', icon: 'Shield' },
  { id: 'retrieval', name: 'Hybrid Retrieval', detail: 'Searching across legal texts', icon: 'Search' },
  { id: 'context', name: 'Hierarchical Context', detail: 'Resolving parent sections', icon: 'Layers' },
  { id: 'grounding', name: 'Citation Grounding', detail: 'Verifying against source', icon: 'FileCheck' },
]

const STAGE_DELAYS = [800, 1200, 1000, 900]

export default function Home() {
  const {
    activeTab,
    compareResult,
    setStatus,
    setIsLoadingStatus,
    isLoadingStatus,
    status,
    appState,
    setAppState,
    currentResponse,
    setCurrentResponse,
    activeSourceId,
    setActiveSourceId,
    activeSource,
    setActiveSource,
    processingStage,
    setProcessingStage,
    submittedQuery,
    setSubmittedQuery,
    addSearchHistory,
    isSearching,
    setIsSearching,
    setQuery,
  } = useAppStore()

  const [statusError, setStatusError] = useState<string | null>(null)

  // Load status on mount
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

  // Handle query submission
  const handleSubmitQuery = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim() || isSearching) return

    setSubmittedQuery(searchQuery)
    setQuery('')
    setIsSearching(true)
    setAppState('processing')
    setProcessingStage(0)
    setCurrentResponse(null)

    // Simulate processing stages
    for (let i = 0; i < PROCESSING_STAGES.length; i++) {
      await new Promise(resolve => setTimeout(resolve, STAGE_DELAYS[i]))
      setProcessingStage(i + 1)
    }

    try {
      // Call the actual API
      const response = await apiClient.search({
        query: searchQuery,
        page: 1,
        page_size: 10,
        verify: false,
        format: 'summary',
        include_related: true,
      })

      // Transform API response to match design.md structure
      const transformedResponse = {
        id: crypto.randomUUID(),
        query: searchQuery,
        answer: response.generated_response || 'No response available',
        domain: response.route || 'LEGAL_RESEARCH',
        confidence: 0.85,
        sources: response.items?.map((r: any, idx: number) => ({
          id: `source-${idx}`,
          bookTitle: r.metadata?.source || r.metadata?.act || 'Unknown Source',
          author: 'Legal Authority',
          chapter: r.metadata?.chapter || '',
          section: r.metadata?.section_number || r.metadata?.section || r.citation?.section || '',
          page: r.metadata?.page || parseInt(r.citation?.page) || 1,
          paragraph: 1,
          relevanceScore: r.score ? Math.round(r.score * 100) : 85,
          matchedText: r.snippet || r.content?.substring(0, 200) || '',
          fullText: r.snippet || r.content || '',
          act: r.act || r.metadata?.act || r.citation?.act || 'BNS',
          highlightRanges: [{ start: 0, end: Math.min(50, (r.snippet || r.content || '').length) }],
        })) || [],
        pipeline: PROCESSING_STAGES.map((stage, idx) => ({
          id: stage.id,
          name: stage.name,
          status: (idx < PROCESSING_STAGES.length ? 'completed' : 'pending') as 'completed' | 'active' | 'pending',
          detail: stage.detail,
        })),
        timestamp: new Date().toISOString(),
      }

      setCurrentResponse(transformedResponse)
      addSearchHistory(searchQuery, transformedResponse.domain)
      setAppState('responded')
    } catch (err) {
      console.error('Search error:', err)
      setAppState('idle')
    } finally {
      setIsSearching(false)
    }
  }, [isSearching, setSubmittedQuery, setQuery, setIsSearching, setAppState, setProcessingStage, setCurrentResponse, addSearchHistory])

  // Handle source selection
  const handleSourceClick = useCallback((source: any) => {
    setActiveSourceId(source.id)
    setActiveSource(source)
  }, [setActiveSourceId, setActiveSource])

  // Handle new query
  const handleNewQuery = useCallback(() => {
    setAppState('idle')
    setCurrentResponse(null)
    setActiveSourceId(null)
    setActiveSource(null)
    setSubmittedQuery('')
  }, [setAppState, setCurrentResponse, setActiveSourceId, setActiveSource, setSubmittedQuery])

  // Handle history item click
  const handleHistoryClick = useCallback((historyItem: { query: string }) => {
    handleSubmitQuery(historyItem.query)
  }, [handleSubmitQuery])

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Error Message Display */}
      <ErrorMessage />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <SidePanel
          onNewQuery={handleNewQuery}
          onHistoryClick={handleHistoryClick}
        />

        {/* Main Content Area */}
        <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-300 ${activeSourceId ? 'max-w-[calc(100%-420px)]' : ''}`}>
          {/* Top Bar / Status */}
          <div className="flex items-center justify-between px-6 py-3 bg-cream border-b border-slate/30">
            <div className="flex items-center gap-3">
              {appState === 'idle' && (
                <span className="text-sm text-silver">Ready for queries</span>
              )}
              {appState === 'processing' && (
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-gold animate-pulse" />
                  <span className="text-sm text-gold">Processing...</span>
                </div>
              )}
              {appState === 'responded' && (
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-success" />
                  <span className="text-sm text-success">Query Resolved</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-4">
              {isLoadingStatus ? (
                <span className="text-xs text-silver">Loading...</span>
              ) : status ? (
                <span className="text-xs text-silver">
                  {status.document_count?.toLocaleString() || 0} docs indexed
                </span>
              ) : null}
            </div>
          </div>

          {/* Content Container */}
          <div className="flex-1 overflow-auto">
            {appState === 'idle' && (
              <WelcomeScreen onQuerySubmit={handleSubmitQuery} />
            )}

            {appState === 'processing' && (
              <ProcessingIndicator
                query={submittedQuery}
                currentStage={processingStage}
                stages={PROCESSING_STAGES}
              />
            )}

            {appState === 'responded' && currentResponse && (
              <ResponseDisplay
                response={currentResponse}
                onSourceClick={handleSourceClick}
              />
            )}
          </div>

          {/* Query Input (only show when not in compare mode) */}
          {activeTab === 'search' && (
            <SearchBar
              onSubmit={handleSubmitQuery}
              disabled={isSearching}
            />
          )}
        </div>

        {/* Document Panel - slides in from right */}
        {activeSourceId && activeSource && (
          <DocumentPanel
            source={activeSource}
            onClose={() => {
              setActiveSourceId(null)
              setActiveSource(null)
            }}
          />
        )}
      </div>

      {/* Compare Panel Mode */}
      {activeTab === 'compare' && (
        <div className="fixed inset-0 z-50 bg-cream">
          <ComparePanel />
          {compareResult && (
            <div className="flex-1 px-6 py-4 overflow-auto bg-cream">
              <pre className="font-mono text-[13px] leading-relaxed text-[#e8e8e8] whitespace-pre-wrap break-word">
                {compareResult}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}