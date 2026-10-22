import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { Regex, Copy, Check, SlidersHorizontal, TriangleAlert, Braces, ScanLine } from "lucide-react";
import { cn } from "../utils/cn";
import { Btn, Panel, SectionShell, Tag } from "./ui";
import { GRAMMAR, byId } from "../data/corpus";
import {
  BOUNDARY_SOURCE,
  anchorMap,
  canon,
  fixedWindows,
  regexUnits
} from "../lib/text";
import { useCopy } from "../lib/hooks";
function kindOf(line) {
  const t = line.replace(/^\t+/, "");
  if (/^(?:[Ss]ection|[Ss]ec\.?|s\.)\s*\d{1,4}[A-Z]?\.\s+/.test(t) || /^\d{1,4}[A-Z]?\.\s+[^a-z\d]/.test(t)) return "section";
  if (/^[ \t]*Provided\b/i.test(t)) return "proviso";
  if (/^[ \t]*Exception/i.test(t)) return "exception";
  if (/^[ \t]*Explanation/i.test(t)) return "explanation";
  if (/^[ \t]*Illustration/i.test(t)) return "illustration";
  if (/^[ \t]*\([a-zA-Z0-9]+\)/.test(t) || /^[ \t]*[—–-]/.test(t)) return "clause";
  return "body";
}
function GrammarSection() {
  const [active, setActive] = useState("exception");
  const { copied, copy } = useCopy();
  const sample = useMemo(
    () => [byId("bns-101"), byId("bns-152")].filter(Boolean).map((s) => canon(s)).join("\n"),
    []
  );
  const lines = useMemo(() => sample.split("\n"), [sample]);
  const activeGroup = GRAMMAR.find((g) => g.group === active);
  const litKinds = useMemo(() => {
    if (!activeGroup) return /* @__PURE__ */ new Set();
    const set = new Set(activeGroup.highlights);
    if (!activeGroup.highlights.length) ["section", "clause", "proviso", "exception", "explanation", "illustration"].forEach((k) => set.add(k));
    return set;
  }, [activeGroup]);
  return /* @__PURE__ */ jsxs(
    SectionShell,
    {
      id: "grammar",
      no: "02",
      kicker: "The boundary grammar",
      title: /* @__PURE__ */ jsxs(Fragment, { children: [
        "Eight groups.",
        /* @__PURE__ */ jsx("span", { className: "block italic text-gold-light", children: "No length parameter." })
      ] }),
      lede: /* @__PURE__ */ jsx(Fragment, { children: "Chunking is usually a hyper-parameter: a token count, an overlap, a splitter. Here it is a pattern \u2014 the same eight the index runs, compiled once and run over the bare-act text. Hover a group to see what it seizes in a real section." }),
      aside: /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap gap-2", children: [
        /* @__PURE__ */ jsx(Tag, { tone: "gold", children: "flags: gm" }),
        /* @__PURE__ */ jsx(Tag, { tone: "neutral", children: "lazy body, eager boundary" }),
        /* @__PURE__ */ jsx(Tag, { tone: "neutral", children: "deterministic \xB7 idempotent" })
      ] }),
      children: [
        /* @__PURE__ */ jsxs(Panel, { className: "overflow-hidden", children: [
          /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center justify-between gap-3 border-b border-hair bg-panel-2 px-4 py-2.5", children: [
            /* @__PURE__ */ jsxs("span", { className: "flex items-center gap-2 label-xs text-silver", children: [
              /* @__PURE__ */ jsx(Regex, { className: "h-3.5 w-3.5 text-gold", strokeWidth: 1.5 }),
              "boundary.gm \u2014 compiled on this page, on the extract to the right"
            ] }),
            /* @__PURE__ */ jsxs(
              "button",
              {
                onClick: () => copy(BOUNDARY_SOURCE, "pat"),
                className: "flex items-center gap-1.5 border border-hair px-2 py-1 font-mono text-[10.5px] text-muted transition-colors hover:border-gold/60 hover:text-gold",
                children: [
                  copied === "pat" ? /* @__PURE__ */ jsx(Check, { className: "h-3 w-3 text-success" }) : /* @__PURE__ */ jsx(Copy, { className: "h-3 w-3" }),
                  copied === "pat" ? "copied" : "copy source"
                ]
              }
            )
          ] }),
          /* @__PURE__ */ jsx("div", { className: "border-b border-hair bg-cream/50 px-4 py-4", children: /* @__PURE__ */ jsxs("p", { className: "overflow-x-auto whitespace-nowrap font-mono text-[11.5px] leading-relaxed text-muted", children: [
            /* @__PURE__ */ jsx("span", { className: "text-slate-custom", children: "/" }),
            GRAMMAR.map((g) => /* @__PURE__ */ jsx(
              "button",
              {
                onMouseEnter: () => setActive(g.group),
                onFocus: () => setActive(g.group),
                onClick: () => setActive(g.group),
                className: cn(
                  "font-mono transition-colors duration-200",
                  active === g.group ? "bg-gold/15 text-gold-light" : "text-silver/70 hover:text-paper"
                ),
                children: g.pattern
              },
              g.group
            )),
            /* @__PURE__ */ jsx("span", { className: "text-slate-custom", children: "/gm" })
          ] }) }),
          /* @__PURE__ */ jsxs("div", { className: "grid lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]", children: [
            /* @__PURE__ */ jsx("ul", { className: "divide-y divide-hair border-b border-hair lg:border-b-0 lg:border-r", children: GRAMMAR.map((g) => {
              const on = active === g.group;
              return /* @__PURE__ */ jsxs(
                "li",
                {
                  onMouseEnter: () => setActive(g.group),
                  className: cn(
                    "group cursor-default px-4 py-3 transition-colors duration-200",
                    on ? "bg-gold/[0.06]" : "hover:bg-panel-2/70"
                  ),
                  children: [
                    /* @__PURE__ */ jsxs("div", { className: "flex items-center gap-2", children: [
                      /* @__PURE__ */ jsx(
                        "span",
                        {
                          className: cn(
                            "h-1.5 w-1.5 transition-colors duration-200",
                            on ? "bg-gold" : "bg-slate-custom"
                          )
                        }
                      ),
                      /* @__PURE__ */ jsxs("span", { className: cn("font-mono text-[12px]", on ? "text-gold-light" : "text-paper/85"), children: [
                        "?<",
                        g.group,
                        ">"
                      ] }),
                      /* @__PURE__ */ jsx("span", { className: "ml-auto label-xs text-muted", children: g.highlights.length ? g.highlights.join(" \xB7 ") : "structural" })
                    ] }),
                    /* @__PURE__ */ jsx(
                      "p",
                      {
                        className: cn(
                          "mt-1.5 max-w-[46ch] text-[12.5px] leading-[1.6] transition-colors duration-200",
                          on ? "text-silver" : "text-muted"
                        ),
                        children: g.role
                      }
                    )
                  ]
                },
                g.group
              );
            }) }),
            /* @__PURE__ */ jsxs("div", { className: "relative", children: [
              /* @__PURE__ */ jsxs("div", { className: "flex items-center justify-between border-b border-hair bg-panel-2 px-4 py-2.5", children: [
                /* @__PURE__ */ jsx("span", { className: "label-xs text-muted", children: "Bharatiya Nyaya Sanhita, 2023 \xB7 stored text" }),
                /* @__PURE__ */ jsxs("span", { className: "flex items-center gap-1.5 label-xs text-gold", children: [
                  /* @__PURE__ */ jsx(ScanLine, { className: "h-3 w-3", strokeWidth: 1.6 }),
                  activeGroup?.group ?? "\u2014"
                ] })
              ] }),
              /* @__PURE__ */ jsx("div", { className: "max-h-[420px] overflow-y-auto px-4 py-4", children: lines.map((l, i) => {
                const k = kindOf(l);
                const lit = litKinds.has(k);
                const dim = activeGroup && activeGroup.group !== "body" && !lit;
                return /* @__PURE__ */ jsx(
                  "p",
                  {
                    className: cn(
                      "whitespace-pre-wrap border-l-2 py-[1px] pl-2 font-mono text-[11.5px] leading-[1.75] transition-all duration-300",
                      lit ? "border-gold bg-gold/[0.09] text-gold-light" : "border-transparent",
                      dim ? "text-muted/40" : lit ? "" : "text-silver/80"
                    ),
                    children: l || " "
                  },
                  i
                );
              }) }),
              /* @__PURE__ */ jsx("div", { className: "grid grid-cols-2 gap-px border-t border-hair bg-hair sm:grid-cols-4", children: ["proviso", "exception", "explanation", "illustration"].map((k) => /* @__PURE__ */ jsxs("div", { className: "bg-panel px-3 py-2.5", children: [
                /* @__PURE__ */ jsx("p", { className: "label-xs text-muted", children: k }),
                /* @__PURE__ */ jsx("p", { className: "mt-1 font-mono text-[13px] text-paper", children: anchorMap(sample)[k] })
              ] }, k)) })
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsx("div", { className: "mt-4 grid gap-px bg-hair sm:grid-cols-3", children: [
          { t: "What it will not do", b: "It never breaks on a blank line, a heading, a page number or a token count. Those are formatting, not law." },
          { t: "What it must do", b: "It must keep 124A distinct from 124, and 304B distinct from 304 \u2014 the letter suffix is part of the identity of the provision." },
          { t: "What it yields", b: "A unit per section, filed under Act \u2192 Chapter \u2192 Part \u2192 Section \u2192 Clause, addressable by path and stampable with an offset." }
        ].map((c) => /* @__PURE__ */ jsxs("div", { className: "bg-cream px-4 py-4 transition-colors duration-300 hover:bg-panel/70", children: [
          /* @__PURE__ */ jsxs("p", { className: "flex items-center gap-2 label-xs text-gold", children: [
            /* @__PURE__ */ jsx(Braces, { className: "h-3 w-3", strokeWidth: 1.6 }),
            c.t
          ] }),
          /* @__PURE__ */ jsx("p", { className: "mt-2 text-[12.5px] leading-[1.65] text-silver", children: c.b })
        ] }, c.t)) })
      ]
    }
  );
}
function ChunkingSection() {
  const [size, setSize] = useState(300);
  const [overlap, setOverlap] = useState(64);
  const [mode, setMode] = useState("window");
  const [sel, setSel] = useState(0);
  const text = useMemo(
    () => [byId("bns-101"), byId("bns-103"), byId("bns-105"), byId("bns-152")].filter(Boolean).map((s) => canon(s)).join("\n"),
    []
  );
  const units = useMemo(() => regexUnits(text), [text]);
  const windows = useMemo(() => fixedWindows(text, size, overlap), [text, size, overlap]);
  const anchors = useMemo(() => anchorMap(text), [text]);
  const severed = windows.filter((w) => w.midSentence).length;
  const detached = windows.filter((w) => w.lostAnchors.some((l) => l.includes("carve-out") || l.includes("clause list"))).length;
  const anchorOffsets = useMemo(() => units.map((u) => u.start), [units]);
  return /* @__PURE__ */ jsx(
    SectionShell,
    {
      id: "chunking",
      no: "03",
      kicker: "The chunking test",
      title: /* @__PURE__ */ jsxs(Fragment, { children: [
        "Set the window.",
        /* @__PURE__ */ jsx("span", { className: "block italic text-gold-light", children: "Count what it cuts." })
      ] }),
      lede: /* @__PURE__ */ jsx(Fragment, { children: "Same text, same corpus, two splitters. Drive the window size the way every retrieval stack normally does and watch which provisions lose their provisos \u2014 then switch to the boundary grammar and see that the only honest chunk length is the section." }),
      aside: /* @__PURE__ */ jsx("div", { className: "grid gap-px bg-hair sm:grid-cols-2", children: [
        ["sections in extract", String(units.length)],
        ["provisos at stake", String(anchors.proviso)],
        ["exceptions at stake", String(anchors.exception)],
        ["illustrations at stake", String(anchors.illustration)]
      ].map(([k, v]) => /* @__PURE__ */ jsxs("div", { className: "bg-cream px-3 py-2.5", children: [
        /* @__PURE__ */ jsx("p", { className: "label-xs text-muted", children: k }),
        /* @__PURE__ */ jsx("p", { className: "mt-1 font-display text-[22px] leading-none text-gold-light", children: v })
      ] }, k)) }),
      children: /* @__PURE__ */ jsxs(Panel, { className: "overflow-hidden", children: [
        /* @__PURE__ */ jsxs("div", { className: "flex flex-col gap-4 border-b border-hair bg-panel-2 px-4 py-3.5 lg:flex-row lg:items-center", children: [
          /* @__PURE__ */ jsx("div", { className: "flex items-center gap-0 border border-hair", children: [
            ["window", "Fixed window + overlap"],
            ["grammar", "Boundary grammar"]
          ].map(([m, label]) => /* @__PURE__ */ jsx(
            "button",
            {
              onClick: () => setMode(m),
              className: cn(
                "px-3 py-2 label-xs transition-colors duration-200",
                mode === m ? "bg-gold text-ink" : "text-silver hover:bg-panel hover:text-gold-light"
              ),
              children: label
            },
            m
          )) }),
          /* @__PURE__ */ jsxs("div", { className: cn("flex flex-1 flex-wrap items-center gap-5 transition-opacity duration-300", mode === "grammar" && "pointer-events-none opacity-30"), children: [
            /* @__PURE__ */ jsxs("label", { className: "flex min-w-[190px] flex-1 items-center gap-3", children: [
              /* @__PURE__ */ jsxs("span", { className: "flex items-center gap-1.5 label-xs text-muted", children: [
                /* @__PURE__ */ jsx(SlidersHorizontal, { className: "h-3 w-3", strokeWidth: 1.6 }),
                "window"
              ] }),
              /* @__PURE__ */ jsx(
                "input",
                {
                  type: "range",
                  min: 120,
                  max: 720,
                  step: 20,
                  value: size,
                  onChange: (e) => setSize(+e.target.value),
                  className: "h-px flex-1 cursor-ew-resize appearance-none bg-slate-custom accent-[#c9a962] [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:bg-gold"
                }
              ),
              /* @__PURE__ */ jsxs("span", { className: "w-14 font-mono text-[11px] text-paper", children: [
                size,
                " ch"
              ] })
            ] }),
            /* @__PURE__ */ jsxs("label", { className: "flex min-w-[190px] flex-1 items-center gap-3", children: [
              /* @__PURE__ */ jsxs("span", { className: "flex items-center gap-1.5 label-xs text-muted", children: [
                /* @__PURE__ */ jsx(SlidersHorizontal, { className: "h-3 w-3", strokeWidth: 1.6 }),
                "overlap"
              ] }),
              /* @__PURE__ */ jsx(
                "input",
                {
                  type: "range",
                  min: 0,
                  max: 200,
                  step: 8,
                  value: overlap,
                  onChange: (e) => setOverlap(+e.target.value),
                  className: "h-px flex-1 cursor-ew-resize appearance-none bg-slate-custom accent-[#c9a962] [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:bg-gold"
                }
              ),
              /* @__PURE__ */ jsxs("span", { className: "w-14 font-mono text-[11px] text-paper", children: [
                overlap,
                " ch"
              ] })
            ] })
          ] }),
          /* @__PURE__ */ jsx("div", { className: cn("font-mono text-[11px] transition-opacity", mode === "grammar" ? "text-silver" : "text-muted"), children: mode === "window" ? `${windows.length} windows` : `${units.length} units` })
        ] }),
        /* @__PURE__ */ jsxs("div", { className: "border-b border-hair px-4 py-4", children: [
          /* @__PURE__ */ jsx("div", { className: "flex h-12 w-full overflow-hidden gap-px", children: mode === "window" ? windows.map((w, i) => /* @__PURE__ */ jsx(
            "button",
            {
              onMouseEnter: () => setSel(i),
              onClick: () => setSel(i),
              style: { flexGrow: Math.max(1, w.text.length) },
              className: cn(
                "relative min-w-[6px] border-t-2 transition-colors duration-200",
                w.lostAnchors.length ? "border-error/80 bg-error/[0.16] hover:bg-error/25" : "border-slate-custom bg-slate-custom/20 hover:bg-slate-custom/35",
                sel === i && "bg-gold/25 border-gold"
              ),
              title: `window ${w.index + 1} \xB7 ${w.text.length} chars${w.lostAnchors.length ? ` \xB7 ${w.lostAnchors[0]}` : ""}`
            },
            i
          )) : units.map((u, i) => /* @__PURE__ */ jsx(
            "button",
            {
              onMouseEnter: () => setSel(i),
              onClick: () => setSel(i),
              style: { flexGrow: Math.max(1, u.text.length) },
              className: cn(
                "relative min-w-[6px] border-t-2 bg-success/[0.13] transition-colors duration-200",
                sel === i ? "border-gold bg-gold/20" : "border-success/60 hover:bg-success/20"
              ),
              title: `\xA7 ${u.number} \xB7 ${u.text.length} chars \xB7 intact`,
              children: /* @__PURE__ */ jsxs("span", { className: "absolute inset-x-0 top-1 truncate px-1 text-left font-mono text-[9px] text-paper/70", children: [
                "\xA7",
                u.number
              ] })
            },
            i
          )) }),
          /* @__PURE__ */ jsx("div", { className: "relative mt-1 h-3", children: mode === "window" && anchorOffsets.filter((o) => o < text.length).map((o, i) => /* @__PURE__ */ jsx(
            "span",
            {
              className: "absolute top-0 h-3 w-px bg-gold",
              style: { left: `${o / text.length * 100}%` },
              title: "a real section boundary falls inside the tape"
            },
            i
          )) })
        ] }),
        /* @__PURE__ */ jsxs("div", { className: "grid lg:grid-cols-[minmax(0,1fr)_300px]", children: [
          /* @__PURE__ */ jsx("div", { className: "max-h-[400px] overflow-y-auto px-4 py-4", children: mode === "window" ? /* @__PURE__ */ jsx("ol", { className: "space-y-3", children: windows.map((w, i) => /* @__PURE__ */ jsxs(
            "li",
            {
              onMouseEnter: () => setSel(i),
              className: cn(
                "border-l-2 bg-panel/40 py-2 pl-3 pr-3 transition-colors duration-200",
                sel === i ? "border-gold bg-panel" : "border-hair"
              ),
              children: [
                /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-2 font-mono text-[10.5px] text-muted", children: [
                  /* @__PURE__ */ jsxs("span", { className: "text-silver", children: [
                    "w",
                    String(w.index + 1).padStart(2, "0")
                  ] }),
                  /* @__PURE__ */ jsx("span", { children: "\xB7" }),
                  /* @__PURE__ */ jsxs("span", { children: [
                    "off ",
                    w.start,
                    "\u2013",
                    w.end
                  ] }),
                  /* @__PURE__ */ jsx("span", { children: "\xB7" }),
                  /* @__PURE__ */ jsxs("span", { children: [
                    w.text.length,
                    " ch"
                  ] }),
                  !w.orphaned ? /* @__PURE__ */ jsx(Tag, { tone: "neutral", children: "opens on anchor" }) : /* @__PURE__ */ jsx(Tag, { tone: "muted", children: "no anchor" })
                ] }),
                /* @__PURE__ */ jsxs("p", { className: "mt-1.5 whitespace-pre-wrap font-mono text-[11.5px] leading-[1.7] text-silver/90", children: [
                  w.text.slice(0, 320),
                  w.text.length > 320 && /* @__PURE__ */ jsx("span", { className: "text-muted", children: " \u2026" }),
                  w.midSentence && /* @__PURE__ */ jsx("span", { className: "text-error", children: "\u25AE" })
                ] }),
                w.lostAnchors.length > 0 && /* @__PURE__ */ jsx("ul", { className: "mt-1.5 flex flex-wrap gap-x-4 gap-y-1", children: w.lostAnchors.map((l) => /* @__PURE__ */ jsxs("li", { className: "flex items-center gap-1.5 text-[11px] text-error/85", children: [
                  /* @__PURE__ */ jsx(TriangleAlert, { className: "h-3 w-3", strokeWidth: 1.6 }),
                  l
                ] }, l)) })
              ]
            },
            i
          )) }) : /* @__PURE__ */ jsx("ol", { className: "space-y-3", children: units.map((u, i) => /* @__PURE__ */ jsxs(
            "li",
            {
              onMouseEnter: () => setSel(i),
              className: cn(
                "border-l-2 bg-panel/40 py-2 pl-3 pr-3 transition-colors duration-200",
                sel === i ? "border-gold bg-panel" : "border-success/40"
              ),
              children: [
                /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-2 font-mono text-[10.5px] text-muted", children: [
                  /* @__PURE__ */ jsxs("span", { className: "text-gold", children: [
                    "u",
                    String(u.index + 1).padStart(2, "0")
                  ] }),
                  /* @__PURE__ */ jsx("span", { children: "\xB7" }),
                  /* @__PURE__ */ jsxs("span", { children: [
                    "\xA7 ",
                    u.number
                  ] }),
                  /* @__PURE__ */ jsx("span", { children: "\xB7" }),
                  /* @__PURE__ */ jsxs("span", { children: [
                    "off ",
                    u.start,
                    "\u2013",
                    u.end
                  ] }),
                  /* @__PURE__ */ jsx("span", { children: "\xB7" }),
                  /* @__PURE__ */ jsxs("span", { children: [
                    u.text.length,
                    " ch"
                  ] }),
                  /* @__PURE__ */ jsx(Tag, { tone: "active", children: "whole section" })
                ] }),
                /* @__PURE__ */ jsx("p", { className: "mt-1 font-display text-[15px] italic text-paper/90", children: u.marginal }),
                /* @__PURE__ */ jsxs("p", { className: "mt-1.5 whitespace-pre-wrap font-mono text-[11.5px] leading-[1.7] text-silver/90", children: [
                  u.text.slice(0, 400),
                  u.text.length > 400 && /* @__PURE__ */ jsx("span", { className: "text-muted", children: " \u2026 printed whole, stored whole" })
                ] }),
                /* @__PURE__ */ jsxs("p", { className: "mt-1.5 font-mono text-[10.5px] text-muted", children: [
                  "anchors inside: ",
                  u.anchors.proviso,
                  " proviso \xB7 ",
                  u.anchors.exception,
                  " exception \xB7",
                  " ",
                  u.anchors.explanation,
                  " explanation \xB7 ",
                  u.anchors.illustration,
                  " illustration \xB7",
                  " ",
                  u.anchors.clause,
                  " clause"
                ] })
              ]
            },
            i
          )) }) }),
          /* @__PURE__ */ jsxs("div", { className: "border-t border-hair lg:border-l lg:border-t-0", children: [
            /* @__PURE__ */ jsxs("div", { className: "border-b border-hair px-4 py-3", children: [
              /* @__PURE__ */ jsx("p", { className: "label-xs text-muted", children: "verdict" }),
              /* @__PURE__ */ jsx("p", { className: "mt-2 font-display text-[26px] leading-none text-paper", children: mode === "window" ? /* @__PURE__ */ jsxs(Fragment, { children: [
                /* @__PURE__ */ jsx("span", { className: "text-error", children: severed }),
                /* @__PURE__ */ jsx("span", { className: "text-[13px] italic text-silver", children: " sentences severed" })
              ] }) : /* @__PURE__ */ jsxs(Fragment, { children: [
                /* @__PURE__ */ jsx("span", { className: "text-success", children: "0" }),
                /* @__PURE__ */ jsx("span", { className: "text-[13px] italic text-silver", children: " sentences severed" })
              ] }) })
            ] }),
            /* @__PURE__ */ jsx("div", { className: "divide-y divide-hair/70", children: [
              ["chunks produced", mode === "window" ? String(windows.length) : String(units.length)],
              ["carve-outs detached", mode === "window" ? String(detached) : "0"],
              ["units opening on an anchor", `${mode === "window" ? windows.filter((w) => !w.orphaned).length : units.length} / ${mode === "window" ? windows.length : units.length}`],
              ["longest unit vs window", mode === "window" ? `${size} ch cap` : `${Math.max(...units.map((u) => u.text.length), 0)} ch, uncapped`]
            ].map(([k, v]) => /* @__PURE__ */ jsxs("div", { className: "flex items-baseline justify-between gap-3 px-4 py-2.5", children: [
              /* @__PURE__ */ jsx("span", { className: "text-[12px] text-silver", children: k }),
              /* @__PURE__ */ jsx("span", { className: "font-mono text-[11.5px] text-paper", children: v })
            ] }, k)) }),
            /* @__PURE__ */ jsxs("div", { className: "px-4 py-4", children: [
              /* @__PURE__ */ jsx("p", { className: "text-[12px] leading-[1.65] text-muted", children: mode === "window" ? "Every cut below is a sentence a court would have to read without its condition attached. Raise the window and the count falls; it never reaches zero." : "The grammar has no size to raise. A section of sixty pages is one unit, because that is what a section is." }),
              /* @__PURE__ */ jsx(
                Btn,
                {
                  variant: "ghost",
                  className: "mt-3 w-full",
                  onClick: () => setMode(mode === "window" ? "grammar" : "window"),
                  children: mode === "window" ? "Show the intact units" : "Cut it up again"
                }
              )
            ] })
          ] })
        ] })
      ] })
    }
  );
}
export {
  ChunkingSection,
  GrammarSection
};
