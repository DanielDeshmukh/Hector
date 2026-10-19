import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { Search, X, ChevronRight, BookOpen, Hash, Layers, ArrowRight } from "lucide-react";
import { cn } from "../utils/cn";
import { Reveal, Tag, WideHead, WideSection } from "./ui";
import {
  ACT_CATEGORIES,
  ACTIVE_ACTS,
  ALL_ACTS,
  REPEALED_ACTS,
  REPEAL_LINKS,
  TOTAL_ACTS
} from "../data/acts";
import { SHORT_CODE_COLLISIONS, CORPUS } from "../data/corpus";
import { canon, digest } from "../lib/text";
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
function Mark({ text, term }) {
  if (!term.trim()) return /* @__PURE__ */ jsx(Fragment, { children: text });
  const parts = text.split(new RegExp(`(${esc(term.trim())})`, "gi"));
  return /* @__PURE__ */ jsx(Fragment, { children: parts.map(
    (p, i) => i % 2 === 1 ? /* @__PURE__ */ jsx("mark", { className: "bg-gold/25 text-gold-light", children: p }, i) : /* @__PURE__ */ jsx("span", { children: p }, i)
  ) });
}
function CorpusSection() {
  const [term, setTerm] = useState("");
  const [cat, setCat] = useState("all");
  const [status, setStatus] = useState("all");
  const [open, setOpen] = useState(null);
  const filtered = useMemo(() => {
    const t = term.trim().toLowerCase();
    return ACT_CATEGORIES.map((c) => {
      if (cat !== "all" && c.slug !== cat) return { ...c, acts: [] };
      return {
        ...c,
        acts: c.acts.filter((a) => {
          if (status !== "all" && a.status !== status) return false;
          if (!t) return true;
          return a.name.toLowerCase().includes(t) || a.code.toLowerCase().includes(t) || c.title.toLowerCase().includes(t) || String(a.year).includes(t) || (a.repeals ?? "").toLowerCase().includes(t);
        })
      };
    }).filter((c) => c.acts.length);
  }, [term, cat, status]);
  const shown = filtered.reduce((n, c) => n + c.acts.length, 0);
  const flat = filtered.flatMap((c) => c.acts.map((a) => ({ ...a, category: c.title })));
  return /* @__PURE__ */ jsxs(WideSection, { id: "corpus", children: [
    /* @__PURE__ */ jsx(
      WideHead,
      {
        no: "01",
        kicker: "The indexed corpus",
        title: /* @__PURE__ */ jsxs(Fragment, { children: [
          "Thirty-eight bare acts.",
          /* @__PURE__ */ jsx("span", { className: "block italic text-gold-light", children: "Nothing between you and the text." })
        ] }),
        lede: /* @__PURE__ */ jsx(Fragment, { children: "The index holds the statute as printed \u2014 long title, preamble, chapters, parts, sections, sub-sections, provisos, explanations, illustrations and schedules. Commentary, digests and headnotes are excluded, because a retrieval set should not be able to pass off a editorial summary as an enactment." }),
        controls: /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-2 lg:justify-end", children: [
          /* @__PURE__ */ jsxs(Tag, { tone: "gold", children: [
            TOTAL_ACTS,
            " statutes"
          ] }),
          /* @__PURE__ */ jsxs(Tag, { tone: "active", children: [
            ACTIVE_ACTS,
            " in force"
          ] }),
          /* @__PURE__ */ jsxs(Tag, { tone: "repealed", children: [
            REPEALED_ACTS,
            " repealed \xB7 still indexed"
          ] })
        ] })
      }
    ),
    /* @__PURE__ */ jsxs("div", { className: "mt-10 flex flex-col gap-3 border border-hair bg-panel-2/60 p-3 lg:flex-row lg:items-center", children: [
      /* @__PURE__ */ jsxs("label", { className: "group flex flex-1 items-center gap-3 border border-hair bg-cream px-3 py-2 transition-colors focus-within:border-gold/60", children: [
        /* @__PURE__ */ jsx(Search, { className: "h-3.5 w-3.5 text-muted transition-colors group-focus-within:text-gold", strokeWidth: 1.7 }),
        /* @__PURE__ */ jsx(
          "input",
          {
            value: term,
            onChange: (e) => setTerm(e.target.value),
            placeholder: "Search statute, short code, year or the act it repealed \u2014 try \u201C420\u201D, \u201Cmaintenance\u201D, \u201C1860\u201D",
            className: "min-w-0 flex-1 bg-transparent font-mono text-[12px] text-paper outline-none placeholder:text-muted/70"
          }
        ),
        term && /* @__PURE__ */ jsx("button", { onClick: () => setTerm(""), "aria-label": "Clear search", className: "text-muted hover:text-gold", children: /* @__PURE__ */ jsx(X, { className: "h-3.5 w-3.5", strokeWidth: 1.7 }) })
      ] }),
      /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-1.5", children: [
        [{ slug: "all", title: `All ${ACT_CATEGORIES.length}` }, ...ACT_CATEGORIES.map((c) => ({ slug: c.slug, title: `${c.title} ${c.acts.length}` }))].map(
          (c) => /* @__PURE__ */ jsx(
            "button",
            {
              onClick: () => setCat(c.slug),
              className: cn(
                "border px-2 py-1 font-mono text-[10.5px] transition-colors duration-200",
                cat === c.slug ? "border-gold/70 bg-gold/10 text-gold-light" : "border-hair text-muted hover:border-slate-custom hover:text-silver"
              ),
              children: c.title
            },
            c.slug
          )
        ),
        /* @__PURE__ */ jsx("span", { className: "mx-1 hidden h-4 w-px bg-hair sm:block" }),
        ["all", "Active", "Repealed"].map((s) => /* @__PURE__ */ jsx(
          "button",
          {
            onClick: () => setStatus(s),
            className: cn(
              "border px-2 py-1 font-mono text-[10.5px] uppercase tracking-wider transition-colors duration-200",
              status === s ? "border-silver/60 bg-slate-custom/30 text-paper" : "border-hair text-muted hover:text-silver"
            ),
            children: s
          },
          s
        ))
      ] })
    ] }),
    /* @__PURE__ */ jsxs("div", { className: "mt-px border border-hair bg-cream", children: [
      /* @__PURE__ */ jsxs("div", { className: "hidden grid-cols-[44px_minmax(0,1fr)_88px_120px_120px_40px] gap-4 border-b border-hair bg-panel-2 px-4 py-2 label-xs text-muted md:grid", children: [
        /* @__PURE__ */ jsx("span", { children: "#" }),
        /* @__PURE__ */ jsx("span", { children: "statute as printed" }),
        /* @__PURE__ */ jsx("span", { children: "year" }),
        /* @__PURE__ */ jsx("span", { children: "short code" }),
        /* @__PURE__ */ jsx("span", { children: "status" }),
        /* @__PURE__ */ jsx("span", {})
      ] }),
      filtered.length === 0 && /* @__PURE__ */ jsxs("div", { className: "px-4 py-14 text-center", children: [
        /* @__PURE__ */ jsxs("p", { className: "font-display text-[22px] italic text-silver/70", children: [
          "No enactment answers to \u201C",
          term,
          "\u201D."
        ] }),
        /* @__PURE__ */ jsxs("p", { className: "mt-2 text-[12px] text-muted", children: [
          "The index holds ",
          TOTAL_ACTS,
          " statutes; try a short code instead."
        ] })
      ] }),
      filtered.map((c) => /* @__PURE__ */ jsxs("div", { children: [
        /* @__PURE__ */ jsxs("div", { className: "flex items-center gap-3 border-y border-hair bg-panel/70 px-4 py-1.5 first:border-t-0", children: [
          /* @__PURE__ */ jsx("span", { className: "label-xs text-gold", children: c.title }),
          /* @__PURE__ */ jsx("span", { className: "h-px flex-1 bg-hair" }),
          /* @__PURE__ */ jsxs("span", { className: "font-mono text-[10.5px] text-muted", children: [
            c.acts.length,
            " act",
            c.acts.length > 1 ? "s" : ""
          ] })
        ] }),
        c.acts.map((a) => {
          const key = `${c.slug}-${a.code}-${a.year}`;
          const on = open === key;
          return /* @__PURE__ */ jsxs("div", { className: "border-b border-hair/60 last:border-b-0", children: [
            /* @__PURE__ */ jsxs(
              "button",
              {
                onClick: () => setOpen(on ? null : key),
                className: cn(
                  "group grid w-full grid-cols-[44px_minmax(0,1fr)_40px] items-center gap-4 px-4 py-3 text-left transition-colors duration-200 md:grid-cols-[44px_minmax(0,1fr)_88px_120px_120px_40px]",
                  on ? "bg-gold/[0.06]" : "hover:bg-panel/50"
                ),
                children: [
                  /* @__PURE__ */ jsx("span", { className: "font-mono text-[10.5px] text-muted", children: String(ALL_ACTS.indexOf(a) + 1).padStart(2, "0") }),
                  /* @__PURE__ */ jsxs("span", { className: "min-w-0", children: [
                    /* @__PURE__ */ jsx("span", { className: "block truncate text-[14px] leading-snug text-paper transition-colors duration-200 group-hover:text-gold-light", children: /* @__PURE__ */ jsx(Mark, { text: a.name, term }) }),
                    a.repeals && /* @__PURE__ */ jsxs("span", { className: "mt-0.5 block truncate font-mono text-[10.5px] text-muted", children: [
                      "repeals ",
                      /* @__PURE__ */ jsx(Mark, { text: a.repeals, term })
                    ] })
                  ] }),
                  /* @__PURE__ */ jsx("span", { className: "hidden font-mono text-[11.5px] text-silver md:block", children: /* @__PURE__ */ jsx(Mark, { text: String(a.year), term }) }),
                  /* @__PURE__ */ jsx("span", { className: "hidden md:block", children: /* @__PURE__ */ jsx("span", { className: "inline-flex items-center border border-slate-custom/80 px-1.5 py-0.5 font-mono text-[10.5px] text-gold-light", children: /* @__PURE__ */ jsx(Mark, { text: a.code, term }) }) }),
                  /* @__PURE__ */ jsx("span", { className: "hidden md:block", children: /* @__PURE__ */ jsx(Tag, { tone: a.status === "Active" ? "active" : "repealed", children: a.status }) }),
                  /* @__PURE__ */ jsx(
                    ChevronRight,
                    {
                      className: cn(
                        "h-3.5 w-3.5 text-muted transition-transform duration-300",
                        on && "rotate-90 text-gold"
                      ),
                      strokeWidth: 1.7
                    }
                  )
                ]
              }
            ),
            on && /* @__PURE__ */ jsxs("div", { className: "grid gap-px border-t border-hair bg-hair md:grid-cols-[minmax(0,1fr)_260px]", children: [
              /* @__PURE__ */ jsxs("div", { className: "bg-panel px-4 py-4", children: [
                /* @__PURE__ */ jsx("p", { className: "label-xs text-muted", children: "reading note" }),
                /* @__PURE__ */ jsx("p", { className: "mt-2 max-w-[62ch] text-[13px] leading-[1.7] text-silver", children: a.note ?? `${a.name} is held as a single canonical string, amended text folded to the date of the last Gazette correction in the index. Units are addressed as ${a.code} \xA7 n.` }),
                /* @__PURE__ */ jsxs("div", { className: "mt-4 flex flex-wrap gap-x-8 gap-y-2 font-mono text-[11px]", children: [
                  /* @__PURE__ */ jsxs("span", { className: "text-muted", children: [
                    "anchors.",
                    " ",
                    /* @__PURE__ */ jsx("span", { className: "text-silver", children: a.code === "Constitution" ? "ARTICLE \xB7 PART \xB7 SCHEDULE" : "SECTION \xB7 CHAPTER \xB7 PART \xB7 SCHEDULE" })
                  ] }),
                  /* @__PURE__ */ jsxs("span", { className: "text-muted", children: [
                    "status. ",
                    /* @__PURE__ */ jsx("span", { className: a.status === "Active" ? "text-success" : "text-error/80", children: a.status })
                  ] }),
                  /* @__PURE__ */ jsxs("span", { className: "text-muted", children: [
                    "repeal entry. ",
                    /* @__PURE__ */ jsx("span", { className: "text-silver", children: a.repeals ?? "none asserted" })
                  ] })
                ] })
              ] }),
              /* @__PURE__ */ jsxs("div", { className: "bg-panel px-4 py-4", children: [
                /* @__PURE__ */ jsx("p", { className: "label-xs text-muted", children: "index digest" }),
                /* @__PURE__ */ jsxs("p", { className: "mt-2 flex items-center gap-1.5 font-mono text-[11.5px] text-paper/90", children: [
                  /* @__PURE__ */ jsx(Hash, { className: "h-3 w-3 text-gold", strokeWidth: 1.7 }),
                  a.code.toLowerCase(),
                  "-",
                  digest(`${a.name}|${a.year}|${a.status}`).slice(0, 8)
                ] }),
                /* @__PURE__ */ jsxs("p", { className: "mt-3 text-[11.5px] leading-relaxed text-muted", children: [
                  CORPUS.filter((s) => s.code === a.code).length,
                  " unit(s) from this act are open for inspection on this page."
                ] }),
                /* @__PURE__ */ jsxs("a", { href: "#grammar", className: "group mt-3 inline-flex items-center gap-1.5 label-xs text-gold hover:text-gold-light", children: [
                  "see the grammar",
                  /* @__PURE__ */ jsx(ArrowRight, { className: "h-3 w-3 transition-transform group-hover:translate-x-0.5" })
                ] })
              ] })
            ] })
          ] }, key);
        })
      ] }, c.slug)),
      /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-4 border-t border-hair bg-panel-2 px-4 py-2.5 font-mono text-[10.5px] text-muted", children: [
        /* @__PURE__ */ jsxs("span", { children: [
          "showing ",
          /* @__PURE__ */ jsx("span", { className: "text-gold-light", children: shown }),
          " of ",
          TOTAL_ACTS
        ] }),
        /* @__PURE__ */ jsx("span", { className: "h-3 w-px bg-hair" }),
        /* @__PURE__ */ jsxs("span", { children: [
          "filter: ",
          cat === "all" ? "all categories" : cat,
          " \xB7 ",
          status
        ] }),
        /* @__PURE__ */ jsxs("span", { className: "ml-auto flex items-center gap-1.5", children: [
          /* @__PURE__ */ jsx(Layers, { className: "h-3 w-3", strokeWidth: 1.6 }),
          " ",
          flat.length ? "click a row for the index entry" : ""
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxs("div", { className: "mt-4 grid gap-px bg-hair lg:grid-cols-3", children: [
      /* @__PURE__ */ jsxs("div", { className: "bg-cream px-4 py-4", children: [
        /* @__PURE__ */ jsxs("p", { className: "flex items-center gap-2 label-xs text-gold", children: [
          /* @__PURE__ */ jsx(BookOpen, { className: "h-3.5 w-3.5", strokeWidth: 1.6 }),
          "repeal entries carried on the index"
        ] }),
        /* @__PURE__ */ jsx("ul", { className: "mt-3 space-y-2", children: ALL_ACTS.filter((a) => a.repeals).map((a) => /* @__PURE__ */ jsxs("li", { className: "flex items-baseline gap-2 border-b border-hair/60 pb-1.5 font-mono text-[11px] text-silver", children: [
          /* @__PURE__ */ jsx("span", { className: "text-gold-light", children: a.code }),
          /* @__PURE__ */ jsx("span", { className: "text-muted", children: a.year }),
          /* @__PURE__ */ jsx("span", { className: "text-muted", children: "\u2192" }),
          /* @__PURE__ */ jsx("span", { className: "text-paper/80", children: a.repeals })
        ] }, `${a.code}-${a.year}`)) }),
        /* @__PURE__ */ jsxs("p", { className: "mt-3 text-[11.5px] leading-relaxed text-muted", children: [
          REPEAL_LINKS,
          " statutes in the index carry an express repeal. Both texts stay addressable \u2014 the repealed one is what a pre-commencement offence is charged under."
        ] })
      ] }),
      /* @__PURE__ */ jsxs("div", { className: "bg-cream px-4 py-4", children: [
        /* @__PURE__ */ jsx("p", { className: "label-xs text-gold", children: "short-code collisions" }),
        /* @__PURE__ */ jsxs("p", { className: "mt-2 text-[12.5px] leading-[1.6] text-silver", children: [
          "Three abbreviations are claimed twice across ",
          TOTAL_ACTS,
          " statutes. The resolver keeps both and pins the full long title before it answers, so a citation to \u201CCA\u201D is never silently resolved."
        ] }),
        /* @__PURE__ */ jsx("ul", { className: "mt-3 space-y-2", children: SHORT_CODE_COLLISIONS.map((c) => /* @__PURE__ */ jsx("li", { className: "border-l-2 border-warning/50 py-1 pl-3 font-mono text-[11px] text-warning/85", children: c }, c)) })
      ] }),
      /* @__PURE__ */ jsx(Reveal, { y: false, className: "bg-cream", children: /* @__PURE__ */ jsxs("div", { className: "px-4 py-4", children: [
        /* @__PURE__ */ jsx("p", { className: "label-xs text-gold", children: "unit extract on this page" }),
        /* @__PURE__ */ jsxs("p", { className: "mt-2 font-display text-[40px] leading-none text-paper", children: [
          CORPUS.length,
          /* @__PURE__ */ jsx("span", { className: "ml-2 font-sans text-[12px] font-light italic text-silver", children: "sections, whole" })
        ] }),
        /* @__PURE__ */ jsx("p", { className: "mt-2 text-[11.5px] leading-relaxed text-muted", children: "Opened so the grammar can be inspected rather than described: the criminal succession, the procedural pair, a bail provision, and two civil sections that every chambers asks about." }),
        /* @__PURE__ */ jsxs("div", { className: "mt-3 flex flex-wrap gap-1.5", children: [
          CORPUS.slice(0, 8).map((s) => /* @__PURE__ */ jsxs("span", { className: "border border-hair px-1.5 py-0.5 font-mono text-[10px] text-silver", children: [
            s.code,
            " \xA7",
            s.section.replace(/^Article\s+/, "Art. ")
          ] }, s.id)),
          /* @__PURE__ */ jsxs("span", { className: "border border-hair px-1.5 py-0.5 font-mono text-[10px] text-muted", children: [
            "+",
            Math.max(0, CORPUS.length - 8)
          ] })
        ] })
      ] }) })
    ] })
  ] });
}
const canonOf = (id) => {
  const s = CORPUS.find((x) => x.id === id);
  return s ? canon(s) : "";
};
export {
  CorpusSection,
  canonOf
};
