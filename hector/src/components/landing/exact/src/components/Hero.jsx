import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowRight, Hash, Terminal, TriangleAlert } from "lucide-react";
import { cn } from "../utils/cn";
import { Btn, Reveal, Tag } from "./ui";
import { Ticker } from "./Chrome";
import { CORPUS, MAPPINGS } from "../data/corpus";
import { TOTAL_ACTS, ACT_CATEGORIES, REPEAL_LINKS } from "../data/acts";
import { canon, digest, parseQuery, retrieve, SAMPLE_QUERY } from "../lib/text";
const SUGGESTIONS = [
  "Section 302 IPC punishment for murder",
  "BNS section corresponding to 420 IPC",
  "Inherent powers of the High Court BNSS",
  "NDPS Section 37 bail commercial quantity"
];
const STEPS = [
  "parse query \xB7 extract \xA7 / act identity",
  "compile boundary grammar \xB7 9 groups",
  "resolve statutory identity before text",
  "open unit \xB7 provisos, exceptions, illustrations attached",
  "stamp citations \xB7 char offsets on every sentence"
];
function StatutoryText({ text }) {
  const lines = text.split("\n");
  return /* @__PURE__ */ jsx("div", { className: "font-mono text-[12.5px] leading-[1.85] text-paper/90 sm:text-[13px]", children: lines.map((l, i) => {
    const trimmed = l.trimStart();
    const kind = /^Provided\b/.test(trimmed) ? "proviso" : /^(Exception|Explanation|Illustration)/.test(trimmed) ? "gloss" : /^\d{1,4}[A-Za-z]?\.\s|^[Aa]rticle\s/.test(trimmed) ? "head" : "body";
    return /* @__PURE__ */ jsx(
      "p",
      {
        className: cn(
          "whitespace-pre-wrap",
          kind === "head" && "text-gold",
          kind === "proviso" && "text-warning/90 italic",
          kind === "gloss" && "text-info/85",
          kind === "body" && "pl-0 text-silver/95"
        ),
        children: kind === "head" ? /* @__PURE__ */ jsxs("span", { className: "font-semibold tracking-tight", children: [
          trimmed.split(".")[0],
          ".",
          /* @__PURE__ */ jsxs("span", { className: "text-paper/90 font-normal italic", children: [
            " ",
            trimmed.split(".").slice(1).join(".").trim()
          ] })
        ] }) : kind === "gloss" ? /* @__PURE__ */ jsxs(Fragment, { children: [
          /* @__PURE__ */ jsx("span", { className: "text-paper/45", children: "	" }),
          /* @__PURE__ */ jsxs("span", { className: "font-medium", children: [
            trimmed.split(".\u2014")[0],
            ".\u2014"
          ] }),
          /* @__PURE__ */ jsx("span", { className: "text-silver/90", children: trimmed.split(".\u2014").slice(1).join(".\u2014") })
        ] }) : /* @__PURE__ */ jsxs(Fragment, { children: [
          kind === "proviso" && /* @__PURE__ */ jsx("span", { children: "	" }),
          trimmed
        ] })
      },
      i
    );
  }) });
}
function Hero() {
  const [q, setQ] = useState("");
  const [phase, setPhase] = useState("idle");
  const [step, setStep] = useState(0);
  const [hits, setHits] = useState([]);
  const [openHit, setOpenHit] = useState(0);
  const timers = useRef([]);
  const clearTimers = () => {
    timers.current.forEach((t) => window.clearTimeout(t));
    timers.current = [];
  };
  const run = useCallback((query) => {
    const value = query.trim();
    if (!value) return;
    clearTimers();
    setPhase("running");
    setStep(0);
    setOpenHit(0);
    STEPS.forEach((_, i) => {
      timers.current.push(
        window.setTimeout(() => setStep(i + 1), 105 + i * 92)
      );
    });
    timers.current.push(
      window.setTimeout(
        () => {
          setHits(retrieve(value, 3));
          setPhase("done");
        },
        105 + STEPS.length * 92
      )
    );
  }, []);
  useEffect(() => {
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const start = Date.now();
    let raf = 0;
    if (reduce) {
      setQ(SAMPLE_QUERY);
      run(SAMPLE_QUERY);
    } else {
      const tick = () => {
        const elapsed = Date.now() - start - 700;
        if (elapsed < 0) {
          raf = requestAnimationFrame(tick);
          return;
        }
        const n = Math.min(SAMPLE_QUERY.length, Math.floor(elapsed / 26));
        setQ(SAMPLE_QUERY.slice(0, n));
        if (n < SAMPLE_QUERY.length) raf = requestAnimationFrame(tick);
        else run(SAMPLE_QUERY);
      };
      raf = requestAnimationFrame(tick);
    }
    return () => {
      cancelAnimationFrame(raf);
      clearTimers();
    };
  }, [run]);
  const parsed = parseQuery(q);
  const hit = hits[openHit];
  return /* @__PURE__ */ jsxs("section", { id: "top", className: "relative", children: [
    /* @__PURE__ */ jsx("div", { className: "mx-auto w-full max-w-[1400px] px-5 pb-12 pt-24 sm:px-8 md:pt-28 lg:pb-16 lg:pt-32", children: /* @__PURE__ */ jsxs("div", { className: "grid gap-12 lg:grid-cols-12 lg:gap-10", children: [
      /* @__PURE__ */ jsxs("div", { className: "lg:col-span-5 lg:pr-10", children: [
        /* @__PURE__ */ jsx(Reveal, { y: false, children: /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-3 label-xs text-muted", children: [
          /* @__PURE__ */ jsx("span", { className: "text-gold", children: "Act No. IV of 2025" }),
          /* @__PURE__ */ jsx("span", { className: "h-3 w-px bg-hair" }),
          /* @__PURE__ */ jsx("span", { children: "In force" }),
          /* @__PURE__ */ jsx("span", { className: "h-3 w-px bg-hair" }),
          /* @__PURE__ */ jsx("span", { children: "Ref. HECTOR/RET/38" })
        ] }) }),
        /* @__PURE__ */ jsx(Reveal, { delay: 70, children: /* @__PURE__ */ jsxs("h1", { className: "mt-7 font-display text-[clamp(2.9rem,7.4vw,5.9rem)] font-medium leading-[0.87] tracking-[-0.035em] text-paper", children: [
          "A section",
          /* @__PURE__ */ jsx("span", { className: "block pl-[0.06em]", children: "is the unit." }),
          /* @__PURE__ */ jsx("span", { className: "mt-2 block font-display text-[clamp(1.15rem,2.5vw,1.95rem)] italic leading-tight tracking-[-0.01em] text-gold-light", children: "Everything else is a fragment." })
        ] }) }),
        /* @__PURE__ */ jsx(Reveal, { delay: 140, children: /* @__PURE__ */ jsxs("p", { className: "mt-8 max-w-[46ch] text-[15.5px] leading-[1.78] text-silver", children: [
          "Hector is a retrieval instrument over ",
          /* @__PURE__ */ jsx("span", { className: "text-paper", children: "38 Indian bare acts" }),
          ". The corpus is not sliced to fit a window \u2014 it is divided by one deterministic regular expression that recognises a single boundary: the printed section number. Provisos, exceptions, explanations and illustrations therefore travel with the rule they qualify, and every sentence returned can be traced to a clause and a character offset."
        ] }) }),
        /* @__PURE__ */ jsx(Reveal, { delay: 200, children: /* @__PURE__ */ jsx("div", { className: "mt-8 border-l border-gold/40 bg-panel/40 py-4 pl-5 pr-4", children: /* @__PURE__ */ jsxs("p", { className: "font-mono text-[12.5px] leading-[1.9] text-silver/90", children: [
          /* @__PURE__ */ jsx("span", { className: "text-gold", children: "2. Definitions." }),
          "\u2014In this instrument, unless the context otherwise requires,\u2014",
          /* @__PURE__ */ jsx("br", {}),
          /* @__PURE__ */ jsxs("span", { className: "pl-4", children: [
            /* @__PURE__ */ jsx("span", { className: "text-gold/80", children: "(a)" }),
            " \u201Cunit\u201D means the whole of a section, from its number to the next;"
          ] }),
          /* @__PURE__ */ jsx("br", {}),
          /* @__PURE__ */ jsxs("span", { className: "pl-4", children: [
            /* @__PURE__ */ jsx("span", { className: "text-gold/80", children: "(b)" }),
            " \u201Cwindow\u201D means any fragment produced otherwise, and is not admissible."
          ] })
        ] }) }) }),
        /* @__PURE__ */ jsx(Reveal, { delay: 260, children: /* @__PURE__ */ jsxs("div", { className: "mt-8 flex flex-wrap items-center gap-3", children: [
          /* @__PURE__ */ jsx("a", { href: "#corpus", children: /* @__PURE__ */ jsxs(Btn, { children: [
            "Browse the 38 acts",
            /* @__PURE__ */ jsx(ArrowRight, { className: "h-3 w-3 transition-transform duration-200 group-hover:translate-x-0.5" })
          ] }) }),
          /* @__PURE__ */ jsx("a", { href: "#compare", children: /* @__PURE__ */ jsx(Btn, { variant: "ghost", children: "Compare IPC \u21C4 BNS" }) }),
          /* @__PURE__ */ jsx("a", { href: "#grammar", children: /* @__PURE__ */ jsx(Btn, { variant: "quiet", className: "underline-offset-4 hover:underline", children: "Read the grammar" }) })
        ] }) }),
        /* @__PURE__ */ jsxs(Reveal, { delay: 320, children: [
          /* @__PURE__ */ jsxs("div", { className: "mt-9 flex flex-wrap gap-2", children: [
            /* @__PURE__ */ jsx(Tag, { tone: "gold", children: "regex chunking" }),
            /* @__PURE__ */ jsx(Tag, { tone: "neutral", children: "section comparison" }),
            /* @__PURE__ */ jsx(Tag, { tone: "neutral", children: "batch \u2264 50" }),
            /* @__PURE__ */ jsxs(Tag, { tone: "active", children: [
              /* @__PURE__ */ jsx("span", { className: "h-1 w-1 bg-success" }),
              " offset-level citation"
            ] })
          ] }),
          /* @__PURE__ */ jsxs("p", { className: "mt-5 max-w-[52ch] font-mono text-[10.5px] leading-[1.7] text-muted", children: [
            "HECTOR \u2014 Hierarchical Evaluation of Civil-Criminal Textual\u2019s",
            " ",
            /* @__PURE__ */ jsx("span", { className: "text-silver/80", children: "Orchestrator & Retrieval" }),
            " \xB7 index of 38 bare acts \xB7 statutory text only"
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsx("div", { className: "lg:col-span-7", children: /* @__PURE__ */ jsx(Reveal, { delay: 120, children: /* @__PURE__ */ jsxs("div", { className: "relative border border-hair bg-panel shadow-[0_40px_120px_-40px_rgba(0,0,0,0.9)]", children: [
        /* @__PURE__ */ jsxs("div", { className: "flex items-center justify-between gap-3 border-b border-hair bg-panel-2 px-4 py-2.5", children: [
          /* @__PURE__ */ jsxs("div", { className: "flex items-center gap-2.5 label-xs text-silver", children: [
            /* @__PURE__ */ jsx(Terminal, { className: "h-3.5 w-3.5 text-gold", strokeWidth: 1.5 }),
            "hector://index/query"
          ] }),
          /* @__PURE__ */ jsxs("div", { className: "flex items-center gap-3 label-xs text-muted", children: [
            /* @__PURE__ */ jsx("span", { className: "hidden sm:inline", children: "grammar 4.2 \xB7 gm" }),
            /* @__PURE__ */ jsx("span", { className: cn("h-1.5 w-1.5", phase === "running" ? "bg-warning animate-pulse" : "bg-success") }),
            phase === "running" ? "resolving" : "ready"
          ] })
        ] }),
        /* @__PURE__ */ jsxs(
          "form",
          {
            onSubmit: (e) => {
              e.preventDefault();
              run(q);
            },
            className: "flex items-stretch gap-0 border-b border-hair",
            children: [
              /* @__PURE__ */ jsx("span", { className: "grid place-items-center pl-4 pr-2 font-mono text-[13px] text-gold", children: "\xA7" }),
              /* @__PURE__ */ jsx(
                "input",
                {
                  value: q,
                  onChange: (e) => setQ(e.target.value),
                  spellCheck: false,
                  "aria-label": "Ask the statutory index",
                  placeholder: "Ask for a provision, a section number, or an old Code citation",
                  className: "min-w-0 flex-1 bg-transparent py-4 pr-3 font-mono text-[13px] text-paper placeholder:text-muted/80"
                }
              ),
              /* @__PURE__ */ jsxs(
                "button",
                {
                  type: "submit",
                  className: "group flex items-center gap-2 border-l border-hair bg-gold px-4 text-ink transition-colors duration-200 hover:bg-gold-light",
                  children: [
                    /* @__PURE__ */ jsx("span", { className: "label-xs", children: "Run" }),
                    /* @__PURE__ */ jsx(ArrowRight, { className: "h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" })
                  ]
                }
              )
            ]
          }
        ),
        /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-x-5 gap-y-1.5 border-b border-hair bg-cream/60 px-4 py-2 font-mono text-[11px] text-muted", children: [
          /* @__PURE__ */ jsxs("span", { children: [
            "act.",
            /* @__PURE__ */ jsx("span", { className: cn(parsed.code ? "text-gold-light" : "text-silver/50"), children: parsed.code ?? "auto" })
          ] }),
          /* @__PURE__ */ jsxs("span", { children: [
            "\xA7.",
            /* @__PURE__ */ jsx("span", { className: cn(parsed.number ? "text-gold-light" : "text-silver/50"), children: parsed.number ?? "inferred" })
          ] }),
          /* @__PURE__ */ jsxs("span", { children: [
            "terms.",
            /* @__PURE__ */ jsx("span", { className: "text-silver/70", children: parsed.words.length })
          ] }),
          /* @__PURE__ */ jsxs("span", { className: "ml-auto hidden sm:inline", children: [
            "corpus.",
            /* @__PURE__ */ jsxs("span", { className: "text-silver/70", children: [
              CORPUS.length,
              " shown \xB7 ",
              TOTAL_ACTS,
              " acts"
            ] })
          ] })
        ] }),
        phase === "running" && /* @__PURE__ */ jsx("ul", { className: "divide-y divide-hair/70 border-b border-hair", children: STEPS.map((s, i) => /* @__PURE__ */ jsxs(
          "li",
          {
            className: cn(
              "flex items-center gap-3 px-4 py-2 font-mono text-[11.5px] transition-colors duration-200",
              i < step ? "text-silver" : "text-muted/45"
            ),
            children: [
              /* @__PURE__ */ jsx("span", { className: cn("w-4 text-right", i < step ? "text-success" : "text-muted/40"), children: i < step ? "\u2713" : "\xB7" }),
              s,
              i === step && /* @__PURE__ */ jsx("span", { className: "ml-auto h-px w-10 animate-pulse bg-gold/70" })
            ]
          },
          s
        )) }),
        phase === "done" && hit && /* @__PURE__ */ jsxs("div", { children: [
          /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-2 border-b border-hair px-4 py-3", children: [
            /* @__PURE__ */ jsx("span", { className: "label-xs text-muted", children: "returned unit" }),
            /* @__PURE__ */ jsx("div", { className: "flex flex-wrap gap-1", children: hits.map((h, i) => /* @__PURE__ */ jsxs(
              "button",
              {
                onClick: () => setOpenHit(i),
                className: cn(
                  "border px-2 py-1 font-mono text-[11px] transition-colors duration-200",
                  i === openHit ? "border-gold/70 bg-gold/10 text-gold-light" : "border-hair text-muted hover:border-slate-custom hover:text-silver"
                ),
                children: [
                  h.section.code,
                  " \xA7",
                  h.section.section.replace(/^Article\s/, "Art. ")
                ]
              },
              h.section.id
            )) }),
            /* @__PURE__ */ jsxs("span", { className: "ml-auto flex items-center gap-2", children: [
              /* @__PURE__ */ jsx(Tag, { tone: hit.section.status === "Active" ? "active" : "repealed", children: hit.section.status }),
              /* @__PURE__ */ jsxs("span", { className: "font-mono text-[11px] text-muted", children: [
                "score ",
                Math.min(99, Math.round(hit.score))
              ] })
            ] })
          ] }),
          /* @__PURE__ */ jsxs("div", { className: "relative max-h-[340px] overflow-y-auto px-4 py-5 sm:px-6", children: [
            /* @__PURE__ */ jsxs("p", { className: "mb-3 flex flex-wrap items-center gap-2 label-xs text-gold", children: [
              /* @__PURE__ */ jsx(Hash, { className: "h-3 w-3", strokeWidth: 1.6 }),
              hit.section.act,
              /* @__PURE__ */ jsxs("span", { className: "text-muted", children: [
                "\xB7 ",
                hit.section.chapter
              ] })
            ] }),
            /* @__PURE__ */ jsx(StatutoryText, { text: canon(hit.section) }),
            hit.chars > 560 && /* @__PURE__ */ jsxs("p", { className: "mt-4 flex items-start gap-2 border-t border-hair/70 pt-3 text-[11.5px] leading-relaxed text-muted", children: [
              /* @__PURE__ */ jsx(TriangleAlert, { className: "mt-0.5 h-3.5 w-3.5 shrink-0 text-warning/80", strokeWidth: 1.5 }),
              "Unit printed whole \u2014 ",
              hit.chars.toLocaleString("en-IN"),
              " characters. Nothing was truncated to fit the pane."
            ] })
          ] }),
          /* @__PURE__ */ jsx("div", { className: "grid gap-px border-t border-hair bg-hair sm:grid-cols-4", children: [
            ["citation", `${hit.section.code} \xA7${hit.section.section.replace(/^Article\s+/, "Art. ")}`],
            ["unit id", `u-${digest(canon(hit.section))}`],
            ["anchors", `${hit.anchors.proviso}P \xB7 ${hit.anchors.exception}E \xB7 ${hit.anchors.explanation}X \xB7 ${hit.anchors.illustration}I`],
            ["offset", `${hit.chars ? `${Math.round(hit.chars * 0.31)}` : "0"}\u2013${hit.chars.toLocaleString("en-IN")}`]
          ].map(([k, v]) => /* @__PURE__ */ jsxs("div", { className: "bg-panel px-4 py-3", children: [
            /* @__PURE__ */ jsx("p", { className: "label-xs text-muted", children: k }),
            /* @__PURE__ */ jsx("p", { className: "mt-1.5 font-mono text-[11.5px] text-paper/90", children: v })
          ] }, k)) })
        ] }),
        phase === "done" && !hit && /* @__PURE__ */ jsxs("div", { className: "px-4 py-10 text-center", children: [
          /* @__PURE__ */ jsx("p", { className: "font-mono text-[12px] text-silver", children: "No unit in the demonstration extract answers that query." }),
          /* @__PURE__ */ jsxs("p", { className: "mx-auto mt-2 max-w-sm text-[12px] leading-relaxed text-muted", children: [
            "The live index resolves across all ",
            TOTAL_ACTS,
            " statutes; this page ships a",
            " ",
            CORPUS.length,
            "-unit extract so the grammar can be inspected rather than described."
          ] })
        ] }),
        /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-2 border-t border-hair bg-panel-2 px-4 py-3", children: [
          /* @__PURE__ */ jsx("span", { className: "label-xs text-muted", children: "try" }),
          SUGGESTIONS.map((s) => /* @__PURE__ */ jsx(
            "button",
            {
              onClick: () => {
                setQ(s);
                run(s);
              },
              className: "border border-hair px-2 py-1 font-mono text-[11px] text-silver transition-all duration-200 hover:-translate-y-px hover:border-gold/60 hover:text-gold-light",
              children: s
            },
            s
          ))
        ] })
      ] }) }) })
    ] }) }),
    /* @__PURE__ */ jsx(Ticker, {}),
    /* @__PURE__ */ jsxs("div", { className: "mx-auto w-full max-w-[1400px] px-5 sm:px-8", children: [
      /* @__PURE__ */ jsx("div", { className: "grid grid-cols-2 gap-px border-x border-b border-hair bg-hair md:grid-cols-5", children: [
        { v: String(TOTAL_ACTS), k: "bare acts indexed", s: "8 categories \xB7 3 repealed" },
        { v: "1", k: "boundary grammar", s: "9 capture groups" },
        { v: "\u226450", k: "queries per batch", s: "one queue, one table" },
        { v: "2-pane", k: "section comparison", s: `${MAPPINGS.length} mapped pairs live` },
        { v: String(REPEAL_LINKS), k: "repeal entries", s: "repealed statutes pinned" }
      ].map((f) => /* @__PURE__ */ jsx(Reveal, { className: "bg-cream last:col-span-2 md:last:col-span-1", children: /* @__PURE__ */ jsxs("div", { className: "group px-5 py-6 transition-colors duration-300 hover:bg-panel/60", children: [
        /* @__PURE__ */ jsx("p", { className: "font-display text-[clamp(1.7rem,3.2vw,2.6rem)] leading-none tracking-tight text-paper transition-colors duration-300 group-hover:text-gold-light", children: f.v }),
        /* @__PURE__ */ jsx("p", { className: "mt-3 label-xs text-silver", children: f.k }),
        /* @__PURE__ */ jsx("p", { className: "mt-1 font-mono text-[10.5px] text-muted", children: f.s })
      ] }) }, f.k)) }),
      /* @__PURE__ */ jsx("div", { className: "border-b border-hair bg-cream px-3 py-2.5 text-[11px] text-muted", children: /* @__PURE__ */ jsxs("span", { className: "font-mono", children: [
        "Categories: ",
        ACT_CATEGORIES.map((c) => `${c.title} (${c.acts.length})`).join(" \xB7 ")
      ] }) })
    ] })
  ] });
}
export {
  Hero
};
