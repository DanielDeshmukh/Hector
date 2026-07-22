"use client";

import { useState } from "react";
import { Upload, Play, FileText, Download, Check, X, AlertTriangle, Loader2 } from "lucide-react";
import { runBatchQuery, parseBatchText, exportPdf } from "@/api/hectorApi";

export default function BatchQueryPanel({ onClose }) {
  const [mode, setMode] = useState("input"); // "input" | "results"
  const [inputText, setInputText] = useState("");
  const [queries, setQueries] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleParse = async () => {
    try {
      const parsed = await parseBatchText(inputText);
      setQueries(parsed.queries);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRun = async () => {
    if (queries.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const result = await runBatchQuery(queries);
      setResults(result);
      setMode("results");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!results) return;
    const csv = [
      "Query,Route,Confidence,Results,Time(ms),Cache Hit,Error",
      ...results.results.map(r =>
        `"${r.query}","${r.route || ""}",${r.confidence || 0},${r.result_count},${r.response_ms || 0},${r.cache_hit},"${r.error || ""}"`
      ),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hector-batch-${results.job_id}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-3xl max-h-[85vh] rounded-xl border border-slate-custom/30 bg-cream shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-custom/30 px-5 py-4">
          <div className="flex items-center gap-2">
            <FileText size={16} className="text-gold" />
            <h2 className="font-serif text-lg font-semibold text-gold-light">Batch Query</h2>
            <span className="text-[11px] text-silver/40">({queries.length} queries)</span>
          </div>
          <button
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-md text-silver/40 hover:bg-slate-custom/30 hover:text-silver"
          >
            <X size={14} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {mode === "input" ? (
            <div className="space-y-4">
              <div>
                <label className="block text-[11px] font-medium text-silver/50 mb-2">
                  Enter queries (one per line)
                </label>
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder={"What is the punishment for murder under BNS?\nDefine cheating under Section 318 BNS\nCompare IPC 302 with BNS 101"}
                  className="w-full h-48 rounded-lg border border-slate-custom/40 bg-charcoal/40 px-4 py-3 text-[13px] text-gold-light placeholder-silver/30 outline-none focus:border-gold/40 resize-none font-mono"
                />
              </div>

              {queries.length > 0 && (
                <div className="rounded-lg border border-slate-custom/30 bg-charcoal/20 p-3">
                  <p className="text-[11px] text-silver/50 mb-2">Parsed queries:</p>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {queries.map((q, i) => (
                      <div key={i} className="flex items-center gap-2 text-[12px] text-silver/60">
                        <span className="text-silver/30 font-mono">{i + 1}.</span>
                        {q}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {error && (
                <div className="flex items-center gap-2 rounded-lg border border-error/20 bg-error/5 px-3 py-2 text-[12px] text-error">
                  <AlertTriangle size={12} />
                  {error}
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Summary */}
              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: "Total", value: results.total },
                  { label: "Completed", value: results.completed, color: "text-success" },
                  { label: "Failed", value: results.failed, color: results.failed > 0 ? "text-error" : "text-silver/40" },
                  { label: "Duration", value: `${(results.duration_ms / 1000).toFixed(1)}s` },
                ].map(({ label, value, color }) => (
                  <div key={label} className="text-center rounded-lg border border-slate-custom/20 bg-charcoal/20 p-3">
                    <p className={`text-lg font-serif font-semibold ${color || "text-gold-light"}`}>{value}</p>
                    <p className="text-[10px] text-silver/40">{label}</p>
                  </div>
                ))}
              </div>

              {/* Results table */}
              <div className="rounded-lg border border-slate-custom/30 overflow-hidden">
                <table className="w-full text-left text-[11px]">
                  <thead className="bg-charcoal/40">
                    <tr>
                      <th className="px-3 py-2 text-silver/50 font-medium">#</th>
                      <th className="px-3 py-2 text-silver/50 font-medium">Query</th>
                      <th className="px-3 py-2 text-silver/50 font-medium">Route</th>
                      <th className="px-3 py-2 text-silver/50 font-medium">Conf</th>
                      <th className="px-3 py-2 text-silver/50 font-medium">Time</th>
                      <th className="px-3 py-2 text-silver/50 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.results.map((r) => (
                      <tr key={r.index} className="border-t border-slate-custom/20">
                        <td className="px-3 py-2 text-silver/30 font-mono">{r.index + 1}</td>
                        <td className="px-3 py-2 text-silver/60 max-w-xs truncate" title={r.query}>{r.query}</td>
                        <td className="px-3 py-2 text-silver/40">{r.route?.replace(/_/g, " ") || "-"}</td>
                        <td className="px-3 py-2 text-silver/40">{r.confidence ? `${r.confidence}%` : "-"}</td>
                        <td className="px-3 py-2 text-silver/40 font-mono">{r.response_ms ? `${Math.round(r.response_ms)}ms` : "-"}</td>
                        <td className="px-3 py-2">
                          {r.error ? (
                            <span className="text-error text-[10px]">Failed</span>
                          ) : r.cache_hit ? (
                            <span className="text-gold text-[10px]">Cached</span>
                          ) : (
                            <Check size={12} className="text-success" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Response previews */}
              <div className="space-y-2">
                <p className="text-[11px] font-medium text-silver/50">Response Previews</p>
                {results.results.filter(r => r.response && !r.error).map((r) => (
                  <div key={r.index} className="rounded-lg border border-slate-custom/20 bg-charcoal/20 p-3">
                    <p className="text-[10px] text-gold/60 mb-1">#{r.index + 1} {r.query}</p>
                    <p className="text-[11px] text-silver/50 line-clamp-3">{r.response}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-slate-custom/30 px-5 py-3">
          <div className="text-[11px] text-silver/30">
            {mode === "input"
              ? `${queries.length} queries parsed`
              : `${results?.completed}/${results?.total} succeeded`}
          </div>
          <div className="flex items-center gap-2">
            {mode === "results" && (
              <button
                onClick={handleExport}
                className="flex items-center gap-1.5 rounded-lg border border-slate-custom/40 px-3 py-2 text-[11px] font-medium text-silver/60 hover:border-gold/30 hover:text-gold"
              >
                <Download size={11} />
                Export CSV
              </button>
            )}
            {mode === "input" && queries.length > 0 && (
              <button
                onClick={handleRun}
                disabled={loading}
                className="flex items-center gap-1.5 rounded-lg bg-gold/90 px-4 py-2 text-[11px] font-medium text-charcoal hover:bg-gold disabled:opacity-40"
              >
                {loading ? <Loader2 size={11} className="animate-spin" /> : <Play size={11} />}
                {loading ? "Running..." : `Run ${queries.length} Queries`}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
