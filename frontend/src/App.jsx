import { useState, useCallback, useRef, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import QueryInput from "./components/QueryInput";
import ResponseDisplay from "./components/ResponseDisplay";
import DocumentPanel from "./components/DocumentPanel";
import WelcomeScreen from "./components/WelcomeScreen";
import ProcessingIndicator from "./components/ProcessingIndicator";
import { mockResponse } from "./data/mockData";

export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [appState, setAppState] = useState("idle");
  const [currentResponse, setCurrentResponse] = useState(null);
  const [activeSourceId, setActiveSourceId] = useState(null);
  const [activeSource, setActiveSource] = useState(null);
  const [processingStage, setProcessingStage] = useState(0);
  const [submittedQuery, setSubmittedQuery] = useState("");
  const responseRef = useRef(null);

  const simulateProcessing = useCallback(() => {
    setAppState("processing");
    setProcessingStage(0);

    const stageDelays = [800, 1200, 1000, 900];
    let elapsed = 0;

    stageDelays.forEach((delay, index) => {
      elapsed += delay;
      setTimeout(() => {
        setProcessingStage(index + 1);
      }, elapsed);
    });

    // After all stages complete, show response
    setTimeout(() => {
      setCurrentResponse(mockResponse);
      setAppState("responded");
    }, elapsed + 600);
  }, []);

  const handleSubmit = useCallback(
    (query) => {
      setSubmittedQuery(query);
      setActiveSourceId(null);
      setActiveSource(null);
      simulateProcessing();
    },
    [simulateProcessing]
  );

  const handleNewQuery = useCallback(() => {
    setAppState("idle");
    setCurrentResponse(null);
    setActiveSourceId(null);
    setActiveSource(null);
    setSubmittedQuery("");
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
      setSubmittedQuery(query);
      setActiveSourceId(null);
      setActiveSource(null);
      simulateProcessing();
    },
    [simulateProcessing]
  );

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
              <span>CoVe Architecture</span>
              <span className="text-slate-custom">-</span>
              <span>Hard-RAG Pipeline</span>
            </div>
          </header>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto">
            <div className="mx-auto max-w-3xl px-6 py-6">
              {/* Idle State */}
              {appState === "idle" && <WelcomeScreen />}

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
