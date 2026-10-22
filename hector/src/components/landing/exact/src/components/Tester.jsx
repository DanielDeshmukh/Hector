import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { ScanLine, TriangleAlert, Regex, Check } from "lucide-react";
import { cn } from "../utils/cn";
import { Btn, Reveal, Tag, WideHead, WideSection } from "./ui";
import { BOUNDARY_SOURCE, canon, regexUnits } from "../lib/text";
import { byId } from "../data/corpus";
import { useCopy } from "../lib/hooks";
const MESSY = `THE BHARATIYA NYAYA SANHITA, 2023
(46 of 2023, 25.12.2023)
101. Culpable homicide.\u2014Whoever causes death by doing an act with the intention of causing death, or with such intention as aforesaid, shall be punishable with imprisonment for life or with fine which may extend to ten years.
102. Murder.\u2014Except in the cases hereinafter excepted, culpable homicide is murder,\u2014
first, if the act by which the death is caused is done with the intention of causing death;
secondly, if it is done with the intention of causing such bodily injury as the offender knows to be likely to cause death.
Exception 1.\u2014Culpable homicide is not murder if the offender, whilst deprived of the power of self-control by grave and sudden provocation, causes the death of the person who gave the provocation.
Illustration.\u2014A is provoked by B and kills him in the heat of passion.
Short title and commencement.
103. Punishment for murder.\u2014Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.`;
const CLEAN = [byId("ipc-124a"), byId("bns-152")].map((s) => canon(s)).join("\n");
const NOT_LAW = `Memorandum for the learned Senior:
Kindly settle the bail application. The Court took a view on 14.08 that the proviso to Section 37 NDPS is not merely procedural. Three grounds, two of which are already in thePaper. Revisiting the citation is not necessary at this stage.`;
function TesterSection() {
  const [text, setText] = useState(MESSY);
  const { copied, copy } = useCopy();
  const units = useMemo(() => regexUnits(text), [text]);
  const covered = units.reduce((n, u) => n + u.text.length, 0);
  const residual = Math.max(0, text.length - covered);
  const totalAnchors = units.reduce(
    (a, u) => ({
      proviso: a.proviso + u.anchors.proviso,
      exception: a.exception + u.anchors.exception,
      explanation: a.explanation + u.anchors.explanation,
      illustration: a.illustration + u.anchors.illustration,
      clause: a.clause + u.anchors.clause
    }),
    { proviso: 0, exception: 0, explanation: 0, illustration: 0, clause: 0 }
  );
  return /* @__PURE__ */ jsxs(WideSection, { id: "tester", children: [
    /* @__PURE__ */ jsx(
      WideHead,
      {
        no: "03A",
        kicker: "Insertion \xB7 live boundary test",
        title: /* @__PURE__ */ jsxs(Fragment, { children: [
          "Paste your own text.",
          /* @__PURE__ */ jsx("span", { className: "block italic text-gold-light", children: "Run the grammar on it." })
        ] }),
        lede: /* @__PURE__ */ jsx(Fragment, { children: "The pattern compiled above is running in this page. Drop in a section, a page torn out of a bare act, or a memorandum that is not law at all \u2014 and read what the splitter decides, including what it refuses to treat as a chunk." }),
        controls: /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-2 lg:justify-end", children: [
          /* @__PURE__ */ jsx(Btn, { variant: "ghost", onClick: () => setText(MESSY), children: "Messy bare-act page" }),
          /* @__PURE__ */ jsx(Btn, { variant: "ghost", onClick: () => setText(CLEAN), children: "Two mapped sections" }),
          /* @__PURE__ */ jsx(Btn, { variant: "quiet", onClick: () => setText(NOT_LAW), children: "Something that isn\u2019t law" })
        ] })
      }
    ),
    /* @__PURE__ */ jsxs("div", { className: "mt-10 grid gap-px bg-hair lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]", children: [
      /* @__PURE__ */ jsxs("div", { className: "bg-cream", children: [
        /* @__PURE__ */ jsxs("div", { className: "flex items-center justify-between border-b border-hair bg-panel-2 px-4 py-2.5", children: [
          /* @__PURE__ */ jsxs("span", { className: "flex items-center gap-2 label-xs text-silver", children: [
            /* @__PURE__ */ jsx(Regex, { className: "h-3.5 w-3.5 text-gold", strokeWidth: 1.5 }),
            "input \xB7 as printed"
          ] }),
          /* @__PURE__ */ jsxs("span", { className: "font-mono text-[10.5px] text-muted", children: [
            text.length.toLocaleString("en-IN"),
            " ch"
          ] })
        ] }),
        /* @__PURE__ */ jsx(
          "textarea",
          {
            value: text,
            spellCheck: false,
            onChange: (e) => setText(e.target.value),
            className: "h-[360px] w-full resize-none bg-transparent px-4 py-4 font-mono text-[12px] leading-[1.9] text-paper/90 outline-none placeholder:text-muted",
            placeholder: "Paste a section here\u2026"
          }
        ),
        /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-2 border-t border-hair bg-panel-2 px-4 py-2.5", children: [
          /* @__PURE__ */ jsxs("span", { className: "font-mono text-[10.5px] text-muted", children: [
            "units ",
            units.length,
            " \xB7 covered ",
            covered.toLocaleString("en-IN"),
            " ch \xB7 unabsorbed ",
            residual.toLocaleString("en-IN"),
            " ch"
          ] }),
          /* @__PURE__ */ jsxs(
            "button",
            {
              onClick: () => copy(BOUNDARY_SOURCE, "src"),
              className: "ml-auto flex items-center gap-1.5 border border-hair px-2 py-1 font-mono text-[10.5px] text-silver transition-colors hover:border-gold/60 hover:text-gold",
              children: [
                copied === "src" ? /* @__PURE__ */ jsx(Check, { className: "h-3 w-3 text-success" }) : /* @__PURE__ */ jsx(ScanLine, { className: "h-3 w-3" }),
                copied === "src" ? "source copied" : "copy pattern"
              ]
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxs("div", { className: "bg-cream", children: [
        /* @__PURE__ */ jsxs("div", { className: "flex items-center justify-between border-b border-hair bg-panel-2 px-4 py-2.5", children: [
          /* @__PURE__ */ jsx("span", { className: "label-xs text-silver", children: "units emitted" }),
          /* @__PURE__ */ jsxs("span", { className: "flex items-center gap-2", children: [
            units.length ? /* @__PURE__ */ jsxs(Tag, { tone: "active", children: [
              /* @__PURE__ */ jsx("span", { className: "h-1 w-1 bg-success" }),
              " boundary-respected"
            ] }) : /* @__PURE__ */ jsxs(Tag, { tone: "repealed", children: [
              /* @__PURE__ */ jsx("span", { className: "h-1 w-1 bg-error" }),
              " refused"
            ] }),
            /* @__PURE__ */ jsx("span", { className: "font-mono text-[10.5px] text-muted", children: "/gm" })
          ] })
        ] }),
        units.length === 0 ? /* @__PURE__ */ jsxs("div", { className: "flex h-[360px] flex-col justify-center px-6", children: [
          /* @__PURE__ */ jsxs("p", { className: "flex items-center gap-2 font-display text-[26px] leading-tight text-paper", children: [
            /* @__PURE__ */ jsx(TriangleAlert, { className: "h-5 w-5 text-error/80", strokeWidth: 1.5 }),
            "The grammar found no section anchor."
          ] }),
          /* @__PURE__ */ jsx("p", { className: "mt-3 max-w-[54ch] text-[13px] leading-[1.7] text-silver", children: "Nothing was invented to fill the gap. Input that is not drafted as a numbered provision does not become a unit, and a corpus that cannot be opened at a section boundary is not a statute index \u2014 it is a pile." }),
          /* @__PURE__ */ jsxs("p", { className: "mt-4 border-l-2 border-error/50 pl-3 font-mono text-[11.5px] leading-relaxed text-muted", children: [
            "expected: a line beginning with a section number and a marginal note, e.g.",
            /* @__PURE__ */ jsx("br", {}),
            /* @__PURE__ */ jsx("span", { className: "text-gold-light", children: "103. Punishment for murder.\u2014" }),
            "Whoever commits murder\u2026"
          ] })
        ] }) : /* @__PURE__ */ jsx("ol", { className: "max-h-[360px] divide-y divide-hair/70 overflow-y-auto", children: units.map((u) => /* @__PURE__ */ jsxs("li", { className: "group px-4 py-3.5 transition-colors duration-200 hover:bg-panel/60", children: [
          /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-x-3 gap-y-1", children: [
            /* @__PURE__ */ jsxs("span", { className: "font-mono text-[11px] text-gold", children: [
              "u",
              String(u.index + 1).padStart(2, "0")
            ] }),
            /* @__PURE__ */ jsxs("span", { className: "font-mono text-[12.5px] text-paper", children: [
              "\xA7 ",
              u.number
            ] }),
            /* @__PURE__ */ jsx("span", { className: "truncate text-[13px] italic text-silver/90", children: u.marginal || "\u2014" }),
            /* @__PURE__ */ jsxs("span", { className: "ml-auto font-mono text-[10.5px] text-muted", children: [
              "off ",
              u.start,
              "\u2013",
              u.end,
              " \xB7 ",
              u.text.length,
              " ch"
            ] })
          ] }),
          /* @__PURE__ */ jsx("p", { className: "mt-1.5 line-clamp-2 whitespace-pre-wrap font-mono text-[11.5px] leading-[1.7] text-muted transition-colors duration-200 group-hover:text-silver/85", children: u.text.replace(/\s+/g, " ").trim() }),
          /* @__PURE__ */ jsx("p", { className: "mt-1.5 flex flex-wrap gap-x-3 font-mono text-[10.5px]", children: [
            ["clause", u.anchors.clause],
            ["proviso", u.anchors.proviso],
            ["exception", u.anchors.exception],
            ["explanation", u.anchors.explanation],
            ["illustration", u.anchors.illustration]
          ].map(([k, v]) => /* @__PURE__ */ jsxs("span", { className: cn(v ? "text-gold/80" : "text-slate-custom"), children: [
            k,
            " ",
            v
          ] }, k)) })
        ] }, u.index)) }),
        /* @__PURE__ */ jsx(Reveal, { y: false, children: /* @__PURE__ */ jsx("div", { className: "grid grid-cols-2 gap-px border-t border-hair bg-hair sm:grid-cols-5", children: [
          ["units", String(units.length)],
          ["provisos kept", String(totalAnchors.proviso)],
          ["exceptions kept", String(totalAnchors.exception)],
          ["explanations kept", String(totalAnchors.explanation)],
          ["illustrations kept", String(totalAnchors.illustration)]
        ].map(([k, v]) => /* @__PURE__ */ jsxs("div", { className: "bg-cream px-3 py-2.5", children: [
          /* @__PURE__ */ jsx("p", { className: "label-xs text-muted", children: k }),
          /* @__PURE__ */ jsx("p", { className: cn("mt-1 font-display text-[20px] leading-none", v === "0" ? "text-slate-custom" : "text-gold-light"), children: v })
        ] }, k)) }) }),
        /* @__PURE__ */ jsxs("p", { className: "border-t border-hair bg-panel px-4 py-2.5 font-mono text-[10.5px] leading-relaxed text-muted", children: [
          "unabsorbed matter (",
          residual.toLocaleString("en-IN"),
          " ch) is text lying outside any anchor \u2014 running heads, the extent note, page furniture. It is dropped, never promoted to a chunk of its own; matter between two anchors belongs to the unit it sits in."
        ] })
      ] })
    ] })
  ] });
}
export {
  TesterSection
};
