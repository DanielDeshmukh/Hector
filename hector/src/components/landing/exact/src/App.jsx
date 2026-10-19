"use client";
import { jsx, jsxs } from "react/jsx-runtime";
import { Hero } from "./components/Hero";
import { CorpusSection } from "./components/Corpus";
import { ChunkingSection, GrammarSection } from "./components/Grammar";
import { TesterSection } from "./components/Tester";
import { ComparisonSection } from "./components/Comparison";
import { BatchSection } from "./components/Batch";
import { AccessSection, FaqSection, ForWhomSection, LedgerSection } from "./components/Practice";
import { Backdrop, Colophon, Masthead } from "./components/Chrome";
import { Reveal } from "./components/ui";
function Doctrine() {
  return /* @__PURE__ */ jsxs("section", { className: "relative overflow-hidden border-t border-hair bg-ink", children: [
    /* @__PURE__ */ jsx("div", { className: "absolute inset-0 rule-grid opacity-60", "aria-hidden": true }),
    /* @__PURE__ */ jsxs("div", { className: "relative mx-auto grid max-w-[1400px] gap-10 px-5 py-16 sm:px-8 md:py-20 lg:grid-cols-12", children: [
      /* @__PURE__ */ jsxs("div", { className: "lg:col-span-2", children: [
        /* @__PURE__ */ jsx("p", { className: "label-xs text-gold", children: "Doctrine" }),
        /* @__PURE__ */ jsxs("p", { className: "mt-3 font-mono text-[10.5px] leading-relaxed text-muted", children: [
          "Art. I \u2014",
          /* @__PURE__ */ jsx("br", {}),
          "of the split"
        ] })
      ] }),
      /* @__PURE__ */ jsxs("div", { className: "lg:col-span-10", children: [
        /* @__PURE__ */ jsx(Reveal, { y: false, children: /* @__PURE__ */ jsxs("p", { className: "font-display text-[clamp(1.9rem,5.2vw,4.4rem)] leading-[0.95] tracking-[-0.03em] text-paper", children: [
          "A proviso detached from its section",
          /* @__PURE__ */ jsxs("span", { className: "block text-silver/70", children: [
            "is ",
            /* @__PURE__ */ jsx("span", { className: "italic text-gold-light", children: "a different law" }),
            " \u2014 and it is still quoted as though it were the whole of it."
          ] })
        ] }) }),
        /* @__PURE__ */ jsx("div", { className: "mt-10 grid gap-px bg-hair md:grid-cols-3", children: [
          ["not a paraphrase problem", "The model is not inventing the condition. The condition was never in the window it was given."],
          ["not a model-size problem", "A larger context window stores the same defect more comfortably. Retrieval still decides what is read."],
          ["a boundary problem", "Boundaries in a statute are drawn by text: a number, a marginal note, an em-dash. Regex reads text."]
        ].map(([h, b]) => /* @__PURE__ */ jsxs("div", { className: "group bg-ink px-5 py-5 transition-colors duration-300 hover:bg-panel/70", children: [
          /* @__PURE__ */ jsx("p", { className: "font-mono text-[11px] uppercase tracking-[0.18em] text-silver transition-colors group-hover:text-gold-light", children: h }),
          /* @__PURE__ */ jsx("p", { className: "mt-2.5 max-w-[36ch] text-[13.5px] leading-[1.7] text-muted transition-colors group-hover:text-silver", children: b }),
          /* @__PURE__ */ jsx("span", { className: "mt-4 block h-px w-8 bg-slate-custom transition-all duration-500 group-hover:w-full group-hover:bg-gold/60" })
        ] }, h)) }),
        /* @__PURE__ */ jsxs("p", { className: "mt-8 max-w-[86ch] border-t border-hair pt-6 text-[14px] leading-[1.8] text-silver/90", children: [
          "Retrieval-augmented, stated plainly: a model only ever reads what the index hands it. So the hand-off is the whole discipline \u2014 hand over a section, complete, with its provisos and its carve-outs and its marginal note attached, and hand over the offset where each sentence was taken from.",
          /* @__PURE__ */ jsx("span", { className: "text-gold-light", children: " Hector exists to make that one step deterministic." })
        ] })
      ] })
    ] })
  ] });
}
function App() {
  return /* @__PURE__ */ jsxs("div", { className: "zip-landing relative min-h-screen", children: [
    /* @__PURE__ */ jsx(Backdrop, {}),
    /* @__PURE__ */ jsx(Masthead, {}),
    /* @__PURE__ */ jsxs("main", { className: "relative", children: [
      /* @__PURE__ */ jsx(Hero, {}),
      /* @__PURE__ */ jsx(CorpusSection, {}),
      /* @__PURE__ */ jsx(Doctrine, {}),
      /* @__PURE__ */ jsx(GrammarSection, {}),
      /* @__PURE__ */ jsx(ChunkingSection, {}),
      /* @__PURE__ */ jsx(TesterSection, {}),
      /* @__PURE__ */ jsx(ComparisonSection, {}),
      /* @__PURE__ */ jsx(BatchSection, {}),
      /* @__PURE__ */ jsx(LedgerSection, {}),
      /* @__PURE__ */ jsx(ForWhomSection, {}),
      /* @__PURE__ */ jsx(AccessSection, {}),
      /* @__PURE__ */ jsx(FaqSection, {})
    ] }),
    /* @__PURE__ */ jsx(Colophon, {})
  ] });
}
export {
  App as default
};
