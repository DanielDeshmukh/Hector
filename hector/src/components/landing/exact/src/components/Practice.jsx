import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { ChevronDown, Check, Minus, BookOpen as BookMarked, Gavel, Landmark, ScrollText } from "lucide-react";
import { cn } from "../utils/cn";
import { Btn, Panel, Reveal, SectionShell, Tag, WideHead, WideSection } from "./ui";
import { FAQ, PIPELINE, byId } from "../data/corpus";
import { canon, digest } from "../lib/text";
function sentences(text) {
  const out = [];
  const re = /[^.]+\.?/g;
  let m;
  while (m = re.exec(text)) {
    const q = m[0].trim();
    if (q.length > 24) out.push({ q, start: m.index, end: m.index + m[0].length });
  }
  return out;
}
function LedgerSection() {
  const text = useMemo(() => canon(byId("bnss-144")), []);
  const ledger = useMemo(() => sentences(text).slice(0, 4), [text]);
  return /* @__PURE__ */ jsx(
    SectionShell,
    {
      id: "ledger",
      no: "06",
      kicker: "Assembly & the ledger",
      title: /* @__PURE__ */ jsxs(Fragment, { children: [
        "Six stages.",
        /* @__PURE__ */ jsx("span", { className: "block italic text-gold-light", children: "One traceable offset." })
      ] }),
      lede: /* @__PURE__ */ jsx(Fragment, { children: "Retrieval is only half the instrument. The other half is the ledger: the record of which unit answered, at which offset, under which anchor. An answer that cannot name its provision does not leave the pipeline." }),
      aside: /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap gap-2", children: [
        /* @__PURE__ */ jsx(Tag, { tone: "gold", children: "offset-level" }),
        /* @__PURE__ */ jsx(Tag, { tone: "neutral", children: "no orphan quotes" })
      ] }),
      children: /* @__PURE__ */ jsxs("div", { className: "grid gap-px bg-hair lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]", children: [
        /* @__PURE__ */ jsx("ol", { className: "bg-cream", children: PIPELINE.map((p) => /* @__PURE__ */ jsxs(
          "li",
          {
            className: "group relative flex gap-4 border-b border-hair/70 px-4 py-4 transition-colors duration-300 last:border-b-0 hover:bg-panel/60",
            children: [
              /* @__PURE__ */ jsx("span", { className: "relative", children: /* @__PURE__ */ jsx("span", { className: "block font-display text-[26px] leading-none text-slate-custom transition-colors duration-300 group-hover:text-gold", children: p.n }) }),
              /* @__PURE__ */ jsxs("span", { className: "min-w-0", children: [
                /* @__PURE__ */ jsxs("span", { className: "flex flex-wrap items-baseline gap-3", children: [
                  /* @__PURE__ */ jsx("span", { className: "text-[15px] text-paper", children: p.title }),
                  /* @__PURE__ */ jsx("span", { className: "ml-auto font-mono text-[10.5px] text-gold/80", children: p.meta })
                ] }),
                /* @__PURE__ */ jsx("span", { className: "mt-1.5 block max-w-[52ch] text-[12.5px] leading-[1.65] text-silver/85", children: p.body })
              ] })
            ]
          },
          p.n
        )) }),
        /* @__PURE__ */ jsx("div", { className: "bg-cream", children: /* @__PURE__ */ jsxs(Panel, { className: "border-0 bg-transparent", children: [
          /* @__PURE__ */ jsxs("div", { className: "flex items-center justify-between border-b border-hair bg-panel-2 px-4 py-2.5", children: [
            /* @__PURE__ */ jsxs("span", { className: "flex items-center gap-2 label-xs text-silver", children: [
              /* @__PURE__ */ jsx(BookMarked, { className: "h-3.5 w-3.5 text-gold", strokeWidth: 1.5 }),
              "ledger \xB7 BNSS s. 144"
            ] }),
            /* @__PURE__ */ jsxs("span", { className: "font-mono text-[10.5px] text-muted", children: [
              "u-",
              digest(text),
              " \xB7 ",
              text.length,
              " ch"
            ] })
          ] }),
          /* @__PURE__ */ jsxs("table", { className: "w-full border-collapse text-left", children: [
            /* @__PURE__ */ jsx("thead", { children: /* @__PURE__ */ jsxs("tr", { className: "border-b border-hair label-xs text-muted", children: [
              /* @__PURE__ */ jsx("th", { className: "px-4 py-2 font-normal", children: "sentence returned" }),
              /* @__PURE__ */ jsx("th", { className: "w-[104px] px-2 py-2 font-normal", children: "offset" }),
              /* @__PURE__ */ jsx("th", { className: "w-[92px] px-2 py-2 text-right font-normal", children: "state" })
            ] }) }),
            /* @__PURE__ */ jsx("tbody", { children: ledger.map((l) => /* @__PURE__ */ jsxs("tr", { className: "group border-b border-hair/60 align-top transition-colors hover:bg-panel/60", children: [
              /* @__PURE__ */ jsxs("td", { className: "px-4 py-3", children: [
                /* @__PURE__ */ jsxs("p", { className: "font-mono text-[11.5px] leading-[1.7] text-silver/90", children: [
                  /* @__PURE__ */ jsx("span", { className: "text-gold/70", children: "\u201C" }),
                  l.q.length > 150 ? `${l.q.slice(0, 150)}\u2026` : l.q,
                  /* @__PURE__ */ jsx("span", { className: "text-gold/70", children: "\u201D" })
                ] }),
                /* @__PURE__ */ jsxs("p", { className: "mt-1 text-[11px] text-muted", children: [
                  "anchor: ",
                  /^Provided/i.test(l.q) ? "proviso" : /^\s*Explanation/i.test(l.q) ? "explanation" : l.q.includes("(a)") || l.q.includes("(b)") ? "clauses (a)\u2013(c)" : "operative sub-section"
                ] })
              ] }),
              /* @__PURE__ */ jsxs("td", { className: "px-2 py-3 font-mono text-[11px] text-muted", children: [
                l.start,
                "\u2013",
                l.end
              ] }),
              /* @__PURE__ */ jsx("td", { className: "px-2 py-3 text-right", children: /* @__PURE__ */ jsxs("span", { className: "inline-flex items-center gap-1.5 font-mono text-[10.5px] text-success", children: [
                /* @__PURE__ */ jsx("span", { className: "h-1 w-1 bg-success" }),
                "traced"
              ] }) })
            ] }, l.start)) })
          ] }),
          /* @__PURE__ */ jsx("div", { className: "grid grid-cols-2 gap-px border-t border-hair bg-hair sm:grid-cols-4", children: [
            ["section units in index", "4,034"],
            ["untraceable sentences", "0"],
            ["citations per answer", "\u2264 12"],
            ["format", "statute \xB7 \xA7 \xB7 cl."]
          ].map(([k, v]) => /* @__PURE__ */ jsxs("div", { className: "bg-panel px-3 py-2.5", children: [
            /* @__PURE__ */ jsx("p", { className: "label-xs text-muted", children: k }),
            /* @__PURE__ */ jsx("p", { className: "mt-1 font-mono text-[11.5px] text-paper/90", children: v })
          ] }, k)) })
        ] }) })
      ] })
    }
  );
}
const FOR = [
  {
    icon: Gavel,
    who: "The bench & the registry",
    what: "Two provisions opened side by side, the old text and the new, with the relation named. Nothing has to be taken on the word of a summary.",
    query: "compare CrPC 482 \u21C4 BNSS 528"
  },
  {
    icon: ScrollText,
    who: "Litigation desks",
    what: "Charge frames, bail applications and discharge petitions drafted against the provision actually in force on the date of the offence.",
    query: "batch \xB7 44 queries \xB7 one matter index"
  },
  {
    icon: Landmark,
    who: "Chambers & solo practice",
    what: "A citation checked in seconds rather than in a copy of a digest that was last printed before the amendment.",
    query: "is 498A IPC carried into the BNS?"
  },
  {
    icon: BookMarked,
    who: "In-house & regulatory",
    what: "Statutory obligations traced to the section that imposes them \u2014 environment, consumer, data, labour \u2014 with the commencement date attached.",
    query: "CPA 2019 s. 2(9) \xB7 deficiency in service"
  }
];
function ForWhomSection() {
  return /* @__PURE__ */ jsxs(WideSection, { id: "practice", tint: true, children: [
    /* @__PURE__ */ jsx(
      WideHead,
      {
        no: "07",
        kicker: "Where it sits on the desk",
        title: /* @__PURE__ */ jsxs(Fragment, { children: [
          "Built for the part of practice",
          /* @__PURE__ */ jsx("span", { className: "block italic text-gold-light", children: "that is reading, not guessing." })
        ] }),
        lede: /* @__PURE__ */ jsx(Fragment, { children: "Hector does not draft your pleading and does not decide your case. It answers the question a bench asks fifteen seconds after you cite a section \u2014 where is that written, and is it still in force." })
      }
    ),
    /* @__PURE__ */ jsx("div", { className: "mt-10 grid gap-px bg-hair md:grid-cols-2", children: FOR.map((f, i) => /* @__PURE__ */ jsx(Reveal, { delay: i * 70, className: "bg-cream", children: /* @__PURE__ */ jsxs("div", { className: "group h-full px-5 py-6 transition-colors duration-300 hover:bg-panel/60", children: [
      /* @__PURE__ */ jsxs("div", { className: "flex items-center gap-3", children: [
        /* @__PURE__ */ jsx("span", { className: "grid h-8 w-8 place-items-center border border-slate-custom text-gold transition-colors duration-300 group-hover:border-gold/70", children: /* @__PURE__ */ jsx(f.icon, { className: "h-4 w-4", strokeWidth: 1.4 }) }),
        /* @__PURE__ */ jsx("h3", { className: "font-display text-[22px] leading-none tracking-tight text-paper", children: f.who }),
        /* @__PURE__ */ jsx("span", { className: "ml-auto font-mono text-[10px] text-muted", children: String(i + 1).padStart(2, "0") })
      ] }),
      /* @__PURE__ */ jsx("p", { className: "mt-3 max-w-[54ch] text-[13.5px] leading-[1.7] text-silver", children: f.what }),
      /* @__PURE__ */ jsxs("p", { className: "mt-4 inline-flex items-center gap-2 border border-hair px-2.5 py-1.5 font-mono text-[11px] text-silver/80 transition-colors duration-300 group-hover:border-gold/50 group-hover:text-gold-light", children: [
        /* @__PURE__ */ jsx("span", { className: "text-muted", children: "q>" }),
        f.query
      ] })
    ] }) }, f.who)) })
  ] });
}
function AccessSection() {
  return /* @__PURE__ */ jsxs(WideSection, { id: "access", children: [
    /* @__PURE__ */ jsx(
      WideHead,
      {
        no: "08",
        kicker: "Access",
        title: /* @__PURE__ */ jsxs(Fragment, { children: [
          "Free for everyone.",
          /* @__PURE__ */ jsx("span", { className: "block italic text-gold-light", children: "No plan, no seat, no meter." })
        ] }),
        lede: /* @__PURE__ */ jsx(Fragment, { children: "Hector carries no subscription and no per-desk pricing. The index is maintained against the Gazette, the Legislative Department\u2019s amendments and the correction orders \u2014 and it is open to the Bar, the Bench and students alike." }),
        controls: /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-2 lg:justify-end", children: [
          /* @__PURE__ */ jsx(Tag, { tone: "gold", children: "free for everyone" }),
          /* @__PURE__ */ jsx(Tag, { tone: "neutral", children: "no token counting" }),
          /* @__PURE__ */ jsx(Tag, { tone: "neutral", children: "no account required" })
        ] })
      }
    ),
    /* @__PURE__ */ jsx(Reveal, { y: false, children: /* @__PURE__ */ jsxs("div", { className: "mt-10 grid gap-px border border-hair bg-hair lg:grid-cols-[minmax(0,1fr)_420px]", children: [
      /* @__PURE__ */ jsxs("div", { className: "bg-panel px-5 py-6", children: [
        /* @__PURE__ */ jsx("p", { className: "label-xs text-gold", children: "What every account gets" }),
        /* @__PURE__ */ jsx("ul", { className: "mt-4 space-y-2", children: [
          "Full statutory index \u2014 16 acts indexed, 38 catalogued",
          "Section comparison, 2-pane, every mapped pair",
          "Batch runs \u2014 50 queries, one queue",
          "Citation strings and the offset ledger, copy-ready"
        ].map((l) => /* @__PURE__ */ jsxs("li", { className: "flex items-start gap-2 text-[13px] leading-snug text-silver", children: [
          /* @__PURE__ */ jsx(Check, { className: "mt-[3px] h-3 w-3 shrink-0 text-gold/80", strokeWidth: 2 }),
          l
        ] }, l)) }),
        /* @__PURE__ */ jsx("p", { className: "mt-5 max-w-[58ch] text-[12.5px] leading-[1.7] text-muted", children: "There is no gate in front of the statute book: no key request, no trial meter, no seat count. If you can open the page, you have the index." })
      ] }),
      /* @__PURE__ */ jsxs("div", { className: "flex flex-col justify-center gap-3 bg-cream px-5 py-6", children: [
        /* @__PURE__ */ jsx("p", { className: "label-xs text-gold", children: "Open the index" }),
        /* @__PURE__ */ jsx("p", { className: "max-w-[26ch] font-display text-[clamp(1.4rem,2.6vw,2rem)] leading-[1.1] text-paper", children: "No sign-up wall. Ask the statute a question." }),
        /* @__PURE__ */ jsx("a", { href: "/search", children: /* @__PURE__ */ jsx(Btn, { className: "w-full", children: "Try Hector" }) }),
        /* @__PURE__ */ jsx("p", { className: "min-h-[16px] font-mono text-[10.5px] text-muted", children: "free \xB7 no account \xB7 no meter" })
      ] })
    ] }) })
  ] });
}
function FaqSection() {
  const [open, setOpen] = useState(0);
  return /* @__PURE__ */ jsxs(
    SectionShell,
    {
      id: "faq",
      no: "09",
      kicker: "Questions of construction",
      title: /* @__PURE__ */ jsxs(Fragment, { children: [
        "Read it",
        /* @__PURE__ */ jsx("span", { className: "block italic text-gold-light", children: "as a set of clauses." })
      ] }),
      lede: /* @__PURE__ */ jsx(Fragment, { children: "The objections we hear most often, answered without a marketing register. Where the answer is \u201Cit depends on the text\u201D, we say so and point at the text." }),
      children: [
        /* @__PURE__ */ jsx("ol", { className: "border-t border-hair", children: FAQ.map((f, i) => {
          const on = open === i;
          return /* @__PURE__ */ jsxs("li", { className: "border-b border-hair", children: [
            /* @__PURE__ */ jsxs(
              "button",
              {
                onClick: () => setOpen(on ? -1 : i),
                className: "group flex w-full items-start gap-4 py-4 text-left transition-colors duration-200 hover:bg-panel/40",
                children: [
                  /* @__PURE__ */ jsx("span", { className: cn("mt-1 font-mono text-[10.5px]", on ? "text-gold" : "text-muted"), children: `(${String.fromCharCode(97 + i)})` }),
                  /* @__PURE__ */ jsx(
                    "span",
                    {
                      className: cn(
                        "flex-1 font-display text-[clamp(1.1rem,2.1vw,1.5rem)] leading-snug tracking-tight transition-colors duration-200",
                        on ? "text-gold-light" : "text-paper group-hover:text-paper"
                      ),
                      children: f.q
                    }
                  ),
                  /* @__PURE__ */ jsx("span", { className: cn("mt-1 transition-transform duration-300", on ? "rotate-180 text-gold" : "text-muted"), children: /* @__PURE__ */ jsx(ChevronDown, { className: "h-4 w-4", strokeWidth: 1.6 }) })
                ]
              }
            ),
            /* @__PURE__ */ jsx(
              "div",
              {
                className: "grid transition-[grid-template-rows] duration-500 ease-out",
                style: { gridTemplateRows: on ? "1fr" : "0fr" },
                children: /* @__PURE__ */ jsx("div", { className: "overflow-hidden", children: /* @__PURE__ */ jsx("p", { className: "max-w-[74ch] pb-5 pl-[46px] pr-8 text-[13.5px] leading-[1.75] text-silver", children: f.a }) })
              }
            )
          ] }, f.q);
        }) }),
        /* @__PURE__ */ jsxs("p", { className: "mt-6 flex items-center gap-2 font-mono text-[11px] text-muted", children: [
          /* @__PURE__ */ jsx(Minus, { className: "h-3 w-3", strokeWidth: 1.8 }),
          "clause (g) reserved for questions received at the register"
        ] })
      ]
    }
  );
}
export {
  AccessSection,
  FaqSection,
  ForWhomSection,
  LedgerSection
};
