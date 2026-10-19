import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { Check, Copy } from "lucide-react";
import { cn } from "../utils/cn";
import { Reveal } from "./ui";
import { CORPUS, MAPPINGS, byId } from "../data/corpus";
import { citationOf, diffWords } from "../lib/text";
import { useCopy } from "../lib/hooks";
const bodyOf = (s) => s.parts.map((p) => p.kind === "section" ? p.text : `${p.label ? `${p.label} ` : ""}${p.text}`).join(" ").replace(/\s+/g, " ").trim();
const sig = (s) => /^article/i.test(s.section) ? s.section : `s. ${s.section}`;
function Marked({ ops, side, only }) {
  const keep = ops.filter((o) => side === "l" ? o.t !== "add" : o.t !== "del");
  const show = only ? keep.filter((o) => o.t !== "same") : keep;
  if (!show.length) return /* @__PURE__ */ jsx("span", { className: "text-muted italic", children: "\u2014 no change on this side \u2014" });
  return /* @__PURE__ */ jsx(Fragment, { children: show.map((o, i) => /* @__PURE__ */ jsxs(
    "span",
    {
      className: cn(
        o.t === "same" ? "text-silver/85" : side === "l" ? "bg-error/[0.10] text-error/85 line-through decoration-error/40" : "bg-gold/[0.16] text-gold-light"
      ),
      children: [
        o.text,
        only && i < show.length - 1 ? " " : ""
      ]
    },
    i
  )) });
}
function Side({
  s,
  ops,
  side,
  only,
  tag
}) {
  const { copied, copy } = useCopy();
  return /* @__PURE__ */ jsxs("div", { children: [
    /* @__PURE__ */ jsx("p", { className: "label-xs text-muted", children: tag }),
    /* @__PURE__ */ jsx("h3", { className: "mt-3 font-display text-[clamp(1.5rem,3vw,2.1rem)] leading-none tracking-[-0.02em] text-paper", children: /^article/i.test(s.section) ? s.section : `Section ${s.section}` }),
    /* @__PURE__ */ jsx("p", { className: "mt-2 text-[13.5px] leading-snug text-silver/85", children: s.note }),
    /* @__PURE__ */ jsxs("p", { className: "mt-3 flex flex-wrap items-center gap-2 font-mono text-[10.5px] text-muted", children: [
      /* @__PURE__ */ jsx("span", { className: "text-gold/85", children: s.act }),
      /* @__PURE__ */ jsx("span", { className: "h-2 w-px bg-hair" }),
      /* @__PURE__ */ jsx("span", { className: s.status === "Active" ? "text-success/80" : "text-error/70", children: s.status })
    ] }),
    /* @__PURE__ */ jsx("div", { className: "mt-6 border-t border-hair pt-5", children: /* @__PURE__ */ jsxs("p", { className: "font-mono text-[12.5px] leading-[1.95] sm:text-[13px]", children: [
      /* @__PURE__ */ jsxs("span", { className: "text-gold", children: [
        sig(s),
        ". ",
        s.note,
        ".\u2014"
      ] }),
      /* @__PURE__ */ jsx(Marked, { ops, side, only })
    ] }) }),
    /* @__PURE__ */ jsxs(
      "button",
      {
        onClick: () => copy(citationOf(s), s.id),
        className: "mt-6 flex items-center gap-1.5 font-mono text-[10.5px] text-muted transition-colors hover:text-gold",
        children: [
          copied === s.id ? /* @__PURE__ */ jsx(Check, { className: "h-3 w-3 text-success" }) : /* @__PURE__ */ jsx(Copy, { className: "h-3 w-3", strokeWidth: 1.7 }),
          citationOf(s)
        ]
      }
    )
  ] });
}
function ComparisonSection() {
  const [idx, setIdx] = useState(0);
  const [only, setOnly] = useState(false);
  const [custom, setCustom] = useState(null);
  const { copied, copy } = useCopy();
  const m = MAPPINGS[idx];
  const left = custom ? byId(custom.l) : byId(m.from);
  const right = custom ? byId(custom.r) : byId(m.to);
  const ops = useMemo(() => diffWords(bodyOf(left), bodyOf(right)), [left, right]);
  const changed = ops.filter((o) => o.t !== "same").length;
  return /* @__PURE__ */ jsx("section", { id: "compare", className: "relative border-t border-hair", children: /* @__PURE__ */ jsxs("div", { className: "mx-auto w-full max-w-[1080px] px-5 py-16 sm:px-8 md:py-24", children: [
    /* @__PURE__ */ jsx(Reveal, { y: false, children: /* @__PURE__ */ jsxs("div", { className: "flex flex-col gap-5 border-b border-hair pb-6 lg:flex-row lg:items-end lg:justify-between", children: [
      /* @__PURE__ */ jsxs("div", { children: [
        /* @__PURE__ */ jsx("p", { className: "label-xs text-gold", children: "04 \xB7 Section comparison" }),
        /* @__PURE__ */ jsxs("h2", { className: "mt-4 max-w-[24ch] font-display text-[clamp(1.9rem,4.4vw,3.1rem)] leading-[0.94] tracking-[-0.025em] text-paper", children: [
          "The old text. The new text.",
          /* @__PURE__ */ jsx("span", { className: "block italic text-gold-light", children: "Nothing in between." })
        ] })
      ] }),
      /* @__PURE__ */ jsx("p", { className: "max-w-[40ch] text-[13.5px] leading-[1.7] text-silver", children: "One pair at a time, printed whole, with the changed words marked and the relation named." })
    ] }) }),
    /* @__PURE__ */ jsx("div", { className: "mt-8 border-b border-hair", children: custom ? /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-end gap-3 pb-4", children: [
      [
        ["l", "prior text"],
        ["r", "operative text"]
      ].map(([k, label]) => /* @__PURE__ */ jsxs("label", { className: "min-w-[240px] flex-1", children: [
        /* @__PURE__ */ jsx("span", { className: "label-xs text-muted", children: label }),
        /* @__PURE__ */ jsx(
          "select",
          {
            value: custom[k],
            onChange: (e) => setCustom((c) => ({ ...c, [k]: e.target.value })),
            className: "mt-2 w-full border-b border-hair bg-transparent pb-2 font-mono text-[12px] text-paper outline-none transition-colors focus:border-gold",
            children: CORPUS.filter((s) => s.id !== custom[k === "l" ? "r" : "l"]).map((s) => /* @__PURE__ */ jsxs("option", { value: s.id, className: "bg-panel text-paper", children: [
              s.code,
              " ",
              sig(s),
              " \u2014 ",
              s.note
            ] }, s.id))
          }
        )
      ] }, k)),
      /* @__PURE__ */ jsx(
        "button",
        {
          onClick: () => setCustom(null),
          className: "pb-2 font-mono text-[11px] text-muted underline-offset-4 transition-colors hover:text-gold hover:underline",
          children: "back to the mapped pairs"
        }
      )
    ] }) : /* @__PURE__ */ jsxs("div", { className: "-mx-1 flex gap-7 overflow-x-auto px-1", children: [
      MAPPINGS.map((mp, i) => {
        const a = byId(mp.from);
        const b = byId(mp.to);
        const on = i === idx;
        return /* @__PURE__ */ jsxs(
          "button",
          {
            onClick: () => setIdx(i),
            className: cn(
              "group relative shrink-0 pb-4 text-left transition-opacity duration-200",
              on ? "opacity-100" : "opacity-55 hover:opacity-90"
            ),
            children: [
              /* @__PURE__ */ jsxs("span", { className: "flex items-center gap-2 font-mono text-[11.5px] whitespace-nowrap", children: [
                /* @__PURE__ */ jsxs("span", { className: on ? "text-gold" : "text-silver", children: [
                  a.code,
                  " ",
                  sig(a)
                ] }),
                /* @__PURE__ */ jsx("span", { className: "text-slate-custom", children: "\u21C4" }),
                /* @__PURE__ */ jsxs("span", { className: on ? "text-gold-light" : "text-paper/80", children: [
                  b.code,
                  " ",
                  sig(b)
                ] })
              ] }),
              /* @__PURE__ */ jsx("span", { className: "mt-1.5 block font-mono text-[10px] text-muted", children: mp.relation }),
              /* @__PURE__ */ jsx(
                "span",
                {
                  className: cn(
                    "absolute inset-x-0 bottom-0 h-px origin-left bg-gold transition-transform duration-300",
                    on ? "scale-x-100" : "scale-x-0 group-hover:scale-x-50"
                  )
                }
              )
            ]
          },
          `${mp.from}-${mp.to}`
        );
      }),
      /* @__PURE__ */ jsx(
        "button",
        {
          onClick: () => setCustom({ l: left.id, r: right.id }),
          className: "shrink-0 pb-4 font-mono text-[11px] text-muted transition-colors hover:text-gold",
          children: "+ any two provisions"
        }
      )
    ] }) }),
    /* @__PURE__ */ jsxs("div", { className: "grid gap-10 pt-10 md:grid-cols-2 md:gap-0", children: [
      /* @__PURE__ */ jsx("div", { className: "md:border-r md:pr-10", children: /* @__PURE__ */ jsx(Side, { s: left, ops, side: "l", only, tag: custom ? "selected \xB7 a" : "prior text" }) }),
      /* @__PURE__ */ jsx("div", { className: "md:pl-10", children: /* @__PURE__ */ jsx(Side, { s: right, ops, side: "r", only, tag: custom ? "selected \xB7 b" : "operative text" }) })
    ] }),
    /* @__PURE__ */ jsxs("div", { className: "mt-12 flex flex-col gap-5 border-t border-hair pt-6 md:flex-row md:items-start md:gap-10", children: [
      /* @__PURE__ */ jsxs("div", { className: "flex shrink-0 items-center gap-3", children: [
        /* @__PURE__ */ jsx("span", { className: "border border-gold/45 px-2 py-1 font-mono text-[10.5px] tracking-wide text-gold-light", children: custom ? "unmapped" : m.relation }),
        !custom && /* @__PURE__ */ jsxs("span", { className: "flex items-center gap-1.5 font-mono text-[10.5px] text-muted", children: [
          [0, 1, 2].map((n) => /* @__PURE__ */ jsx(
            "span",
            {
              className: cn(
                "h-2.5 w-[3px]",
                n < (m.risk === "low" ? 1 : m.risk === "medium" ? 2 : 3) ? m.risk === "low" ? "bg-success" : m.risk === "medium" ? "bg-warning" : "bg-error" : "bg-slate-custom"
              )
            },
            n
          )),
          m.risk
        ] })
      ] }),
      /* @__PURE__ */ jsx("p", { className: "flex-1 text-[13.5px] leading-[1.75] text-silver", children: custom ? "Manual pairing. The index asserts no relation here \u2014 it returns both texts and lets you read them against each other." : m.delta }),
      /* @__PURE__ */ jsx(
        "button",
        {
          onClick: () => setOnly((v) => !v),
          className: cn(
            "shrink-0 self-start font-mono text-[11px] underline-offset-4 transition-colors hover:underline",
            only ? "text-gold" : "text-muted"
          ),
          children: only ? `changes only \xB7 ${changed} runs` : "changes only"
        }
      ),
      /* @__PURE__ */ jsxs(
        "button",
        {
          onClick: () => copy(`${citationOf(left)}  \u21C4  ${citationOf(right)}`, "pair"),
          className: "flex shrink-0 items-center gap-1.5 self-start font-mono text-[11px] text-muted transition-colors hover:text-gold",
          children: [
            copied === "pair" ? /* @__PURE__ */ jsx(Check, { className: "h-3 w-3 text-success" }) : /* @__PURE__ */ jsx(Copy, { className: "h-3 w-3", strokeWidth: 1.7 }),
            "copy both citations"
          ]
        }
      )
    ] })
  ] }) });
}
export {
  ComparisonSection
};
