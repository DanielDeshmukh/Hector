import { useState, useCallback, useRef, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import QueryInput from "./components/QueryInput";
import ResponseDisplay from "./components/ResponseDisplay";
import DocumentPanel from "./components/DocumentPanel";
import WelcomeScreen from "./components/WelcomeScreen";
import ProcessingIndicator from "./components/ProcessingIndicator";
import ComparisonView from "./components/ComparisonView";
import { searchHector, compareHector, getStatusHector } from "./api/hectorApi";
import { useLanguage } from "./i18n/LanguageContext";

const HISTORY_STORAGE_KEY = "hector.searchHistory";
const BOOKMARKS_STORAGE_KEY = "hector.bookmarks";
const MAX_HISTORY_ITEMS = 8;
const MAX_BOOKMARK_ITEMS = 20;
const TOP_SEARCH_QUERIES = [
  "What is the BNS equivalent of IPC Section 302?",
  "Compare the punishment for theft under IPC and BNS",
  "What changes were made to sedition laws in BNS?",
  "Explain Section 356 BNS and its IPC counterpart",
];

function loadSearchHistory() {
  try {
    return JSON.parse(window.localStorage.getItem(HISTORY_STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function loadBookmarks() {
  try {
    return JSON.parse(window.localStorage.getItem(BOOKMARKS_STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function normalizeHistoryDomain(domain) {
  if (domain === "LEGAL_RESEARCH") return "Legal Research";
  return domain || "Search";
}

function buildQuerySuggestions(history, response) {
  const relatedProvisionSuggestions =
    response?.raw?.related_provisions?.map((provision) => `Explain ${provision}`) || [];
  const recentQuerySuggestions = history.map((item) => item.query);

  return [
    ...new Set([
      ...relatedProvisionSuggestions,
      ...recentQuerySuggestions,
      ...TOP_SEARCH_QUERIES,
    ]),
  ].slice(0, 4);
}

export default function App() {
  const { lang, toggleLang, t } = useLanguage();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [appState, setAppState] = useState("idle");
  const [currentResponse, setCurrentResponse] = useState(null);
  const [activeSourceId, setActiveSourceId] = useState(null);
  const [activeSource, setActiveSource] = useState(null);
  const [processingStage, setProcessingStage] = useState(0);
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [error, setError] = useState("");
  const [searchHistory, setSearchHistory] = useState(loadSearchHistory);
  const [bookmarks, setBookmarks] = useState(loadBookmarks);
  const [systemStatus, setSystemStatus] = useState(null);
  const [compareMode, setCompareMode] = useState(false);
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState("");
  const responseRef = useRef(null);
  const querySuggestions = buildQuerySuggestions(searchHistory, currentResponse);

  const startProcessingAnimation = useCallback(() => {
    setAppState("processing");
    setProcessingStage(0);

    const intervalId = window.setInterval(() => {
      setProcessingStage((stage) => (stage >= 3 ? 3 : stage + 1));
    }, 900);

    return () => window.clearInterval(intervalId);
  }, []);

  const handleSubmit = useCallback(
    async (query) => {
      setSubmittedQuery(query);
      setActiveSourceId(null);
      setActiveSource(null);
      setCurrentResponse(null);
      setError("");

      const stopProcessingAnimation = startProcessingAnimation();
      try {
        const response = await searchHector(query);
        setProcessingStage(4);
        setCurrentResponse(response);
        setSearchHistory((history) => {
          const normalizedQuery = query.trim();
          const nextItem = {
            id: `${Date.now()}-${normalizedQuery}`,
            query: normalizedQuery,
            timestamp: response.timestamp || new Date().toISOString(),
            domain: normalizeHistoryDomain(response.domain),
          };
          return [
            nextItem,
            ...history.filter(
              (item) => item.query.toLowerCase() !== normalizedQuery.toLowerCase()
            ),
          ].slice(0, MAX_HISTORY_ITEMS);
        });
        setAppState("responded");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to reach HECTOR.");
        setAppState("idle");
      } finally {
        stopProcessingAnimation();
      }
    },
    [startProcessingAnimation]
  );

  const handleNewQuery = useCallback(() => {
    setAppState("idle");
    setCurrentResponse(null);
    setActiveSourceId(null);
    setActiveSource(null);
    setSubmittedQuery("");
    setError("");
  }, []);

  useEffect(() => {
    window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(searchHistory));
  }, [searchHistory]);

  useEffect(() => {
    window.localStorage.setItem(BOOKMARKS_STORAGE_KEY, JSON.stringify(bookmarks));
  }, [bookmarks]);

  const handleToggleBookmark = useCallback(
    (source) => {
      setBookmarks((prev) => {
        const exists = prev.find((b) => b.id === source.id);
        if (exists) {
          return prev.filter((b) => b.id !== source.id);
        }
        const bookmark = {
          id: source.id,
          query: submittedQuery,
          bookTitle: source.bookTitle,
          section: source.section,
          act: source.act,
          matchedText: source.matchedText,
          page: source.page,
          relevanceScore: source.relevanceScore,
          timestamp: new Date().toISOString(),
        };
        return [bookmark, ...prev].slice(0, MAX_BOOKMARK_ITEMS);
      });
    },
    [submittedQuery]
  );

  const handleRemoveBookmark = useCallback((bookmarkId) => {
    setBookmarks((prev) => prev.filter((b) => b.id !== bookmarkId));
  }, []);

  const handleSourceClick = useCallback(
    (sourceId) => {
      if (activeSourceId === sourceId) {
        setActiveSourceId(null);
        setActiveSource(null);
      } else {
        setActiveSourceId(sourceId);
        const source = currentResponse?.sources.find((s) => s.id === sourceId);
        if (source) setActiveSource(source);
      }
    },
    [activeSourceId, currentResponse]
  );

  const handleSelectHistory = useCallback(
    (query) => {
      handleSubmit(query);
    },
    [handleSubmit]
  );

  const handleCompare = useCallback(async (section, act) => {
    setCompareLoading(true);
    setCompareError("");
    setCompareData(null);
    try {
      const data = await compareHector(section, act);
      setCompareData(data);
    } catch (err) {
      setCompareError(err instanceof Error ? err.message : "Comparison failed.");
    } finally {
      setCompareLoading(false);
    }
  }, []);

  const handleToggleCompare = useCallback(() => {
    setCompareMode((prev) => !prev);
    setCompareData(null);
    setCompareError("");
  }, []);

  // Fetch system status on mount
  useEffect(() => {
    getStatusHector()
      .then(setSystemStatus)
      .catch(() => setSystemStatus(null));
  }, []);

  // Auto-scroll response into view
  useEffect(() => {
    if (appState === "responded" && responseRef.current) {
      responseRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [appState]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-cream">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        onNewQuery={handleNewQuery}
        onSelectHistory={handleSelectHistory}
        history={searchHistory}
        bookmarks={bookmarks}
        onRemoveBookmark={handleRemoveBookmark}
        systemStatus={systemStatus}
      />

      {/* Main Area */}
      <div className="flex flex-1 min-w-0">
        {/* Center Content */}
        <main
          className={`flex flex-1 flex-col min-w-0 transition-all duration-300 ${
            activeSource ? "max-w-[calc(100%-420px)]" : ""
          }`}
        >
          {/* Top Bar */}
          <header className="flex items-center justify-between border-b border-slate-custom/30 bg-cream/90 px-6 py-2.5 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              {appState === "responded" && (
                <div className="flex items-center gap-2 animate-fade-in">
                  <span className="h-1.5 w-1.5 rounded-full bg-success"></span>
                  <span className="text-[11px] font-medium text-silver/50">
                    Query Resolved
                  </span>
                </div>
              )}
              {appState === "processing" && (
                <div className="flex items-center gap-2 animate-fade-in">
                  <span className="h-1.5 w-1.5 rounded-full bg-gold animate-pulse"></span>
                  <span className="text-[11px] font-medium text-gold/60">
                    Processing...
                  </span>
                </div>
              )}
              {appState === "idle" && (
                <span className="text-[11px] text-silver/30">
                  Ready for queries
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-[10px] text-silver/25">
              <button
                onClick={toggleLang}
                className="rounded-md px-2 py-1 transition-colors hover:bg-slate-custom/30 hover:text-silver font-medium"
              >
                {lang === "en" ? "\u0939\u093f\u0928\u094d\u0926\u0940" : "English"}
              </button>
              <span className="text-slate-custom">|</span>
              <button
                onClick={handleToggleCompare}
                className={`rounded-md px-2 py-1 transition-colors ${
                  compareMode
                    ? "bg-gold/15 text-gold border border-gold/30"
                    : "hover:bg-slate-custom/30 hover:text-silver"
                }`}
              >
                {compareMode ? t("header.compareMode") : t("header.searchMode")}
              </button>
              <span className="text-slate-custom">|</span>
              <span>CoVe Architecture</span>
              <span className="text-slate-custom">-</span>
              <span>Hard-RAG Pipeline</span>
            </div>
          </header>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto">
            <div className="mx-auto max-w-3xl px-6 py-6">
              {/* Idle State */}
              {appState === "idle" && !compareMode && (
                <>
                  {error && (
                    <div className="mb-4 rounded-lg border border-error/25 bg-error/10 px-4 py-3 text-[13px] leading-relaxed text-red-200">
                      {error}
                    </div>
                  )}
                  <WelcomeScreen />
                </>
              )}

              {/* Compare Mode */}
              {appState === "idle" && compareMode && (
                <ComparisonView
                  onCompare={handleCompare}
                  compareData={compareData}
                  compareLoading={compareLoading}
                  compareError={compareError}
                />
              )}

              {/* Processing State */}
              {appState === "processing" && (
                <div className="py-8">
                  {/* Show the query */}
                  <div className="mb-6 animate-fade-in">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-silver/40 mb-2">
                      Your Query
                    </p>
                    <div className="rounded-lg border border-slate-custom/30 bg-charcoal/30 px-4 py-3">
                      <p className="font-serif text-[15px] text-gold-light leading-relaxed">
                        {submittedQuery}
                      </p>
                    </div>
                  </div>
                  <ProcessingIndicator currentStage={processingStage} />
                </div>
              )}

              {/* Response State */}
              {appState === "responded" && currentResponse && (
                <div className="py-4">
                  {/* Query echo */}
                  <div className="mb-5 animate-fade-in">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-silver/40 mb-2">
                      Query
                    </p>
                    <div className="rounded-lg border border-slate-custom/30 bg-charcoal/30 px-4 py-3">
                      <p className="font-serif text-[15px] text-gold-light leading-relaxed">
                        {submittedQuery}
                      </p>
                    </div>
                  </div>

                  {/* Response */}
                  <div ref={responseRef}>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-silver/40 mb-3">
                      Response
                    </p>
                    <ResponseDisplay
                      response={currentResponse}
                      onSourceClick={handleSourceClick}
                      activeSourceId={activeSourceId}
                      bookmarks={bookmarks}
                      onToggleBookmark={handleToggleBookmark}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Bottom spacer for input */}
            <div className="h-32" />
          </div>

          {/* Fixed Input at Bottom */}
          <div className="border-t border-slate-custom/20 bg-cream/95 backdrop-blur-md px-6 py-4">
            <div className="mx-auto max-w-3xl">
              <QueryInput
                onSubmit={handleSubmit}
                isLoading={appState === "processing"}
                showSuggestions={appState === "idle"}
                suggestions={querySuggestions}
              />
            </div>
          </div>
        </main>

        {/* Document Reference Panel */}
        {activeSource && (
          <div className="w-[420px] shrink-0 overflow-hidden">
            <DocumentPanel
              source={activeSource}
              onClose={() => {
                setActiveSourceId(null);
                setActiveSource(null);
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
