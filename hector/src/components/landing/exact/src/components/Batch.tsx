import { useEffect, useMemo, useRef, useState } from "react";
import { Check, Copy, Download, Play, Square } from "lucide-react";
import { cn } from "../utils/cn";
import { Btn, Reveal } from "./ui";
import { CORPUS } from "../data/corpus";
import { TOTAL_ACTS } from "../data/acts";
import { digest, parseQuery, retrieve, SAMPLE_BATCH, type Hit } from "../lib/text";
import { useCopy } from "../lib/hooks";

const MAX = 50;

type Status = "queued" | "resolving" | "resolved" | "unresolved" | "duplicate";

interface Row {
  id: number;
  text: string;
  status: Status;
  code: string | null;
  number: string | null;
  hits: Hit[];
  ms: number;
  dupOf?: number;
}

const normalise = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

function build(raw: string): Row[] {
  const lines = raw.split("\n").map((l) => l.trim()).filter(Boolean).slice(0, MAX);
  const seen = new Map<string, number>();
  return lines.map((text, i) => {
    const p = parseQuery(text);
    const key = `${p.code ?? "auto"}#${p.number ?? normalise(text).split(" ").filter((w) => w.length > 4).slice(0, 3).join("")}`;
    const dupOf = seen.get(key);
    if (dupOf === undefined) seen.set(key, i + 1);
    return {
      id: i + 1,
      text,
      status: dupOf ? "duplicate" : "queued",
      code: p.code,
      number: p.number,
      hits: [],
      ms: 0,
      dupOf,
    };
  });
}

const run = (text: string) => {
  const hits = retrieve(text, 3);
  return {
    hits,
    ms: hits.length ? 6 + (parseInt(digest(text).slice(0, 3), 16) % 29) : 0,
  };
};

const dot = (r: Row) =>
  r.status === "resolved"
    ? "bg-success"
    : r.status === "unresolved"
      ? "bg-warning"
      : r.status === "duplicate"
        ? "bg-slate-custom"
        : r.status === "resolving"
          ? "bg-gold"
          : "bg-slate-custom/60";

