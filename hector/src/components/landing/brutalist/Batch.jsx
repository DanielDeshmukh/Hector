"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Check, Copy, Download, Play, Square, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/landing/cn";
import { searchHector } from "@/lib/landing/api";
import { BATCH_QUERIES } from "@/lib/landing/samples";
import { Btn, Reveal } from "./ui";
import { useCopy } from "@/lib/landing/hooks";

const MAX = 50;
const GAP_MS = 1100; // stay inside the per-minute limit on /search

const seed = BATCH_QUERIES.map((b) => b.q).join("\n");

export function BatchSection() {
  const [paste, setPaste] = useState(seed);
  const [line, setLine] = useState("");
  const [rows, setRows] = useState([]);
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const stop = useRef(false);
  const started = useRef(0);
  const { copied, copy } = useCopy();

  const queue = useMemo(
    () => paste.split("\n").map((l) => l.trim()).filter(Boolean).slice(0, MAX),
    [paste],
  );

  const build = (lines) =>
    lines.map((text, i) => ({ id: i + 1, text, status: "queued", citation: null, score: null, ms: null, error: null }));

  const start = () => {
    if (!queue.length || running) return;
    const built = build(queue);
    setRows(built);
    setElapsed(0);
    setRunning(true);
    stop.current = false;
    started.current = performance.now();
    (async () => {
      for (let i = 0; i < built.length; i += 1) {
        if (stop.current) break;
        const t0 = performance.now();
        setRows((rs) => rs.map((r, j) => (j === i ? { ...r, status: "resolving" } : r)));
        try {
          const out = await searchHector(built[i].text);
          const ms = Math.round(performance.now() - t0);
          const s = out?.sources?.[0];
          setRows((rs) =>
            rs.map((r, j) =>
              j === i
                ? {
                    ...r,
                    status: s ? "resolved" : "empty",
                    citation: s ? `${s.act || "—"} §${s.section || "—"}` : null,
                    score: s ? Math.round((s.relevanceScore || 0) * 100) / 100 : null,
                    ms,
                    error: null,
                  }
                : r,
            ),
          );
        } catch (e) {
          const ms = Math.round(performance.now() - t0);
          setRows((rs) =>
            rs.map((r, j) => (j === i ? { ...r, status: "error", ms, error: e?.message || "unreachable" } : r)),
          );
        }
        setElapsed(Math.round(performance.now() - started.current));
        if (i < built.length - 1 && !stop.current) {
          await new Promise((res) => setTimeout(res, GAP_MS));
        }
      }
      setRunning(false);
      setElapsed(Math.round(performance.now() - started.current));
    })();
  };

  const halt = () => {
    stop.current = true;
    setRunning(false);
  };

  const clear = () => {
    stop.current = true;
    setRunning(false);
    setRows([]);
    setElapsed(0);
  };

  const done = rows.filter((r) => r.status !== "queued" && r.status !== "resolving").length;
  const stats = useMemo(
    () => ({
      resolved: rows.filter((r) => r.status === "resolved").length,
      empty: rows.filter((r) => r.status === "empty").length,
      errored: rows.filter((r) => r.status === "error").length,
    }),
    [rows],
  );

  const csv = useMemo(() => {
    const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const head = "n,query,citation,score,ms,status";
    const body = rows.map((r) => [r.id, esc(r.text), esc(r.citation ?? ""), r.score ?? "", r.ms ?? "", r.status].join(","));
    return [head, ...body].join("\n");
  }, [rows]);

  const exportCsv = () => {
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `hector-batch-${rows.length}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const annexure = rows
    .filter((r) => r.citation)
    .map((r) => `${String(r.id).padStart(2, "0")}.  ${r.citation}`)
    .join("\n");

  return (
    <section id="batch" className="relative border-t border-hair bg-ink/40">
      <div className="mx-auto w-full max-w-[1080px] px-5 py-16 sm:px-8 md:py-24">
        <Reveal y={false}>
          <div className="flex flex-col gap-5 border-b border-hair pb-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="label-xs text-gold">05 · Batch runs</p>
              <h2 className="mt-4 max-w-[22ch] font-display text-[clamp(1.9rem,4.4vw,3.1rem)] leading-[0.94] tracking-[-0.025em] text-paper">
                Eight questions.
                <span className="block italic text-gold-light">Eight live requests.</span>
              </h2>
            </div>
            <p className="max-w-[40ch] text-[13.5px] leading-[1.7] text-silver">
              The list below is already loaded. Pressing run issues one request per line against the live index,
              in order, and records the citation and the measured round-trip for each. Nothing is pre-filled.
            </p>
          </div>
        </Reveal>

        {/* command line */}
        <div className="mt-8 border border-hair bg-panel">
          <div className="flex items-center gap-3 px-4 py-3">
            <span className="font-mono text-[13px] text-gold">›</span>
            <input
              value={line}
              onChange={(e) => setLine(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  if (line.trim()) {
                    setPaste((p) => (p ? `${p}\n${line.trim()}` : line.trim()));
                    setLine("");
                  }
                }
              }}
              spellCheck={false}
              placeholder="add a question and press enter"
              className="min-w-0 flex-1 bg-transparent font-mono text-[13px] text-paper outline-none placeholder:text-muted/70"
            />
            <button
              onClick={() => {
                if (!line.trim()) return;
                setPaste((p) => (p ? `${p}\n${line.trim()}` : line.trim()));
                setLine("");
              }}
              className="shrink-0 border border-hair px-2.5 py-1 font-mono text-[10.5px] text-silver transition-colors hover:border-gold hover:text-gold"
            >
              add
            </button>
          </div>

          <textarea
            value={paste}
            onChange={(e) => setPaste(e.target.value)}
            spellCheck={false}
            placeholder="one question per line…"
            className="h-[150px] w-full resize-none border-t border-hair bg-cream/40 px-4 py-3 font-mono text-[12.5px] leading-[1.85] text-paper outline-none placeholder:text-muted/60"
          />

          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-hair px-4 py-2.5">
            <span className="font-mono text-[11px] text-muted">
              <span className={cn(queue.length > MAX ? "text-error" : "text-gold")}>{queue.length}</span> / {MAX} queued
            </span>
            <button
              onClick={() => setPaste(seed)}
              className="font-mono text-[11px] text-muted underline-offset-4 transition-colors hover:text-gold hover:underline"
            >
              restore the eight
            </button>
            <button onClick={clear} className="font-mono text-[11px] text-muted transition-colors hover:text-silver">
              clear
            </button>
            <Btn onClick={running ? halt : start} className="ml-auto px-4 py-2">
              {running ? (
                <>
                  <Square className="h-3 w-3 fill-current" /> stop
                </>
              ) : (
                <>
                  <Play className="h-3 w-3 fill-current" /> run {queue.length}
                </>
              )}
            </Btn>
          </div>
        </div>

        {/* the ledger */}
        <ol className="divide-y divide-hair border-x border-b border-hair">
          {rows.length === 0 && (
            <li className="px-4 py-12 text-center">
              <p className="font-display text-[22px] italic text-silver/55">Nothing queued.</p>
              <p className="mx-auto mt-2 max-w-[38ch] text-[12.5px] leading-relaxed text-muted">
                The eight questions are pre-loaded above. Press run to send them, or replace them with your own
                list first.
              </p>
            </li>
          )}

          {rows.map((r) => (
            <li
              key={r.id}
              className={cn(
                "flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-3.5 transition-colors duration-200",
                r.status === "resolving" ? "bg-gold/[0.05]" : "hover:bg-panel/50",
              )}
            >
              <span className="w-6 shrink-0 font-mono text-[10.5px] text-muted">{String(r.id).padStart(2, "0")}</span>
              <span className="min-w-[200px] flex-1 text-[13.5px] leading-snug text-paper/90">{r.text}</span>

              <span className="flex shrink-0 items-center gap-2">
                <span
                  className={cn(
                    "h-1 w-1",
                    r.status === "resolved"
                      ? "bg-success"
                      : r.status === "empty"
                        ? "bg-warning"
                        : r.status === "error"
                          ? "bg-error"
                          : r.status === "resolving"
                            ? "animate-pulse bg-gold"
                            : "bg-slate-custom/60",
                  )}
                />
                <span
                  className={cn(
                    "font-mono text-[10.5px]",
                    r.status === "resolved"
                      ? "text-success/80"
                      : r.status === "empty"
                        ? "text-warning/85"
                        : r.status === "error"
                          ? "text-error/85"
                          : "text-muted",
                  )}
                >
                  {r.status === "queued" ? "— — —" : r.status}
                </span>
              </span>

              <span className="w-full shrink-0 font-mono text-[11.5px] sm:w-[300px] sm:text-right">
                {r.citation ? (
                  <span className="text-gold-light">
                    {r.citation}
                    {r.score !== null && <span className="ml-2 text-muted">{r.score}</span>}
                  </span>
                ) : r.status === "error" ? (
                  <span className="text-error/70">{r.error}</span>
                ) : r.status === "empty" ? (
                  <span className="text-warning/70">no source matched</span>
                ) : null}
                {r.ms !== null && <span className="ml-3 text-muted">{r.ms} ms</span>}
              </span>
            </li>
          ))}
        </ol>

        {/* footer */}
        <div className="flex flex-wrap items-center gap-x-8 gap-y-3 border-x border-b border-hair px-4 py-3">
          <span className="font-mono text-[11px] text-muted">
            <span className="text-success/85">{stats.resolved}</span> resolved
            <span className="mx-2 text-slate-custom">·</span>
            <span className="text-warning/85">{stats.empty}</span> empty
            <span className="mx-2 text-slate-custom">·</span>
            <span className={stats.errored ? "text-error/85" : ""}>{stats.errored}</span> errored
            <span className="mx-2 text-slate-custom">·</span>
            {(elapsed / 1000).toFixed(2)}s elapsed
          </span>
          <span className="ml-auto flex items-center gap-4">
            <button
              onClick={exportCsv}
              disabled={!done}
              className="flex items-center gap-1.5 font-mono text-[11px] text-muted transition-colors hover:text-gold disabled:opacity-35"
            >
              <Download className="h-3 w-3" strokeWidth={1.8} /> CSV
            </button>
            <button
              onClick={() => copy(annexure, "annex")}
              disabled={!stats.resolved}
              className="flex items-center gap-1.5 font-mono text-[11px] text-muted transition-colors hover:text-gold disabled:opacity-35"
            >
              {copied === "annex" ? (
                <Check className="h-3 w-3 text-success" />
              ) : (
                <Copy className="h-3 w-3" strokeWidth={1.8} />
              )}
              citation annexure
            </button>
          </span>
        </div>

        <p className="mt-4 flex max-w-[80ch] items-start gap-2 font-mono text-[10.5px] leading-[1.7] text-muted">
          <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0 text-warning/70" strokeWidth={1.6} />
          Each row is one live request to <span className="text-silver/80">/search</span>. The millisecond figure
          is measured in this browser, round-trip, and will differ from yours. The citation is whatever the index
          returned; where it returned nothing, the row says so rather than substituting a near match. Requests are
          serialised about a second apart to stay inside the endpoint&rsquo;s rate limit.
        </p>
      </div>
    </section>
  );
}
