import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { ChevronDown, Check, Minus, Mail, BookOpen as BookMarked, Gavel, Landmark, ScrollText } from "lucide-react";
import { cn } from "../utils/cn";
import { Btn, Panel, Reveal, SectionShell, Tag, WideHead, WideSection } from "./ui";
import { ACCESS, FAQ, PIPELINE, byId } from "../data/corpus";
import { canon, digest } from "../lib/text";
import { TOTAL_ACTS } from "../data/acts";
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
            ["units in index", String(TOTAL_ACTS)],
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
const FEATURES = [
  ["Bare-act index", `${TOTAL_ACTS} statutes`, `${TOTAL_ACTS} statutes`, `${TOTAL_ACTS} + private overlay`],
  ["Regex boundary units", "whole sections", "whole sections", "whole sections"],
  ["Section comparison", "2-pane, mapped pairs", "2-pane + free pairing", "custom pairs per matter"],
  ["Queries per batch run", "10", "50", "queued, uncapped"],
  ["Citation strings", "copy-ready", "copy-ready", "copy-ready + annexure"],
  ["Exports", "\u2014", "CSV \xB7 annexure", "CSV \xB7 annexure \xB7 JSON"],
  ["Offset ledger", "per sentence", "per sentence", "per sentence"],
  ["Seats", "1", "up to 10", "named counsel"],
  ["Case-report corpus", "\u2014", "read-only add-on", "second index"],
  ["Deployment", "hosted", "hosted", "VPC / on-premise"]
];
function AccessSection() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(null);
  const valid = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.trim());
  return /* @__PURE__ */ jsxs(WideSection, { id: "access", children: [
    /* @__PURE__ */ jsx(
      WideHead,
      {
        no: "08",
        kicker: "Access",
        title: /* @__PURE__ */ jsxs(Fragment, { children: [
          "Priced per desk.",
          /* @__PURE__ */ jsx("span", { className: "block italic text-gold-light", children: "Not per word." })
        ] }),
        lede: /* @__PURE__ */ jsx(Fragment, { children: "The index is maintained against the Gazette, the Legislative Department\u2019s amendments and the correction orders. One subscription, no meter on the statute book." }),
        controls: /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-2 lg:justify-end", children: [
          /* @__PURE__ */ jsx(Tag, { tone: "neutral", children: "no token counting" }),
          /* @__PURE__ */ jsx(Tag, { tone: "neutral", children: "cancel at any quarter" }),
          /* @__PURE__ */ jsx(Tag, { tone: "gold", children: "request reviewed by hand" })
        ] })
      }
    ),
    /* @__PURE__ */ jsx("div", { className: "mt-10 overflow-x-auto", children: /* @__PURE__ */ jsxs("table", { className: "w-full min-w-[720px] border-collapse text-left", children: [
      /* @__PURE__ */ jsx("thead", { children: /* @__PURE__ */ jsxs("tr", { children: [
        /* @__PURE__ */ jsx("th", { className: "w-[240px] border-b border-hair px-4 py-5 align-bottom", children: /* @__PURE__ */ jsx("span", { className: "label-xs text-muted", children: "plan" }) }),
        ACCESS.map((t) => /* @__PURE__ */ jsxs(
          "th",
          {
            className: cn(
              "relative border-b px-5 py-5 align-bottom transition-colors duration-300",
              t.featured ? "border-gold/70 bg-gold/[0.05]" : "border-hair bg-cream"
            ),
            children: [
              t.featured && /* @__PURE__ */ jsx("span", { className: "absolute inset-x-0 top-0 h-[2px] bg-gold" }),
              /* @__PURE__ */ jsx("p", { className: "label-xs text-gold", children: t.tier }),
              /* @__PURE__ */ jsx("p", { className: "mt-3 font-display text-[clamp(1.7rem,3.2vw,2.5rem)] leading-none tracking-tight text-paper", children: t.price }),
              /* @__PURE__ */ jsx("p", { className: "mt-2 font-mono text-[11px] text-muted", children: t.per }),
              /* @__PURE__ */ jsx("ul", { className: "mt-4 hidden space-y-1.5 lg:block", children: t.lines.map((l) => /* @__PURE__ */ jsxs("li", { className: "flex items-start gap-2 text-[12px] leading-snug text-silver", children: [
                /* @__PURE__ */ jsx(Check, { className: "mt-[3px] h-3 w-3 shrink-0 text-gold/80", strokeWidth: 2 }),
                l
              ] }, l)) })
            ]
          },
          t.tier
        ))
      ] }) }),
      /* @__PURE__ */ jsx("tbody", { children: FEATURES.map(([label, ...cells]) => /* @__PURE__ */ jsxs("tr", { className: "group border-b border-hair/60 transition-colors hover:bg-panel/40", children: [
        /* @__PURE__ */ jsx("th", { scope: "row", className: "px-4 py-2.5 text-left text-[12.5px] font-normal text-silver", children: label }),
        cells.map((c, i) => /* @__PURE__ */ jsx(
          "td",
          {
            className: cn(
              "px-5 py-2.5 font-mono text-[11.5px]",
              c === "\u2014" ? "text-slate-custom" : "text-paper/90",
              ACCESS[i]?.featured && "bg-gold/[0.03]"
            ),
            children: c
          },
          i
        ))
      ] }, label)) })
    ] }) }),
    /* @__PURE__ */ jsx(Reveal, { y: false, children: /* @__PURE__ */ jsxs("div", { className: "mt-6 grid gap-px border border-hair bg-hair lg:grid-cols-[minmax(0,1fr)_420px]", children: [
      /* @__PURE__ */ jsxs("div", { className: "bg-panel px-5 py-6", children: [
        /* @__PURE__ */ jsx("p", { className: "label-xs text-gold", children: "Index keys" }),
        /* @__PURE__ */ jsx("p", { className: "mt-3 max-w-[44ch] font-display text-[clamp(1.4rem,2.6vw,2rem)] leading-[1.1] text-paper", children: "Keys are issued to members of the Bar, to the Bench, and to registries \u2014 by name, and after a look at the roll." }),
        /* @__PURE__ */ jsx("p", { className: "mt-3 max-w-[58ch] text-[12.5px] leading-[1.7] text-muted", children: "Send the enrolment number or the department. A person reads every request; the corpus is not sold to anyone who intends to let it speak for itself." })
      ] }),
      /* @__PURE__ */ jsxs(
        "form",
        {
          onSubmit: (e) => {
            e.preventDefault();
            if (valid) setSent(email.trim());
          },
          className: "flex flex-col justify-center gap-3 bg-cream px-5 py-6",
          children: [
            /* @__PURE__ */ jsxs("label", { className: "flex items-center gap-3 border border-hair bg-panel px-3 py-2.5 transition-colors focus-within:border-gold/60", children: [
              /* @__PURE__ */ jsx(Mail, { className: "h-3.5 w-3.5 text-muted", strokeWidth: 1.7 }),
              /* @__PURE__ */ jsx(
                "input",
                {
                  value: email,
                  onChange: (e) => {
                    setEmail(e.target.value);
                    setSent(null);
                  },
                  placeholder: "counsel@chambers.in",
                  className: "min-w-0 flex-1 bg-transparent font-mono text-[12.5px] text-paper outline-none placeholder:text-muted/70"
                }
              )
            ] }),
            !valid && email.trim().length > 3 && /* @__PURE__ */ jsx("p", { className: "font-mono text-[10.5px] text-error/80", children: "that address does not parse" }),
            /* @__PURE__ */ jsx(Btn, { type: "submit", disabled: !valid, className: "w-full", children: "Request a key" }),
            /* @__PURE__ */ jsx("p", { className: "min-h-[16px] font-mono text-[10.5px] text-muted", children: sent ? /* @__PURE__ */ jsxs("span", { className: "text-success", children: [
              "logged \xB7 ",
              sent,
              " \xB7 you will hear from a person"
            ] }) : "no card, no trial meter \xB7 reply within two working days" })
          ]
        }
      )
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
