"use client";

import { useState } from "react";
import { ArrowRight, BookOpen, Search } from "lucide-react";

export default function ComparisonView({
  onCompare,
  compareData,
  compareLoading,
  compareError,
}) {
  const [section, setSection] = useState("");
  const [act, setAct] = useState("IPC");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (section.trim()) {
      onCompare(section.trim(), act);
    }
  };

  return (
    <div className="flex flex-col items-center py-12 px-4">
      <div className="mb-8 text-center animate-fade-in">
        <img src="/tab-icon.png" alt="HECTOR" className="mx-auto mb-4 h-14 w-14 rounded-xl" />
        <h2 className="font-serif text-2xl font-semibold text-gold-light">
          IPC &harr; BNS Comparison
        </h2>
        <p className="mt-2 text-[13px] text-silver/50">
          Enter a section number to compare across acts
        </p>
      </div>

      <form onSubmit={handleSubmit} className="w-full max-w-md animate-fade-in-delay-1" role="search" aria-label="Section comparison">
        <div className="flex gap-2 mb-4">
          <select
            value={act}
            onChange={(e) => setAct(e.target.value)}
            aria-label="Select act to compare"
            className="rounded-lg border border-slate-custom/60 bg-charcoal/80 px-3 py-2.5 text-[13px] text-gold-light outline-none focus:border-gold/40"
          >
            <option value="IPC">IPC</option>
            <option value="BNS">BNS</option>
          </select>
          <input
            type="text"
            value={section}
            onChange={(e) => setSection(e.target.value)}
            placeholder="e.g., 302"
            aria-label="Section number to compare"
            className="flex-1 rounded-lg border border-slate-custom/60 bg-charcoal/80 px-4 py-2.5 text-[14px] text-gold-light placeholder-silver/40 outline-none focus:border-gold/40"
          />
          <button
            type="submit"
            disabled={!section.trim() || compareLoading}
            aria-label="Compare sections"
            className="flex h-10 w-10 items-center justify-center rounded-lg bg-gold/90 text-charcoal transition-all hover:bg-gold disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <Search size={16} />
          </button>
        </div>
      </form>

      {compareError && (
        <div className="mb-4 w-full max-w-md rounded-lg border border-error/25 bg-error/10 px-4 py-3 text-[13px] text-red-200">
          {compareError}
        </div>
      )}

      {compareLoading && (
        <div className="py-8 text-[13px] text-silver/50 animate-pulse">
          Comparing sections...
        </div>
      )}

      {compareData && !compareLoading && (
        <div className="w-full max-w-2xl mt-6 animate-fade-in">
          <div className="mb-4 flex items-center gap-3 text-[13px]">
            <span className="rounded-md border border-gold/20 bg-gold/5 px-2.5 py-1 font-medium text-gold">
              {compareData.requestedAct} &sect;{compareData.requestedSection}
            </span>
            <ArrowRight size={14} className="text-silver/40" />
            <span className="rounded-md border border-info/20 bg-info/5 px-2.5 py-1 font-medium text-info">
              {compareData.counterpartAct || "\u2014"} &sect;{compareData.counterpartSection || "\u2014"}
            </span>
          </div>

          {compareData.note && (
            <p className="mb-4 text-[12px] text-silver/50 italic">{compareData.note}</p>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            {/* Requested Results */}
            <div className="rounded-lg border border-slate-custom/30 bg-charcoal/40 p-4">
              <h3 className="mb-3 flex items-center gap-2 text-[13px] font-semibold text-gold-light">
                <BookOpen size={14} />
                {compareData.requestedAct} Results
              </h3>
              {compareData.requestedResults.length === 0 ? (
                <p className="text-[12px] text-silver/40">No results found</p>
              ) : (
                <div className="space-y-2">
                  {compareData.requestedResults.map((source) => (
                    <div
                      key={source.id}
                      className="rounded border border-slate-custom/20 bg-cream/30 p-2.5"
                    >
                      <p className="text-[11px] font-medium text-silver/70">
                        {source.bookTitle}
                      </p>
                      <p className="mt-1 line-clamp-3 text-[11.5px] leading-relaxed text-silver/50">
                        &ldquo;{source.matchedText}&rdquo;
                      </p>
                      <div className="mt-1.5 flex items-center gap-2 text-[10px] text-silver/35">
                        <span>{source.section}</span>
                        {source.page && <span>Page {source.page}</span>}
                        <span className="rounded bg-success/8 px-1 py-0.5 text-success">
                          {Math.round(source.relevanceScore * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Counterpart Results */}
            <div className="rounded-lg border border-slate-custom/30 bg-charcoal/40 p-4">
              <h3 className="mb-3 flex items-center gap-2 text-[13px] font-semibold text-info">
                <BookOpen size={14} />
                {compareData.counterpartAct || "Counterpart"} Results
              </h3>
              {compareData.counterpartResults.length === 0 ? (
                <p className="text-[12px] text-silver/40">No results found</p>
              ) : (
                <div className="space-y-2">
                  {compareData.counterpartResults.map((source) => (
                    <div
                      key={source.id}
                      className="rounded border border-slate-custom/20 bg-cream/30 p-2.5"
                    >
                      <p className="text-[11px] font-medium text-silver/70">
                        {source.bookTitle}
                      </p>
                      <p className="mt-1 line-clamp-3 text-[11.5px] leading-relaxed text-silver/50">
                        &ldquo;{source.matchedText}&rdquo;
                      </p>
                      <div className="mt-1.5 flex items-center gap-2 text-[10px] text-silver/35">
                        <span>{source.section}</span>
                        {source.page && <span>Page {source.page}</span>}
                        <span className="rounded bg-success/8 px-1 py-0.5 text-success">
                          {Math.round(source.relevanceScore * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
