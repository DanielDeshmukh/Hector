import { BookOpen, ExternalLink, Tag, BarChart3, Bookmark, BookmarkCheck } from "lucide-react";
import PipelineStatus from "./PipelineStatus";

function formatLocation(source) {
  const parts = [];
  if (source.page) parts.push(`Page ${source.page}`);
  if (source.paragraph) parts.push(`para ${source.paragraph}`);
  return parts.join(", ");
}

function renderFormattedText(text) {
  const lines = String(text || "").split("\n");
  return lines.map((line, i) => {
    let processed = line.replace(
      /\*\*(.+?)\*\*/g,
      '<strong class="text-gold-light font-semibold">$1</strong>'
    );
    processed = processed.replace(
      /\*(.+?)\*/g,
      '<em class="text-silver italic">$1</em>'
    );

    if (line.startsWith("- ")) {
      return (
        <li
          key={i}
          className="ml-4 list-disc py-0.5 text-[13.5px] leading-relaxed text-silver/90 marker:text-gold/40"
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

function renderBodyLines(body) {
  return String(body || "")
    .split("\n")
    .filter(Boolean)
    .map((line, index) => (
      <p key={`${index}-${line}`} className="text-[13.5px] leading-[1.75] text-silver/90">
        {line}
      </p>
    ));
}

function ComparisonTable({ rows }) {
  if (!rows?.length) return null;

  return (
    <div className="mt-3 overflow-x-auto rounded-md border border-slate-custom/30">
      <table className="w-full min-w-[620px] border-collapse text-left text-[12px]">
        <thead className="bg-cream/70 text-[10px] uppercase tracking-[0.12em] text-silver/45">
          <tr>
            <th className="w-[24%] border-b border-slate-custom/30 px-3 py-2 font-semibold">Point</th>
            <th className="w-[38%] border-b border-slate-custom/30 px-3 py-2 font-semibold">IPC</th>
            <th className="w-[38%] border-b border-slate-custom/30 px-3 py-2 font-semibold">BNS</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.point} className="border-t border-slate-custom/20 align-top">
              <td className="px-3 py-2 font-medium text-gold-light">{row.point}</td>
              <td className="px-3 py-2 leading-relaxed text-silver/75">{row.ipc}</td>
              <td className="px-3 py-2 leading-relaxed text-silver/75">{row.bns}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CitationGrounding({ sources, onSourceClick, activeSourceId }) {
  if (!sources?.length) return null;

  return (
    <section>
      <h3 className="mb-2 font-serif text-[16px] font-semibold text-gold-light">
        Citation Grounding
      </h3>
      <div className="grid gap-2">
        {sources.map((source) => {
          const isActive = activeSourceId === source.source_id;
          return (
          <button
            key={`${source.number}-${source.source_id || source.title}`}
            type="button"
            disabled={!source.source_id}
            onClick={() => source.source_id && onSourceClick(source.source_id)}
            className={`rounded-md border px-3 py-2 text-left transition-colors ${
              isActive
                ? "border-gold/40 bg-gold/5"
                : "border-slate-custom/25 bg-cream/45 hover:border-slate-custom/50"
            } disabled:cursor-default`}
          >
            <div className="flex flex-wrap items-center gap-2 text-[10px] text-silver/40">
              <span className="font-mono text-gold">[S{source.number}]</span>
              <span>{source.title}</span>
              <span>-</span>
              <span>
                Section {source.section} {source.act}
              </span>
              <span>-</span>
              <span>{Math.round(Number(source.similarity || 0) * 100)}% relevance</span>
            </div>
            <p className="mt-1 text-[12px] leading-relaxed text-silver/70">
              "{source.excerpt}"
            </p>
          </button>
        )})}
      </div>
    </section>
  );
}

function StructuredAnswer({ response, onSourceClick, activeSourceId }) {
  if (!response.answerSections?.length) {
    return <div className="space-y-0">{renderFormattedText(response.answer)}</div>;
  }

  return (
    <div className="space-y-5">
      {response.answerSections.map((section) => (
        <section key={section.title}>
          <h3 className="mb-2 font-serif text-[16px] font-semibold text-gold-light">
            {section.title}
          </h3>
          <div className="space-y-2">{renderBodyLines(section.body)}</div>
          <ComparisonTable rows={section.rows} />
        </section>
      ))}

      <CitationGrounding
        sources={response.sourceSections}
        onSourceClick={onSourceClick}
        activeSourceId={activeSourceId}
      />

      <p className="border-t border-slate-custom/25 pt-3 text-[11px] leading-relaxed text-silver/45">
        Note: This is for informational purposes only and does not constitute legal advice.
      </p>
    </div>
  );
}

export default function ResponseDisplay({
  response,
  onSourceClick,
  activeSourceId,
  bookmarks = [],
  onToggleBookmark,
}) {
  const isBookmarked = (sourceId) => bookmarks.some((b) => b.id === sourceId);
  return (
    <div className="space-y-5 animate-fade-in">
      <PipelineStatus stages={response.pipeline} />

      <div className="flex flex-wrap items-center gap-3">
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

      <div className="rounded-lg border border-slate-custom/30 bg-charcoal/40 p-5">
        <StructuredAnswer
          response={response}
          onSourceClick={onSourceClick}
          activeSourceId={activeSourceId}
        />
      </div>

      <div>
        <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-silver/50">
          Source Documents ({response.sources.length})
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
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded font-mono text-[11px] font-semibold ${
                  activeSourceId === source.id
                    ? "bg-gold/15 text-gold"
                    : "bg-slate-custom/30 text-silver/50"
                }`}
              >
                {index + 1}
              </span>

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
                  <div className="flex items-center gap-1.5 shrink-0">
                    {onToggleBookmark && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onToggleBookmark(source);
                        }}
                        className={`rounded p-1 transition-colors ${
                          isBookmarked(source.id)
                            ? "text-gold bg-gold/10"
                            : "text-silver/20 hover:text-gold/60"
                        }`}
                        title={isBookmarked(source.id) ? "Remove bookmark" : "Bookmark this source"}
                      >
                        {isBookmarked(source.id) ? (
                          <BookmarkCheck size={13} />
                        ) : (
                          <Bookmark size={13} />
                        )}
                      </button>
                    )}
                    <ExternalLink
                      size={13}
                      className={`mt-0.5 shrink-0 ${
                        activeSourceId === source.id
                          ? "text-gold/60"
                          : "text-silver/20 group-hover:text-silver/40"
                      }`}
                    />
                  </div>
                </div>

                <p className="mt-1.5 line-clamp-2 text-[11.5px] leading-relaxed text-silver/50">
                  "{source.matchedText}"
                </p>

                <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px]">
                  <span className="flex items-center gap-1 text-silver/35">
                    <BookOpen size={10} />
                    {source.section}
                  </span>
                  {formatLocation(source) && (
                    <>
                      <span className="text-slate-custom">-</span>
                      <span className="text-silver/35">{formatLocation(source)}</span>
                    </>
                  )}
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

                {source.reasons?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {source.reasons.slice(0, 3).map((reason) => (
                      <span
                        key={reason}
                        className="rounded border border-slate-custom/30 bg-charcoal/40 px-1.5 py-0.5 text-[9.5px] text-silver/35"
                      >
                        {reason}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
