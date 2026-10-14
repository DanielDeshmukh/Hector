"use client";

import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Menu, Layers } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import QueryInput from "@/components/QueryInput";
import DocumentPanel from "@/components/DocumentPanel";
import BatchQueryPanel from "@/components/BatchQueryPanel";
import { searchHector, compareHector, getStatusHector } from "@/api/hectorApi";
import { LanguageProvider, useLanguage } from "@/i18n/LanguageContext";
import { AppContext } from "@/components/appContext";

const HISTORY_STORAGE_KEY = "hector.searchHistory";
const BOOKMARKS_STORAGE_KEY = "hector.bookmarks";
const SIDEBAR_STATE_KEY = "hector.sidebarCollapsed";
const MAX_HISTORY_ITEMS = 8;
const MAX_BOOKMARK_ITEMS = 20;
const COMPARE_PATH = "/compare";
const SEARCH_PATH = "/search";
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

function loadSidebarState() {
  try {
    return window.localStorage.getItem(SIDEBAR_STATE_KEY) === "true";
  } catch {
    return false;
  }
}

function normalizePath(pathname) {
  if (!pathname) return SEARCH_PATH;
  const trimmed = pathname.replace(/\/+$/, "");
  return trimmed === "" ? SEARCH_PATH : trimmed;
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

function AppShellInner({ children }) {
  const { lang, toggleLang, t } = useLanguage();
  const router = useRouter();
  const pathname = normalizePath(usePathname());
  const isCompare = pathname === COMPARE_PATH;

  const [sidebarCollapsed, setSidebarCollapsed] = useState(loadSidebarState);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [batchPanelOpen, setBatchPanelOpen] = useState(false);
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
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState("");
  const [inputResetKey, setInputResetKey] = useState(0);

  // Request tokens: the latest id wins. Older in-flight responses are dropped
  // instead of clobbering newer state.
  const searchReqRef = useRef(0);
  const searchInFlightRef = useRef(false);
  const compareReqRef = useRef(0);

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
    async (query, file = null) => {
      // Guard against the sidebar history path, which bypasses QueryInput's
      // own isLoading check and would otherwise double-fetch.
      if (searchInFlightRef.current) return;

      // A search submitted from the compare route belongs on the search route.
      if (pathname !== SEARCH_PATH) router.push(SEARCH_PATH);

      searchInFlightRef.current = true;
      const reqId = ++searchReqRef.current;

      setSubmittedQuery(query);
      setActiveSourceId(null);
      setActiveSource(null);
      setCurrentResponse(null);
      setError("");

      const stopProcessingAnimation = startProcessingAnimation();
      try {
        const response = await searchHector(query, file);
        if (reqId !== searchReqRef.current) return;
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
        if (reqId !== searchReqRef.current) return;
        setError(err instanceof Error ? err.message : "Unable to reach HECTOR.");
        setAppState("idle");
      } finally {
        stopProcessingAnimation();
        if (reqId === searchReqRef.current) searchInFlightRef.current = false;
      }
    },
    [pathname, router, startProcessingAnimation]
  );

  const handleNewQuery = useCallback(() => {
    // Invalidate any in-flight search so a late response cannot resurrect
    // state the user just cleared, and release the in-flight lock.
    searchReqRef.current += 1;
    searchInFlightRef.current = false;
    if (pathname !== SEARCH_PATH) router.push(SEARCH_PATH);
    setAppState("idle");
    setCurrentResponse(null);
    setActiveSourceId(null);
    setActiveSource(null);
    setSubmittedQuery("");
    setError("");
    setInputResetKey((k) => k + 1);
  }, [pathname, router]);

  useEffect(() => {
    window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(searchHistory));
  }, [searchHistory]);

  useEffect(() => {
    window.localStorage.setItem(BOOKMARKS_STORAGE_KEY, JSON.stringify(bookmarks));
  }, [bookmarks]);

  useEffect(() => {
    window.localStorage.setItem(SIDEBAR_STATE_KEY, String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  // Close mobile menu when viewport expands to desktop
  useEffect(() => {
    const mql = window.matchMedia("(min-width: 768px)");
    const handler = (e) => {
      if (e.matches) setMobileMenuOpen(false);
    };
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

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
    const reqId = ++compareReqRef.current;
    setCompareLoading(true);
    setCompareError("");
    setCompareData(null);
    try {
      const data = await compareHector(section, act);
      if (reqId !== compareReqRef.current) return;
      setCompareData(data);
    } catch (err) {
      if (reqId !== compareReqRef.current) return;
      setCompareError(err instanceof Error ? err.message : "Comparison failed.");
    } finally {
      if (reqId === compareReqRef.current) setCompareLoading(false);
    }
  }, []);

  const handleToggleMode = useCallback(() => {
    router.push(isCompare ? SEARCH_PATH : COMPARE_PATH);
  }, [isCompare, router]);

  // Fetch system status on mount, then keep it fresh (db_source indicator)
  useEffect(() => {
    let cancelled = false;
    const fetchStatus = () =>
      getStatusHector()
        .then((s) => {
          if (!cancelled) setSystemStatus(s);
        })
        .catch(() => {
          if (!cancelled) setSystemStatus(null);
        });
    fetchStatus();
    const timer = setInterval(fetchStatus, 30000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const contextValue = useMemo(
    () => ({
      appState,
      currentResponse,
      activeSourceId,
      activeSource,
      processingStage,
      submittedQuery,
      error,
      searchHistory,
      bookmarks,
      systemStatus,
      querySuggestions,
      isCompare,
      isLoading: appState === "processing",
      handleSubmit,
      handleNewQuery,
      handleSelectHistory,
      handleSourceClick,
      handleToggleBookmark,
      handleRemoveBookmark,
      compareData,
      compareLoading,
      compareError,
      handleCompare,
    }),
    [
      appState,
      currentResponse,
      activeSourceId,
      activeSource,
      processingStage,
      submittedQuery,
      error,
      searchHistory,
      bookmarks,
      systemStatus,
      querySuggestions,
      isCompare,
      handleSubmit,
      handleNewQuery,
      handleSelectHistory,
      handleSourceClick,
      handleToggleBookmark,
      handleRemoveBookmark,
      compareData,
      compareLoading,
      compareError,
      handleCompare,
    ]
  );

  return (
    <AppContext.Provider value={contextValue}>
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
          mobileOpen={mobileMenuOpen}
          onMobileClose={() => setMobileMenuOpen(false)}
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
            <header className="flex items-center justify-between border-b border-slate-custom/30 bg-cream/90 px-4 md:px-6 py-2.5 backdrop-blur-sm">
              <div className="flex items-center gap-3">
                {/* Mobile hamburger */}
                <button
                  onClick={() => setMobileMenuOpen(true)}
                  className="md:hidden flex h-8 w-8 items-center justify-center rounded-lg text-silver/60 hover:bg-slate-custom/30 hover:text-silver"
                  aria-label="Open menu"
                >
                  <Menu size={18} />
                </button>
                {!isCompare && appState === "responded" && (
                  <div className="flex items-center gap-2 animate-fade-in">
                    <span className="h-1.5 w-1.5 rounded-full bg-success"></span>
                    <span className="text-[11px] font-medium text-silver/50">
                      {t("header.resolved")}
                    </span>
                  </div>
                )}
                {!isCompare && appState === "processing" && (
                  <div className="flex items-center gap-2 animate-fade-in">
                    <span className="h-1.5 w-1.5 rounded-full bg-gold animate-pulse"></span>
                    <span className="text-[11px] font-medium text-gold/60">
                      {t("header.processing")}
                    </span>
                  </div>
                )}
                {!isCompare && appState === "idle" && (
                  <span className="text-[11px] text-silver/45">
                    {t("header.ready")}
                  </span>
                )}
                {isCompare && (
                  <span className="text-[11px] text-silver/45">
                    {t("header.compareStatus")}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 text-[10px] text-silver/45">
                <button
                  onClick={() => setBatchPanelOpen(true)}
                  className="hidden md:flex items-center gap-1 rounded-md px-2 py-1 transition-colors hover:bg-slate-custom/30 hover:text-silver font-medium"
                  title="Batch Query"
                >
                  <Layers size={12} />
                  <span>Batch</span>
                </button>
                <span className="hidden md:inline text-slate-custom">|</span>
                <button
                  onClick={toggleLang}
                  className="rounded-md px-2 py-1 transition-colors hover:bg-slate-custom/30 hover:text-silver font-medium"
                >
                  {lang === "en" ? "\u0939\u093f\u0928\u094d\u0926\u0940" : "English"}
                </button>
                <span className="text-slate-custom">|</span>
                <button
                  onClick={handleToggleMode}
                  aria-current={isCompare ? "page" : undefined}
                  className={`rounded-md px-2 py-1 transition-colors ${
                    isCompare
                      ? "bg-gold/15 text-gold border border-gold/30"
                      : "hover:bg-slate-custom/30 hover:text-silver"
                  }`}
                >
                  {isCompare ? t("header.toSearch") : t("header.toCompare")}
                </button>
                <span className="text-slate-custom">|</span>
                <span>CoVe Architecture</span>
                <span className="text-slate-custom">-</span>
                <span>Hard-RAG Pipeline</span>
              </div>
            </header>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto">
              <div className="mx-auto flex min-h-full max-w-3xl flex-col px-4 md:px-6 py-4 md:py-6">
                {children}
              </div>
            </div>

            {/* Fixed Input at Bottom */}
            <div className="border-t border-slate-custom/20 bg-cream/95 backdrop-blur-md px-4 md:px-6 py-3 md:py-4">
              <div className="mx-auto max-w-3xl">
                <QueryInput
                  key={inputResetKey}
                  onSubmit={handleSubmit}
                  isLoading={appState === "processing"}
                  showSuggestions={appState === "idle" && !isCompare}
                  suggestions={querySuggestions}
                />
              </div>
            </div>
          </main>

          {/* Document Reference Panel */}
          {activeSource && (
            <div className="fixed inset-0 z-50 md:relative md:z-auto w-full md:w-[420px] shrink-0 overflow-hidden bg-cream md:bg-transparent">
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

        {/* Batch Query Panel */}
        {batchPanelOpen && (
          <BatchQueryPanel onClose={() => setBatchPanelOpen(false)} />
        )}
      </div>
    </AppContext.Provider>
  );
}

export default function AppShell({ children }) {
  return (
    <LanguageProvider>
      <AppShellInner>{children}</AppShellInner>
    </LanguageProvider>
  );
}
