"use client";

import { useRef, useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import WelcomeScreen from "@/components/WelcomeScreen";
import ProcessingIndicator from "@/components/ProcessingIndicator";
import ResponseDisplay from "@/components/ResponseDisplay";
import { SearchSkeleton } from "@/components/Skeleton";
import { useApp } from "@/components/appContext";

export default function SearchPage() {
  const {
    appState,
    currentResponse,
    activeSourceId,
    processingStage,
    submittedQuery,
    error,
    bookmarks,
    handleSubmit,
    handleSourceClick,
    handleToggleBookmark,
  } = useApp();

  const responseRef = useRef(null);

  // Auto-scroll response into view
  useEffect(() => {
    if (appState === "responded" && responseRef.current) {
      responseRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [appState]);

  return (
    <>
      {appState === "idle" && (
        <>
          {error && (
            <div className="mb-4 rounded-lg border border-error/25 bg-error/10 px-4 py-3 animate-fade-in">
              <div className="flex items-start gap-3">
                <AlertTriangle size={16} className="mt-0.5 shrink-0 text-error" />
                <div className="flex-1">
                  <p className="text-[13px] leading-relaxed text-red-200">{error}</p>
                  <button
                    onClick={() => submittedQuery && handleSubmit(submittedQuery)}
                    className="mt-2 flex items-center gap-1.5 text-[12px] font-medium text-gold transition-colors hover:text-gold-light"
                  >
                    <RefreshCw size={12} />
                    Retry query
                  </button>
                </div>
              </div>
            </div>
          )}
          <WelcomeScreen />
        </>
      )}

      {appState === "processing" && (
        <div className="py-8">
          {/* Show the query */}
          <div className="mb-6 animate-fade-in">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-silver/55 mb-2">
              Your Query
            </p>
            <div className="rounded-lg border border-slate-custom/30 bg-charcoal/30 px-4 py-3">
              <p className="font-serif text-[15px] text-gold-light leading-relaxed">
                {submittedQuery}
              </p>
            </div>
          </div>
          <ProcessingIndicator currentStage={processingStage} />
          <div className="mt-6 opacity-40">
            <SearchSkeleton />
          </div>
        </div>
      )}

      {appState === "responded" && currentResponse && (
        <div className="py-4">
          {/* Query echo */}
          <div className="mb-5 animate-fade-in">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-silver/55 mb-2">
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
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-silver/55 mb-3">
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
    </>
  );
}
