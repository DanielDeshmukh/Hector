import { BookOpen, ExternalLink, Tag, BarChart3 } from "lucide-react";
import PipelineStatus from "./PipelineStatus";

function renderFormattedText(text) {
  const lines = text.split("\n");
  return lines.map((line, i) => {
    // Bold markers
    let processed = line.replace(
      /\*\*(.+?)\*\*/g,
      '<strong class="text-gold-light font-semibold">$1</strong>'
    );
    // Italic markers
    processed = processed.replace(
      /\*(.+?)\*/g,
      '<em class="text-silver italic">$1</em>'
    );

    if (line.startsWith("- ")) {
      return (
        <li
          key={i}
          className="ml-4 list-disc text-[13.5px] leading-relaxed text-silver/90 marker:text-gold/40 py-0.5"
          dangerouslySetInnerHTML={{ __html: processed.substring(2) }}
        />
      );
    }

    if (line.trim() === "") {
      return <div key={i} className="h-2.5" />;
    }

    return (
      <p
        key={i}
        className="text-[13.5px] leading-[1.75] text-silver/90"
        dangerouslySetInnerHTML={{ __html: processed }}
      />
    );
  });
}

export default function ResponseDisplay({
  response,
  onSourceClick,
  activeSourceId,
}) {
  return (
    <div className="space-y-5 animate-fade-in">
      {/* Pipeline Status */}
      <PipelineStatus stages={response.pipeline} />

      {/* Domain & Confidence Badge */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className="flex items-center gap-1.5 rounded-md border border-gold/20 bg-gold/5 px-2.5 py-1 text-[11px] font-medium text-gold">
          <Tag size={11} />
          {response.domain}
        </span>
        <span className="flex items-center gap-1.5 rounded-md border border-success/20 bg-success/5 px-2.5 py-1 text-[11px] font-medium text-success">
          <BarChart3 size={11} />
          Confidence: {response.confidence}%
        </span>
        <span className="text-[11px] text-silver/30">
          {new Date(response.timestamp).toLocaleString("en-IN", {
            day: "numeric",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {/* Main Response */}
      <div className="rounded-lg border border-slate-custom/30 bg-charcoal/40 p-5">
        <div className="space-y-0">{renderFormattedText(response.answer)}</div>
      </div>

      {/* Source Citations */}
      <div>
        <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-silver/50">
          Verified Sources ({response.sources.length})
        </p>
        <div className="grid gap-2">
          {response.sources.map((source, index) => (
            <button
              key={source.id}
              onClick={() => onSourceClick(source.id)}
              className={`group flex items-start gap-3 rounded-lg border p-3.5 text-left transition-all ${
                activeSourceId === source.id
                  ? "border-gold/40 bg-gold/5"
                  : "border-slate-custom/30 bg-cream/50 hover:border-slate-custom/60 hover:bg-cream/80"
              }`}
            >
              {/* Index */}
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded font-mono text-[11px] font-semibold ${
                  activeSourceId === source.id
                    ? "bg-gold/15 text-gold"
                    : "bg-slate-custom/30 text-silver/50"
                }`}
              >
                {index + 1}
              </span>

              {/* Content */}
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p
                      className={`text-[13px] font-medium leading-snug ${
                        activeSourceId === source.id
                          ? "text-gold-light"
                          : "text-silver group-hover:text-gold-light"
                      }`}
                    >
                      {source.bookTitle}
                    </p>
                    <p className="mt-0.5 text-[11px] text-silver/40">
                      {source.author}
                    </p>
                  </div>
                  <ExternalLink
                    size={13}
                    className={`mt-0.5 shrink-0 ${
                      activeSourceId === source.id
                        ? "text-gold/60"
                        : "text-silver/20 group-hover:text-silver/40"
                    }`}
                  />
                </div>

                <p className="mt-1.5 text-[11.5px] leading-relaxed text-silver/50 line-clamp-2">
                  "{source.matchedText}"
                </p>

                <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px]">
                  <span className="flex items-center gap-1 text-silver/35">
                    <BookOpen size={10} />
                    {source.section}
                  </span>
                  <span className="text-slate-custom">-</span>
                  <span className="text-silver/35">
                    Page {source.page}, para {source.paragraph}
                  </span>
                  <span className="text-slate-custom">-</span>
                  <span
                    className={`rounded px-1.5 py-0.5 font-medium ${
                      source.relevanceScore >= 0.95
                        ? "bg-success/8 text-success"
                        : source.relevanceScore >= 0.85
                        ? "bg-gold/8 text-gold"
                        : "bg-silver/8 text-silver"
                    }`}
                  >
                    {Math.round(source.relevanceScore * 100)}% match
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
