import { X, BookOpen, FileText, ChevronUp, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";

function renderHighlightedText(text, ranges) {
  if (!ranges.length) {
    return <span>{text}</span>;
  }

  const sortedRanges = [...ranges].sort((a, b) => a.start - b.start);
  const parts = [];
  let lastEnd = 0;

  sortedRanges.forEach((range, i) => {
    // Text before highlight
    if (range.start > lastEnd) {
      parts.push(
        <span key={`text-${i}`} className="text-silver/70">
          {text.slice(lastEnd, range.start)}
        </span>
      );
    }
    // Highlighted text
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

  // Remaining text
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

  useEffect(() => {
    // Scroll to first highlight
    const el = document.getElementById(`highlight-${activeHighlight}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [activeHighlight, source.id]);

  const navigateHighlight = (direction) => {
    const total = source.highlightRanges.length;
    if (direction === "up") {
      setActiveHighlight((prev) => (prev - 1 + total) % total);
    } else {
      setActiveHighlight((prev) => (prev + 1) % total);
    }
  };

  return (
    <div className="flex h-full flex-col bg-cream border-l border-slate-custom/40 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-slate-custom/40 px-4 py-3.5">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            <FileText size={14} className="text-gold shrink-0" />
            <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-gold/70">
              Source Document
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

      {/* Document Metadata Bar */}
      <div className="flex items-center gap-3 border-b border-slate-custom/30 bg-charcoal/30 px-4 py-2.5">
        <span className="rounded border border-slate-custom/40 bg-cream/50 px-2 py-0.5 text-[10px] font-medium text-silver/60">
          {source.act}
        </span>
        <span className="text-[10px] text-silver/30">
          {source.chapter}
        </span>
      </div>

      {/* Section info */}
      <div className="flex items-center justify-between border-b border-slate-custom/30 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <BookOpen size={12} className="text-gold/50" />
          <span className="text-[11px] font-medium text-silver/60">
            {source.section}
          </span>
          <span className="text-silver/20">-</span>
          <span className="text-[11px] text-silver/40">
            Page {source.page}, para {source.paragraph}
          </span>
        </div>

        {/* Highlight navigator */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-silver/35">
            {activeHighlight + 1}/{source.highlightRanges.length} matches
          </span>
          <button
            onClick={() => navigateHighlight("up")}
            className="flex h-5 w-5 items-center justify-center rounded text-silver/30 hover:bg-slate-custom/30 hover:text-silver"
          >
            <ChevronUp size={12} />
          </button>
          <button
            onClick={() => navigateHighlight("down")}
            className="flex h-5 w-5 items-center justify-center rounded text-silver/30 hover:bg-slate-custom/30 hover:text-silver"
          >
            <ChevronDown size={12} />
          </button>
        </div>
      </div>

      {/* Document Content */}
      <div ref={containerRef} className="flex-1 overflow-y-auto px-5 py-5">
        {/* Page number indicator */}
        <div className="mb-4 flex items-center gap-3">
          <div className="h-px flex-1 bg-slate-custom/20"></div>
          <span className="text-[10px] font-medium tracking-wider text-silver/25 uppercase">
            Page {source.page}
          </span>
          <div className="h-px flex-1 bg-slate-custom/20"></div>
        </div>

        {/* Document text - styled to look like a legal document */}
        <div className="font-serif text-[14px] leading-[1.9] tracking-[0.01em]">
          {renderHighlightedText(source.fullText, source.highlightRanges)}
        </div>

        {/* Page footer */}
        <div className="mt-8 border-t border-slate-custom/20 pt-3">
          <div className="flex items-center justify-between text-[10px] text-silver/25">
            <span>{source.act}</span>
            <span>p. {source.page}</span>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-slate-custom/40 px-4 py-2.5 flex items-center justify-between">
        <span className="text-[10px] text-silver/30">
          Relevance: {Math.round(source.relevanceScore * 100)}%
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
            ? "High Confidence"
            : source.relevanceScore >= 0.85
            ? "Moderate Confidence"
            : "Partial Match"}
        </span>
      </div>
    </div>
  );
}
