"use client";

import { useMemo, useState } from "react";
import { SlidersHorizontal, TriangleAlert, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/landing/cn";
import { Panel, SectionShell, Tag, Btn } from "./ui";
import { FIXTURES } from "@/lib/landing/fixtures";
import { scanUnits, anchorTotals, fixedWindows } from "@/lib/landing/boundary";
import { CUT_RULES } from "@/lib/landing/scannerSource";

const MAX_CHARS = CUT_RULES.maxChars.value;

export function ChunkingSection() {
  const [size, setSize] = useState(300);
  const [overlap, setOverlap] = useState(64);
  const [mode, setMode] = useState("window"); // "window" | "grammar"
  const [sel, setSel] = useState(0);

  const text = useMemo(() => FIXTURES.map((f) => f.text).join("\n"), []);
  const scan = useMemo(() => scanUnits(text), [text]);
  const units = scan.units;
  const anchors = useMemo(() => anchorTotals(units), [units]);
  const windows = useMemo(() => fixedWindows(text, size, overlap), [text, size, overlap]);
  const anchorOffsets = useMemo(() => units.map((u) => u.start), [units]);

  const severed = windows.filter((w) => w.midSentence).length;
  const detached = windows.filter((w) => w.lostAnchors.length > 0).length;
  const longest = Math.max(...units.map((u) => u.chars), 0);

  return (
    <SectionShell
      id="chunking"
      no="03"
      kicker="The chunking test"
      title={
        <>
          Set the window.
          <span className="block italic text-gold-light">Count what it cuts.</span>
        </>
      }
      lede={
        <>
          Both splitters run here in your browser on bundled sample text. The left is a configurable fixed-window
          simulation; the right is a JavaScript port of the repository's v2 section scanner. This lab does not
          read the live index or represent the current API ingestion path.
        </>
      }
      aside={
        <div className="grid gap-px bg-hair sm:grid-cols-2">
          {[
            ["sections in extract", String(units.length)],
            ["provisos at stake", String(anchors.proviso)],
            ["exceptions at stake", String(anchors.exception)],
            ["illustrations at stake", String(anchors.illustration)],
          ].map(([k, v]) => (
            <div key={k} className="bg-cream px-3 py-2.5">
              <p className="label-xs text-muted">{k}</p>
              <p className="mt-1 font-display text-[22px] leading-none text-gold-light">{v}</p>
            </div>
          ))}
        </div>
      }
    >
      <Panel className="overflow-hidden">
        {/* controls */}
        <div className="flex flex-col gap-4 border-b border-hair bg-panel-2 px-4 py-3.5 lg:flex-row lg:items-center">
          <div className="flex items-center gap-0 border border-hair">
            {[
              ["window", "Fixed window + overlap"],
              ["grammar", "Boundary grammar"],
            ].map(([m, label]) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={cn(
                  "px-3 py-2 label-xs transition-colors duration-200",
                  mode === m ? "bg-gold text-ink" : "text-silver hover:bg-panel hover:text-gold-light",
                )}
              >
                {label}
              </button>
            ))}
          </div>

          <div
            className={cn(
              "flex flex-1 flex-wrap items-center gap-5 transition-opacity duration-300",
              mode === "grammar" && "pointer-events-none opacity-30",
            )}
          >
            <label className="flex min-w-[190px] flex-1 items-center gap-3">
              <span className="flex items-center gap-1.5 label-xs text-muted">
                <SlidersHorizontal className="h-3 w-3" strokeWidth={1.6} />
                window
              </span>
              <input
                type="range"
                min={120}
                max={720}
                step={20}
                value={size}
                onChange={(e) => setSize(+e.target.value)}
                className="h-px flex-1 cursor-ew-resize appearance-none bg-slate-custom accent-[#c9a962] [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:bg-gold"
              />
              <span className="w-14 font-mono text-[11px] text-paper">{size} ch</span>
            </label>
            <label className="flex min-w-[190px] flex-1 items-center gap-3">
              <span className="flex items-center gap-1.5 label-xs text-muted">
                <SlidersHorizontal className="h-3 w-3" strokeWidth={1.6} />
                overlap
              </span>
              <input
                type="range"
                min={0}
                max={200}
                step={8}
                value={overlap}
                onChange={(e) => setOverlap(+e.target.value)}
                className="h-px flex-1 cursor-ew-resize appearance-none bg-slate-custom accent-[#c9a962] [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:bg-gold"
              />
              <span className="w-14 font-mono text-[11px] text-paper">{overlap} ch</span>
            </label>
          </div>
          <div className={cn("font-mono text-[11px]", mode === "grammar" ? "text-silver" : "text-muted")}>
            {mode === "window" ? `${windows.length} windows` : `${units.length} units`}
          </div>
        </div>

        {/* the tape */}
        <div className="border-b border-hair px-4 py-4">
          <div className="flex h-12 w-full overflow-hidden gap-px">
            {mode === "window"
              ? windows.map((w, i) => (
                  <button
                    key={i}
                    onMouseEnter={() => setSel(i)}
                    onClick={() => setSel(i)}
                    style={{ flexGrow: Math.max(1, w.text.length) }}
                    className={cn(
                      "relative min-w-[6px] border-t-2 transition-colors duration-200",
                      w.lostAnchors.length
                        ? "border-error/80 bg-error/[0.16] hover:bg-error/25"
                        : "border-slate-custom bg-slate-custom/20 hover:bg-slate-custom/35",
                      sel === i && "border-gold bg-gold/25",
                    )}
                    title={`window ${w.index + 1} · ${w.text.length} chars${w.lostAnchors.length ? ` · ${w.lostAnchors[0]}` : ""}`}
                  />
                ))
              : units.map((u, i) => (
                  <button
                    key={u.index}
                    onMouseEnter={() => setSel(i)}
                    onClick={() => setSel(i)}
                    style={{ flexGrow: Math.max(1, u.chars) }}
                    className={cn(
                      "relative min-w-[6px] border-t-2 bg-success/[0.13] transition-colors duration-200",
                      sel === i ? "border-gold bg-gold/20" : "border-success/60 hover:bg-success/20",
                    )}
                    title={`§ ${u.number} · ${u.chars} chars · intact`}
                  >
                    <span className="absolute inset-x-0 top-1 truncate px-1 text-left font-mono text-[9px] text-paper/70">
                      §{u.number}
                    </span>
                  </button>
                ))}
          </div>
          <div className="relative mt-1 h-3">
            {mode === "window" &&
              anchorOffsets
                .filter((o) => o < text.length)
                .map((o, i) => (
                  <span
                    key={i}
                    className="absolute top-0 h-3 w-px bg-gold"
                    style={{ left: `${(o / text.length) * 100}%` }}
                    title="a real section boundary falls inside the tape"
                  />
                ))}
          </div>
          {mode === "window" && (
            <p className="mt-2 font-mono text-[10.5px] text-muted">
              gold ticks mark where the grammar would have opened a unit — every one of them lands mid-window.
            </p>
          )}
        </div>

        {/* body */}
        <div className="grid lg:grid-cols-[minmax(0,1fr)_300px]">
          <div className="max-h-[400px] overflow-y-auto px-4 py-4">
            {mode === "window" ? (
              <ol className="space-y-3">
                {windows.map((w, i) => (
                  <li
                    key={i}
                    onMouseEnter={() => setSel(i)}
                    className={cn(
                      "border-l-2 bg-panel/40 py-2 pl-3 pr-3 transition-colors duration-200",
                      sel === i ? "border-gold bg-panel" : "border-hair",
                    )}
                  >
                    <div className="flex flex-wrap items-center gap-2 font-mono text-[10.5px] text-muted">
                      <span className="text-silver">w{String(w.index + 1).padStart(2, "0")}</span>
                      <span>·</span>
                      <span>
                        off {w.start}–{w.end}
                      </span>
                      <span>·</span>
                      <span>{w.text.length} ch</span>
                      {!w.orphaned ? <Tag tone="neutral">opens on anchor</Tag> : <Tag tone="muted">no anchor</Tag>}
                    </div>
                    <p className="mt-1.5 whitespace-pre-wrap font-mono text-[11.5px] leading-[1.7] text-silver/90">
                      {w.text.slice(0, 320)}
                      {w.text.length > 320 && <span className="text-muted"> …</span>}
                      {w.midSentence && <span className="text-error">▮</span>}
                    </p>
                    {w.lostAnchors.length > 0 && (
                      <ul className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1">
                        {w.lostAnchors.map((l) => (
                          <li key={l} className="flex items-center gap-1.5 text-[11px] text-error/85">
                            <TriangleAlert className="h-3 w-3" strokeWidth={1.6} />
                            {l}
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ol>
            ) : (
              <ol className="space-y-3">
                {units.map((u, i) => (
                  <li
                    key={u.index}
                    onMouseEnter={() => setSel(i)}
                    className={cn(
                      "border-l-2 bg-panel/40 py-2 pl-3 pr-3 transition-colors duration-200",
                      sel === i ? "border-gold bg-panel" : "border-success/40",
                    )}
                  >
                    <div className="flex flex-wrap items-center gap-2 font-mono text-[10.5px] text-muted">
                      <span className="text-gold">u{String(u.index + 1).padStart(2, "0")}</span>
                      <span>·</span>
                      <span>§ {u.number}</span>
                      <span>·</span>
                      <span>
                        off {u.start}–{u.end}
                      </span>
                      <span>·</span>
                      <span>{u.chars} ch</span>
                      <Tag tone="active">whole section</Tag>
                      {u.chars > MAX_CHARS && <Tag tone="repealed">LONG_UNSPLIT</Tag>}
                    </div>
                    <p className="mt-1 font-display text-[15px] italic text-paper/90">{u.marginal || "—"}</p>
                    <p className="mt-1.5 whitespace-pre-wrap font-mono text-[11.5px] leading-[1.7] text-silver/90">
                      {u.lines[0]?.text.slice(0, 420)}
                      {u.chars > 420 && <span className="text-muted"> … stored whole</span>}
                    </p>
                    <p className="mt-1.5 font-mono text-[10.5px] text-muted">
                      anchors inside: {u.anchors.proviso} proviso · {u.anchors.exception} exception ·{" "}
                      {u.anchors.explanation} explanation · {u.anchors.illustration} illustration ·{" "}
                      {u.anchors.clause} clause
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </div>

          {/* verdict */}
          <div className="border-t border-hair lg:border-l lg:border-t-0">
            <div className="border-b border-hair px-4 py-3">
              <p className="label-xs text-muted">verdict</p>
              <p className="mt-2 font-display text-[26px] leading-none text-paper">
                {mode === "window" ? (
                  <>
                    <span className="text-error">{severed}</span>
                    <span className="text-[13px] italic text-silver"> sentences severed</span>
                  </>
                ) : (
                  <>
                    <span className="text-success">0</span>
                    <span className="text-[13px] italic text-silver"> sentences severed</span>
                  </>
                )}
              </p>
            </div>
            <div className="divide-y divide-hair/70">
              {[
                ["chunks produced", mode === "window" ? String(windows.length) : String(units.length)],
                ["windows losing an anchor", mode === "window" ? String(detached) : "0"],
                [
                  "units opening on a section head",
                  `${mode === "window" ? windows.filter((w) => !w.orphaned).length : units.length} / ${
                    mode === "window" ? windows.length : units.length
                  }`,
                ],
                [
                  "length rule",
                  mode === "window" ? `≤ ${size} ch, hard cap` : `≤ ${MAX_CHARS.toLocaleString("en-IN")} ch, else whole`,
                ],
                [
                  "longest chunk produced",
                  mode === "window" ? `${size} ch` : `${longest.toLocaleString("en-IN")} ch`,
                ],
              ].map(([k, v]) => (
                <div key={k} className="flex items-baseline justify-between gap-3 px-4 py-2.5">
                  <span className="text-[12px] text-silver">{k}</span>
                  <span className="font-mono text-[11.5px] text-paper">{v}</span>
                </div>
              ))}
            </div>
            <div className="px-4 py-4">
              <p className="text-[12px] leading-[1.65] text-muted">
                {mode === "window"
                  ? "This local comparison counts sample sentences crossing a fixed-window boundary. It illustrates a possible split; it does not assess legal effect."
                  : `The grammar has no size to raise. A section longer than ${MAX_CHARS.toLocaleString("en-IN")} characters with no safe cut is kept whole and flagged LONG_UNSPLIT, because a wrong cut is worse than a long record.`}
              </p>
              <Btn
                variant="ghost"
                className="mt-3 w-full"
                onClick={() => setMode(mode === "window" ? "grammar" : "window")}
              >
                {mode === "window" ? "Show the intact units" : "Cut it up again"}
              </Btn>
              <p className="mt-3 flex items-start gap-1.5 font-mono text-[10px] leading-relaxed text-muted">
                <ShieldCheck className="mt-0.5 h-3 w-3 shrink-0 text-success/70" strokeWidth={1.6} />
                run entirely in this page. No request was made to produce these figures.
              </p>
            </div>
          </div>
        </div>
      </Panel>

      <p className="mt-3 font-mono text-[10.5px] text-muted">
        Extract: {FIXTURES.map((f) => `${f.code} §${f.section}`).join(" · ")} &mdash;{" "}
        {text.length.toLocaleString("en-IN")} characters total, from bundled sample text; not a live index record.
      </p>
    </SectionShell>
  );
}
