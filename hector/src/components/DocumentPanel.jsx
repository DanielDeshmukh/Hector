"use client";

import { X, BookOpen, FileText, ChevronUp, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";

function formatLocation(source) {
  const parts = [];
  if (source.page) parts.push(`Page ${source.page}`);
  if (source.paragraph) parts.push(`para ${source.paragraph}`);
  return parts.join(", ");
}

function formatObjectEntries(value) {
  return Object.entries(value || {}).filter(([, entryValue]) => {
    return entryValue !== undefined && entryValue !== null && entryValue !== "";
  });
}

function renderHighlightedText(text, ranges) {
  if (!ranges.length) {
    return <span>{text}</span>;
  }

  const sortedRanges = [...ranges].sort((a, b) => a.start - b.start);
  const parts = [];
  let lastEnd = 0;

  sortedRanges.forEach((range, i) => {
    if (range.start > lastEnd) {
      parts.push(
        <span key={`text-${i}`} className="text-silver/70">
          {text.slice(lastEnd, range.start)}
        </span>
      );
    }
    parts.push(
      <mark
        key={`hl-${i}`}
        id={`highlight-${i}`}
        className="highlight-active rounded-sm bg-gold/15 px-0.5 text-gold-light border-l-2 border-gold/40"
      >
        {text.slice(range.start, range.end)}
      </mark>
    );
    lastEnd = range.end;
  });

  if (lastEnd < text.length) {
    parts.push(
      <span key="text-end" className="text-silver/70">
        {text.slice(lastEnd)}
      </span>
    );
  }

  return <>{parts}</>;
}

export default function DocumentPanel({ source, onClose }) {
  const [activeHighlight, setActiveHighlight] = useState(0);
  const containerRef = useRef(null);
  const highlightCount = source.highlightRanges.length;
  const location = formatLocation(source);
  const citationEntries = formatObjectEntries(source.citation);
  const metadataEntries = formatObjectEntries(source.metadata);

  useEffect(() => {
    if (!highlightCount) return;
    const el = document.getElementById(`highlight-${activeHighlight}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [activeHighlight, highlightCount, source.id]);

  const navigateHighlight = (direction) => {
    if (!highlightCount) return;
    if (direction === "up") {
      setActiveHighlight((prev) => (prev - 1 + highlightCount) % highlightCount);
    } else {
      setActiveHighlight((prev) => (prev + 1) % highlightCount);
    }
  };

  return (
    <div className="flex h-full flex-col bg-cream border-l border-slate-custom/40 animate-fade-in">
      <div className="flex items-start justify-between border-b border-slate-custom/40 px-4 py-3.5">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            <FileText size={14} className="text-gold shrink-0" />
            <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-gold/70">
              Retrieved Chunk
            </p>
          </div>
          <h3 className="font-serif text-[15px] font-semibold leading-snug text-gold-light">
            {source.bookTitle}
          </h3>
          <p className="mt-0.5 text-[11px] text-silver/40">{source.author}</p>
        </div>
        <button
          onClick={onClose}
          className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-silver/40 transition-colors hover:bg-slate-custom/30 hover:text-silver"
        >
          <X size={15} />
        </button>
      </div>

      <div className="flex items-center gap-3 border-b border-slate-custom/30 bg-charcoal/30 px-4 py-2.5">
        <span className="rounded border border-slate-custom/40 bg-cream/50 px-2 py-0.5 text-[10px] font-medium text-silver/60">
          {source.act}
        </span>
        <span className="truncate text-[10px] text-silver/30">
          {source.chapter}
        </span>
        {source.metadata?.structure_type && (
          <span className="rounded border border-gold/20 bg-gold/5 px-2 py-0.5 text-[9px] font-medium text-gold/60">
            {source.metadata.structure_type}
          </span>
        )}
        {source.metadata?.is_repealed && (
          <span className="rounded border border-error/20 bg-error/5 px-2 py-0.5 text-[9px] font-medium text-error/70">
            Repealed
          </span>
        )}
      </div>

      <div className="flex items-center justify-between border-b border-slate-custom/30 px-4 py-2.5">
        <div className="flex min-w-0 items-center gap-2">
          <BookOpen size={12} className="text-gold/50 shrink-0" />
          <span className="truncate text-[11px] font-medium text-silver/60">
            {source.section}
          </span>
          {location && <span className="text-[11px] text-silver/40">- {location}</span>}
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-silver/35">
            {highlightCount ? `${activeHighlight + 1}/${highlightCount} matches` : "0 matches"}
          </span>
          <button
            onClick={() => navigateHighlight("up")}
            disabled={!highlightCount}
            className="flex h-5 w-5 items-center justify-center rounded text-silver/30 hover:bg-slate-custom/30 hover:text-silver disabled:opacity-30"
          >
            <ChevronUp size={12} />
          </button>
          <button
            onClick={() => navigateHighlight("down")}
            disabled={!highlightCount}
            className="flex h-5 w-5 items-center justify-center rounded text-silver/30 hover:bg-slate-custom/30 hover:text-silver disabled:opacity-30"
          >
            <ChevronDown size={12} />
          </button>
        </div>
      </div>

      <div ref={containerRef} className="flex-1 overflow-y-auto px-5 py-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="h-px flex-1 bg-slate-custom/20"></div>
          <span className="text-[10px] font-medium tracking-wider text-silver/25 uppercase">
            RAG Retrieval Text
          </span>
          <div className="h-px flex-1 bg-slate-custom/20"></div>
        </div>

        <div className="font-serif text-[14px] leading-[1.9] tracking-[0.01em]">
          {renderHighlightedText(source.fullText || source.matchedText, source.highlightRanges)}
        </div>

        {source.reasons?.length > 0 && (
          <div className="mt-6">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-silver/35">
              Retrieval Reasons
            </p>
            <div className="flex flex-wrap gap-1.5">
              {source.reasons.map((reason) => (
                <span
                  key={reason}
                  className="rounded border border-slate-custom/30 bg-charcoal/35 px-2 py-1 text-[10px] text-silver/45"
                >
                  {reason}
                </span>
              ))}
            </div>
          </div>
        )}

        {(citationEntries.length > 0 || metadataEntries.length > 0) && (
          <div className="mt-6 grid gap-4">
            {citationEntries.length > 0 && (
              <div>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-silver/35">
                  Citation
                </p>
                <dl className="grid gap-1.5 rounded-lg border border-slate-custom/25 bg-charcoal/20 p-3">
                  {citationEntries.map(([key, value]) => (
                    <div key={key} className="grid grid-cols-[92px_minmax(0,1fr)] gap-2 text-[11px]">
                      <dt className="text-silver/35">{key}</dt>
                      <dd className="break-words text-silver/60">{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}

            {metadataEntries.length > 0 && (
              <div>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-silver/35">
                  Metadata
                </p>
                <dl className="grid gap-1.5 rounded-lg border border-slate-custom/25 bg-charcoal/20 p-3">
                  {metadataEntries.map(([key, value]) => (
                    <div key={key} className="grid grid-cols-[92px_minmax(0,1fr)] gap-2 text-[11px]">
                      <dt className="text-silver/35">{key}</dt>
                      <dd className="break-words text-silver/60">{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="border-t border-slate-custom/40 px-4 py-2.5 flex items-center justify-between">
        <span className="text-[10px] text-silver/30">
          RAG score: {Math.round(source.relevanceScore * 100)}%
        </span>
        <span
          className={`rounded px-2 py-0.5 text-[10px] font-medium ${
            source.relevanceScore >= 0.95
              ? "bg-success/8 text-success border border-success/15"
              : source.relevanceScore >= 0.85
              ? "bg-gold/8 text-gold border border-gold/15"
              : "bg-silver/8 text-silver border border-silver/15"
          }`}
        >
          {source.relevanceScore >= 0.95
            ? "High Match"
            : source.relevanceScore >= 0.85
            ? "Moderate Match"
            : "Retrieved Match"}
        </span>
      </div>
    </div>
  );
}