export function BatchSection() {
  const [line, setLine] = useState("");
  const [paste, setPaste] = useState("");
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState<Row[]>([]);
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const cur = useRef(-1);
  const ref = useRef<Row[]>([]);
  const { copied, copy } = useCopy();

  const queue = open ? paste : line;
  const count = queue.split("\n").map((l) => l.trim()).filter(Boolean).length;

  const start = () => {
    const built = build(queue);
    if (!built.length) return;
    ref.current = built;
    setRows(built);
    cur.current = -1;
    setElapsed(0);
    setRunning(true);
  };

  const addLine = () => {
    if (!line.trim()) return;
    setPaste((p) => (p ? `${p}\n${line.trim()}` : line.trim()));
    setOpen(true);
    setLine("");
  };

  useEffect(() => {
    if (!running) return;
    const tick = window.setInterval(() => {
      const n = cur.current + 1;
      if (n >= ref.current.length) {
        setRunning(false);
        window.clearInterval(tick);
        return;
      }
      cur.current = n;
      setRows((rs) =>
        rs.map((r, i) => {
          if (i !== n || r.status === "duplicate") return r;
          const out = run(r.text);
          return { ...r, ...out, status: out.hits.length ? "resolved" : "unresolved" };
        }),
      );
    }, 90);
    const clock = window.setInterval(() => setElapsed((e) => e + 90), 90);
    return () => {
      window.clearInterval(tick);
      window.clearInterval(clock);
    };
  }, [running]);

  const done = rows.filter((r) => r.status === "resolved" || r.status === "unresolved").length;
  const stats = useMemo(
    () => ({
      resolved: rows.filter((r) => r.status === "resolved").length,
      unresolved: rows.filter((r) => r.status === "unresolved").length,
      dups: rows.filter((r) => r.status === "duplicate").length,
    }),
    [rows],
  );

  const csv = useMemo(() => {
    const head = "n,query,act,section,status,citation,ms";
    const body = rows.map((r) => {
      const t = r.hits[0];
      const esc = (v: string) => `"${v.replace(/"/g, '""')}"`;
      return [
        r.id,
        esc(r.text),
        r.code ?? "",
        r.number ?? "",
        r.status,
        esc(t ? `${t.section.act}, ${t.section.section}` : "unresolved"),
        r.ms,
      ].join(",");
    });
    return [head, ...body].join("\n");
  }, [rows]);

  const annexure = rows
    .filter((r) => r.hits[0])
    .map((r) => `${r.id}.  ${r.hits[0].section.act}, ${r.hits[0].section.section} [${r.hits[0].section.status}]`)
    .join("\n");

  const export_csv = () => {
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `hector-batch-${rows.length}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <section id="batch" className="relative border-t border-hair bg-ink/40">
      <div className="mx-auto w-full max-w-[1080px] px-5 py-16 sm:px-8 md:py-24">
        <Reveal y={false}>
          <div className="flex flex-col gap-5 border-b border-hair pb-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="label-xs text-gold">05 · Batch runs</p>
              <h2 className="mt-4 max-w-[22ch] font-display text-[clamp(1.9rem,4.4vw,3.1rem)] leading-[0.94] tracking-[-0.025em] text-paper">
                Fifty questions.
                <span className="block italic text-gold-light">One queue.</span>
              </h2>
            </div>
            <p className="max-w-[40ch] text-[13.5px] leading-[1.7] text-silver">
              Type a question and press enter, or paste a list. Each resolves to one citation, one line, in order.
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
                  addLine();
                }
              }}
              spellCheck={false}
              placeholder="what replaced Section 420 IPC?"
              className="min-w-0 flex-1 bg-transparent font-mono text-[13px] text-paper outline-none placeholder:text-muted/70"
            />
            <button
              onClick={addLine}
              className="shrink-0 border border-hair px-2.5 py-1 font-mono text-[10.5px] text-silver transition-colors hover:border-gold hover:text-gold"
            >
              add
            </button>
          </div>

          {open && (
            <textarea
              value={paste}
              onChange={(e) => setPaste(e.target.value)}
              spellCheck={false}
              placeholder={"one question per line…"}
              className="h-[168px] w-full resize-none border-t border-hair bg-cream/40 px-4 py-3 font-mono text-[12.5px] leading-[1.85] text-paper outline-none placeholder:text-muted/60"
            />
          )}

          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-hair px-4 py-2.5">
            <span className="font-mono text-[11px] text-muted">
              <span className={cn(count > MAX ? "text-error" : "text-gold")}>{Math.min(count, MAX)}</span> / {MAX}
              {count > MAX && <span className="ml-2 text-error/80">{count - MAX} beyond the cap</span>}
            </span>
            <button
              onClick={() => {
                setOpen((v) => !v);
                if (!open && !paste) setPaste(SAMPLE_BATCH);
              }}
              className="font-mono text-[11px] text-muted underline-offset-4 transition-colors hover:text-gold hover:underline"
            >
              {open ? "hide the list" : "paste a list instead"}
            </button>
            <button
              onClick={() => {
                setRows([]);
                setPaste("");
                setLine("");
                setOpen(false);
                setRunning(false);
                setElapsed(0);
              }}
              className="font-mono text-[11px] text-muted transition-colors hover:text-silver"
            >
              clear
            </button>
            <Btn onClick={running ? () => setRunning(false) : start} className="ml-auto px-4 py-2">
              {running ? (
                <>
                  <Square className="h-3 w-3 fill-current" /> stop
                </>
              ) : (
                <>
                  <Play className="h-3 w-3 fill-current" /> run
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
                Add a question above, or paste a list — a matter index, a proof affidavit, whatever the desk is
                holding.
              </p>
            </li>
          )}

          {rows.map((r) => {
            const t = r.hits[0];
            return (
              <li
                key={r.id}
                className={cn(
                  "flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-3.5 transition-colors duration-200",
                  r.status === "resolving" ? "bg-gold/[0.05]" : "hover:bg-panel/50",
                )}
              >
                <span className="w-6 shrink-0 font-mono text-[10.5px] text-muted">
                  {String(r.id).padStart(2, "0")}
                </span>
                <span className="min-w-[200px] flex-1 text-[13.5px] leading-snug text-paper/90">{r.text}</span>

                <span className="flex shrink-0 items-center gap-2">
                  <span className={cn("h-1 w-1", dot(r))} />
                  <span
                    className={cn(
                      "font-mono text-[10.5px]",
                      r.status === "resolved"
                        ? "text-success/80"
                        : r.status === "unresolved"
                          ? "text-warning/85"
                          : "text-muted",
                    )}
                  >
                    {r.status === "queued" ? "— — —" : r.status === "resolving" ? "resolving" : r.status}
                    {r.dupOf ? ` · of ${String(r.dupOf).padStart(2, "0")}` : ""}
                  </span>
                </span>

                <span className="w-full shrink-0 font-mono text-[11.5px] sm:w-[268px] sm:text-right">
                  {t ? (
                    <span className="text-gold-light">
                      {t.section.code} {/^article/i.test(t.section.section) ? t.section.section : `s. ${t.section.section}`}
                      <span className="ml-2 text-muted">{t.section.status.toLowerCase()}</span>
                    </span>
                  ) : r.status === "unresolved" ? (
                    <span className="text-warning/70">no unit — name the act</span>
                  ) : null}
                </span>
              </li>
            );
          })}
        </ol>

        {/* footer line */}
        <div className="flex flex-wrap items-center gap-x-8 gap-y-3 border-x border-b border-hair px-4 py-3">
          <span className="font-mono text-[11px] text-muted">
            <span className="text-success/85">{stats.resolved}</span> resolved
            <span className="mx-2 text-slate-custom">·</span>
            <span className="text-warning/85">{stats.unresolved}</span> unresolved
            <span className="mx-2 text-slate-custom">·</span>
            {stats.dups} de-duped
            <span className="mx-2 text-slate-custom">·</span>
            {(elapsed / 1000).toFixed(2)}s
          </span>
          <span className="ml-auto flex items-center gap-4">
            <button
              onClick={export_csv}
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
              {copied === "annex" ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" strokeWidth={1.8} />}
              citation annexure
            </button>
          </span>
        </div>

        <p className="mt-4 max-w-[70ch] font-mono text-[10.5px] leading-[1.7] text-muted">
          Demonstration runner · resolves against the {CORPUS.length}-unit extract on this page, by the same parse →
          statutory identity → unit sequence the hosted index runs over {TOTAL_ACTS} statutes.
        </p>
      </div>
    </section>
  );
}
