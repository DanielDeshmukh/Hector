import { useMemo, useState } from "react";
import { Regex, Copy, Check, SlidersHorizontal, TriangleAlert, Braces, ScanLine } from "lucide-react";
import { cn } from "../utils/cn";
import { Btn, Panel, SectionShell, Tag } from "./ui";
import { GRAMMAR, byId, type AnchorKind } from "../data/corpus";
import {
  BOUNDARY_SOURCE,
  anchorMap,
  canon,
  fixedWindows,
  regexUnits,
} from "../lib/text";
import { useCopy } from "../lib/hooks";

/* =================================================================== *
 * 02 — the grammar
 * =================================================================== */

type LineKind = AnchorKind | "body" | "head";

function kindOf(line: string): LineKind {
  const t = line.replace(/^\t+/, "");
  if (/^[ \t]*\d{1,4}[A-Za-z]?\.\s/.test(t) || /^[ \t]*[Aa]rticle\s\d/.test(t)) return "section";
  if (/^[ \t]*Provided\b/.test(t)) return "proviso";
  if (/^[ \t]*Exception\b/.test(t)) return "exception";
  if (/^[ \t]*Explanation\b/.test(t)) return "explanation";
  if (/^[ \t]*Illustration\b/.test(t)) return "illustration";
  if (/^[ \t]*[—–-]\s*\(|^[ \t]*[—–-]/.test(t)) return "clause";
  return "body";
}

export function GrammarSection() {
  const [active, setActive] = useState<string | null>("exception");
  const { copied, copy } = useCopy();

  const sample = useMemo(
    () => [byId("bns-102"), byId("bns-152")].filter(Boolean).map((s) => canon(s!)).join("\n"),
    [],
  );
  const lines = useMemo(() => sample.split("\n"), [sample]);
  const activeGroup = GRAMMAR.find((g) => g.group === active);
  const litKinds = useMemo(() => {
    if (!activeGroup) return new Set<LineKind>();
    const set = new Set<LineKind>(activeGroup.highlights);
    if (!activeGroup.highlights.length) (["section", "clause", "proviso", "exception", "explanation", "illustration"] as LineKind[]).forEach((k) => set.add(k));
    if (activeGroup.group === "stop") {
      set.clear();
      set.add("section");
    }
    return set;
  }, [activeGroup]);

  return (
    <SectionShell
      id="grammar"
      no="02"
      kicker="The boundary grammar"
      title={
        <>
          Nine groups.
          <span className="block italic text-gold-light">No length parameter.</span>
        </>
      }
      lede={
        <>
          Chunking is usually a hyper-parameter: a token count, an overlap, a splitter. Here it is a
          pattern — compiled once per statute and run over the bare-act text. Hover a group to see what
          it seizes in a real section.
        </>
      }
      aside={
        <div className="flex flex-wrap gap-2">
          <Tag tone="gold">flags: g</Tag>
          <Tag tone="neutral">lazy body, eager boundary</Tag>
          <Tag tone="neutral">deterministic · idempotent</Tag>
        </div>
      }
    >
      <Panel className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hair bg-panel-2 px-4 py-2.5">
          <span className="flex items-center gap-2 label-xs text-silver">
            <Regex className="h-3.5 w-3.5 text-gold" strokeWidth={1.5} />
            boundary.g — compiled on this page, on the extract to the right
          </span>
          <button
            onClick={() => copy(BOUNDARY_SOURCE, "pat")}
            className="flex items-center gap-1.5 border border-hair px-2 py-1 font-mono text-[10.5px] text-muted transition-colors hover:border-gold/60 hover:text-gold"
          >
            {copied === "pat" ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" />}
            {copied === "pat" ? "copied" : "copy source"}
          </button>
        </div>

        {/* master pattern */}
        <div className="border-b border-hair bg-cream/50 px-4 py-4">
          <p className="overflow-x-auto whitespace-nowrap font-mono text-[11.5px] leading-relaxed text-muted">
            <span className="text-slate-custom">/</span>
            {GRAMMAR.map((g) => (
              <button
                key={g.group}
                onMouseEnter={() => setActive(g.group)}
                onFocus={() => setActive(g.group)}
                onClick={() => setActive(g.group)}
                className={cn(
                  "font-mono transition-colors duration-200",
                  active === g.group ? "bg-gold/15 text-gold-light" : "text-silver/70 hover:text-paper",
                )}
              >
                {g.pattern}
              </button>
            ))}
            <span className="text-slate-custom">/g</span>
          </p>
        </div>

        <div className="grid lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          {/* groups */}
          <ul className="divide-y divide-hair border-b border-hair lg:border-b-0 lg:border-r">
            {GRAMMAR.map((g) => {
              const on = active === g.group;
              return (
                <li
                  key={g.group}
                  onMouseEnter={() => setActive(g.group)}
                  className={cn(
                    "group cursor-default px-4 py-3 transition-colors duration-200",
                    on ? "bg-gold/[0.06]" : "hover:bg-panel-2/70",
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "h-1.5 w-1.5 transition-colors duration-200",
                        on ? "bg-gold" : "bg-slate-custom",
                      )}
                    />
                    <span className={cn("font-mono text-[12px]", on ? "text-gold-light" : "text-paper/85")}>
                      ?&lt;{g.group}&gt;
                    </span>
                    <span className="ml-auto label-xs text-muted">
                      {g.highlights.length ? g.highlights.join(" · ") : "structural"}
                    </span>
                  </div>
                  <p
                    className={cn(
                      "mt-1.5 max-w-[46ch] text-[12.5px] leading-[1.6] transition-colors duration-200",
                      on ? "text-silver" : "text-muted",
                    )}
                  >
                    {g.role}
                  </p>
                </li>
              );
            })}
          </ul>

          {/* sample */}
          <div className="relative">
            <div className="flex items-center justify-between border-b border-hair bg-panel-2 px-4 py-2.5">
              <span className="label-xs text-muted">Bharatiya Nyaya Sanhita, 2023 · stored text</span>
              <span className="flex items-center gap-1.5 label-xs text-gold">
                <ScanLine className="h-3 w-3" strokeWidth={1.6} />
                {activeGroup?.group ?? "—"}
              </span>
            </div>
            <div className="max-h-[420px] overflow-y-auto px-4 py-4">
              {lines.map((l, i) => {
                const k = kindOf(l);
                const lit = litKinds.has(k);
                const dim = activeGroup && activeGroup.group !== "body" && !lit;
                return (
                  <p
                    key={i}
                    className={cn(
                      "whitespace-pre-wrap border-l-2 py-[1px] pl-2 font-mono text-[11.5px] leading-[1.75] transition-all duration-300",
                      lit ? "border-gold bg-gold/[0.09] text-gold-light" : "border-transparent",
                      dim ? "text-muted/40" : lit ? "" : "text-silver/80",
                    )}
                  >
                    {l || " "}
                  </p>
                );
              })}
            </div>
            <div className="grid grid-cols-2 gap-px border-t border-hair bg-hair sm:grid-cols-4">
              {(["proviso", "exception", "explanation", "illustration"] as const).map((k) => (
                <div key={k} className="bg-panel px-3 py-2.5">
                  <p className="label-xs text-muted">{k}</p>
                  <p className="mt-1 font-mono text-[13px] text-paper">
                    {anchorMap(sample)[k]}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Panel>

      <div className="mt-4 grid gap-px bg-hair sm:grid-cols-3">
        {[
          { t: "What it will not do", b: "It never breaks on a blank line, a heading, a page number or a token count. Those are formatting, not law." },
          { t: "What it must do", b: "It must keep 124A distinct from 124, and 304B distinct from 304 — the letter suffix is part of the identity of the provision." },
          { t: "What it yields", b: "A unit per section, filed under Act → Chapter → Part → Section → Clause, addressable by path and stampable with an offset." },
        ].map((c) => (
          <div key={c.t} className="bg-cream px-4 py-4 transition-colors duration-300 hover:bg-panel/70">
            <p className="flex items-center gap-2 label-xs text-gold">
              <Braces className="h-3 w-3" strokeWidth={1.6} />
              {c.t}
            </p>
            <p className="mt-2 text-[12.5px] leading-[1.65] text-silver">{c.b}</p>
          </div>
        ))}
      </div>
    </SectionShell>
  );
}

/* =================================================================== *
 * 03 — chunking lab
 * =================================================================== */

export function ChunkingSection() {
  const [size, setSize] = useState(300);
  const [overlap, setOverlap] = useState(64);
  const [mode, setMode] = useState<"window" | "grammar">("window");
  const [sel, setSel] = useState(0);

  const text = useMemo(
    () =>
      [byId("bns-102"), byId("bns-103"), byId("bns-104"), byId("bns-152")]
        .filter(Boolean)
        .map((s) => canon(s!))
        .join("\n"),
    [],
  );

  const units = useMemo(() => regexUnits(text), [text]);
  const windows = useMemo(() => fixedWindows(text, size, overlap), [text, size, overlap]);
  const anchors = useMemo(() => anchorMap(text), [text]);

  const severed = windows.filter((w) => w.midSentence).length;
  const detached = windows.filter((w) => w.lostAnchors.some((l) => l.includes("carve-out") || l.includes("clause list"))).length;
  const anchorOffsets = useMemo(() => units.map((u) => u.start), [units]);

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
          Same text, same corpus, two splitters. Drive the window size the way every retrieval stack
          normally does and watch which provisions lose their provisos — then switch to the boundary
          grammar and see that the only honest chunk length is the section.
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
            {(
              [
                ["window", "Fixed window + overlap"],
                ["grammar", "Boundary grammar"],
              ] as const
            ).map(([m, label]) => (
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

          <div className={cn("flex flex-1 flex-wrap items-center gap-5 transition-opacity duration-300", mode === "grammar" && "pointer-events-none opacity-30")}>
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
          <div className={cn("font-mono text-[11px] transition-opacity", mode === "grammar" ? "text-silver" : "text-muted")}>
            {mode === "window" ? `${windows.length} windows` : `${units.length} units`}
          </div>
        </div>

        {/* tape */}
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
                      sel === i && "bg-gold/25 border-gold",
                    )}
                    title={`window ${w.index + 1} · ${w.text.length} chars${w.lostAnchors.length ? ` · ${w.lostAnchors[0]}` : ""}`}
                  />
                ))
              : units.map((u, i) => (
                  <button
                    key={i}
                    onMouseEnter={() => setSel(i)}
                    onClick={() => setSel(i)}
                    style={{ flexGrow: Math.max(1, u.text.length) }}
                    className={cn(
                      "relative min-w-[6px] border-t-2 bg-success/[0.13] transition-colors duration-200",
                      sel === i ? "border-gold bg-gold/20" : "border-success/60 hover:bg-success/20",
                    )}
                    title={`§ ${u.number} · ${u.text.length} chars · intact`}
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
                      <span>off {w.start}–{w.end}</span>
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
                    key={i}
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
                      <span>off {u.start}–{u.end}</span>
                      <span>·</span>
                      <span>{u.text.length} ch</span>
                      <Tag tone="active">whole section</Tag>
                    </div>
                    <p className="mt-1 font-display text-[15px] italic text-paper/90">{u.marginal}</p>
                    <p className="mt-1.5 whitespace-pre-wrap font-mono text-[11.5px] leading-[1.7] text-silver/90">
                      {u.text.slice(0, 400)}
                      {u.text.length > 400 && <span className="text-muted"> … printed whole, stored whole</span>}
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

          {/* verdict rail */}
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
                ["carve-outs detached", mode === "window" ? String(detached) : "0"],
                ["units opening on an anchor", `${mode === "window" ? windows.filter((w) => !w.orphaned).length : units.length} / ${mode === "window" ? windows.length : units.length}`],
                ["longest unit vs window", mode === "window" ? `${size} ch cap` : `${Math.max(...units.map((u) => u.text.length), 0)} ch, uncapped`],
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
                  ? "Every cut below is a sentence a court would have to read without its condition attached. Raise the window and the count falls; it never reaches zero."
                  : "The grammar has no size to raise. A section of sixty pages is one unit, because that is what a section is."}
              </p>
              <Btn
                variant="ghost"
                className="mt-3 w-full"
                onClick={() => setMode(mode === "window" ? "grammar" : "window")}
              >
                {mode === "window" ? "Show the intact units" : "Cut it up again"}
              </Btn>
            </div>
          </div>
        </div>
      </Panel>
    </SectionShell>
  );
}
