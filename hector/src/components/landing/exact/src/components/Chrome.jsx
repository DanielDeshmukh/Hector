import { jsx, jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Scale, ArrowRight, ArrowDown, ScanLine } from "lucide-react";
import { cn } from "../utils/cn";
import { useActiveSection, useScrollProgress } from "../lib/hooks";
import { MAPPINGS, byId } from "../data/corpus";
import { citationOf } from "../lib/text";
import { ALL_ACTS, INDEXED_ACTS } from "../data/acts";
import { Btn } from "./ui";
const NAV = [
  { id: "corpus", label: "Corpus" },
  { id: "grammar", label: "Grammar" },
  { id: "chunking", label: "Chunking" },
  { id: "tester", label: "Tester" },
  { id: "compare", label: "Compare" },
  { id: "batch", label: "Batch" },
  { id: "ledger", label: "Ledger" },
  { id: "access", label: "Access" }
];
function Backdrop() {
  const [y, setY] = useState(0);
  useEffect(() => {
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => setY(window.scrollY));
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);
  return /* @__PURE__ */ jsxs("div", { "aria-hidden": true, className: "pointer-events-none fixed inset-0 -z-10 overflow-hidden", children: [
    /* @__PURE__ */ jsx("div", { className: "absolute inset-0 bg-cream" }),
    /* @__PURE__ */ jsx("div", { className: "absolute inset-0 rule-grid" }),
    /* @__PURE__ */ jsx("div", { className: "absolute inset-0 ledger-lines opacity-70" }),
    /* @__PURE__ */ jsx(
      "div",
      {
        className: "absolute inset-x-0 top-0 h-[70vh]",
        style: {
          background: "radial-gradient(78% 58% at 50% -14%, rgba(201,169,98,0.085), rgba(17,19,21,0) 68%)",
          transform: `translate3d(0, ${y * -0.06}px, 0)`
        }
      }
    ),
    /* @__PURE__ */ jsx(
      "div",
      {
        className: "absolute inset-x-0 bottom-0 h-[55vh]",
        style: { background: "linear-gradient(to top, rgba(58,70,89,0.16), rgba(17,19,21,0))" }
      }
    ),
    /* @__PURE__ */ jsx("div", { className: "absolute inset-y-0 left-[max(0px,calc(50%-700px))] w-px bg-silver/[0.09]" }),
    /* @__PURE__ */ jsx("div", { className: "absolute inset-y-0 right-[max(0px,calc(50%-700px))] w-px bg-silver/[0.09]" }),
    /* @__PURE__ */ jsx("div", { className: "grain-layer absolute inset-0 opacity-[0.055] mix-blend-soft-light" })
  ] });
}
function Clock() {
  const [t, setT] = useState(() => /* @__PURE__ */ new Date());
  useEffect(() => {
    const id = window.setInterval(() => setT(/* @__PURE__ */ new Date()), 1e3);
    return () => window.clearInterval(id);
  }, []);
  let s = "";
  try {
    s = t.toLocaleTimeString("en-GB", { hour12: false, timeZone: "Asia/Kolkata" });
  } catch {
    s = t.toTimeString().slice(0, 8);
  }
  return /* @__PURE__ */ jsxs("span", { className: "hidden items-center gap-2 font-mono text-[10.5px] text-muted 2xl:flex", children: [
    /* @__PURE__ */ jsx("span", { className: "h-1 w-1 bg-gold/70" }),
    /* @__PURE__ */ jsx("span", { suppressHydrationWarning: true, children: s }),
    " IST"
  ] });
}
function Masthead() {
  const p = useScrollProgress();
  const active = useActiveSection(NAV.map((n) => n.id));
  const [compact, setCompact] = useState(false);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const onScroll = () => setCompact(window.scrollY > 70);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return /* @__PURE__ */ jsxs(
    "header",
    {
      className: cn(
        "fixed inset-x-0 top-0 z-50 border-b bg-cream/96 transition-all duration-500",
        compact ? "border-hair" : "border-transparent"
      ),
      children: [
        /* @__PURE__ */ jsxs("div", { className: "mx-auto flex max-w-[1400px] items-center gap-6 px-5 sm:px-8", children: [
          /* @__PURE__ */ jsxs("a", { href: "#top", className: "group flex shrink-0 items-center gap-3 py-3.5", children: [
            /* @__PURE__ */ jsx("span", { className: "grid h-8 w-8 place-items-center border border-gold/50 text-gold transition-colors duration-300 group-hover:bg-gold group-hover:text-ink", children: /* @__PURE__ */ jsx(Scale, { className: "h-[15px] w-[15px]", strokeWidth: 1.4 }) }),
            /* @__PURE__ */ jsxs("span", { className: "flex items-baseline gap-2", children: [
              /* @__PURE__ */ jsx("span", { className: "font-display text-[19px] font-semibold uppercase leading-none tracking-[0.3em] text-paper", children: "Hector" }),
              /* @__PURE__ */ jsx("span", { className: "hidden label-xs text-muted sm:inline", children: "grammar 4.2" })
            ] })
          ] }),
          /* @__PURE__ */ jsx("nav", { className: "ml-auto hidden items-center gap-0.5 xl:flex", children: NAV.map((n) => /* @__PURE__ */ jsxs(
            "a",
            {
              href: `#${n.id}`,
              className: cn(
                "group relative flex items-baseline gap-1.5 px-3 py-2 label-xs transition-colors duration-200",
                active === n.id ? "text-gold" : "text-silver hover:text-paper"
              ),
              children: [
                /* @__PURE__ */ jsx("span", { className: cn("mr-0.5 h-1 w-1 translate-y-[-1px]", active === n.id ? "bg-gold" : "bg-slate-custom group-hover:bg-silver") }),
                n.label,
                /* @__PURE__ */ jsx(
                  "span",
                  {
                    className: cn(
                      "absolute inset-x-2 -bottom-px h-px origin-left bg-gold transition-transform duration-300",
                      active === n.id ? "scale-x-100" : "scale-x-0 group-hover:scale-x-100"
                    )
                  }
                )
              ]
            },
            n.id
          )) }),
          /* @__PURE__ */ jsxs("div", { className: "ml-auto flex items-center gap-4 lg:ml-0", children: [
            /* @__PURE__ */ jsx(Clock, {}),
            /* @__PURE__ */ jsxs("span", { className: "hidden items-center gap-2 label-xs text-muted xl:flex", children: [
              /* @__PURE__ */ jsxs("span", { className: "relative flex h-1.5 w-1.5", children: [
                /* @__PURE__ */ jsx("span", { className: "absolute inline-flex h-full w-full animate-ping bg-success/60" }),
                /* @__PURE__ */ jsx("span", { className: "relative inline-flex h-1.5 w-1.5 bg-success" })
              ] }),
              INDEXED_ACTS,
              " acts indexed"
            ] }),
            /* @__PURE__ */ jsx("a", { href: "/search", className: "hidden sm:block", children: /* @__PURE__ */ jsxs(Btn, { className: "px-3.5 py-2", children: [
              "Try Hector",
              /* @__PURE__ */ jsx(ArrowRight, { className: "h-3 w-3 transition-transform duration-200 group-hover:translate-x-0.5" })
            ] }) }),
            /* @__PURE__ */ jsx(
              "button",
              {
                onClick: () => setOpen((o) => !o),
                "aria-label": "Toggle navigation",
                className: "grid h-8 w-8 place-items-center border border-hair text-silver xl:hidden",
                children: /* @__PURE__ */ jsx(ScanLine, { className: "h-4 w-4", strokeWidth: 1.5 })
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ jsx("div", { className: "relative h-px w-full bg-hair/60", children: /* @__PURE__ */ jsx(
          "div",
          {
            className: "h-full bg-gold/80",
            style: { width: `${Math.max(0.5, p * 100)}%`, transition: "width .12s linear" }
          }
        ) }),
        open && /* @__PURE__ */ jsx("div", { className: "border-t border-hair bg-panel px-5 pb-4 xl:hidden", children: /* @__PURE__ */ jsx("div", { className: "grid grid-cols-2 gap-x-6", children: NAV.map((n, i) => /* @__PURE__ */ jsxs(
          "a",
          {
            href: `#${n.id}`,
            onClick: () => setOpen(false),
            className: "flex items-baseline gap-2 border-b border-hair/70 py-2.5 font-mono text-[12px] text-silver",
            children: [
              /* @__PURE__ */ jsx("span", { className: "text-[9px] text-muted", children: String(i + 1).padStart(2, "0") }),
              n.label
            ]
          },
          n.id
        )) }) })
      ]
    }
  );
}
function Ticker() {
  const items = MAPPINGS.map((m) => {
    const a = byId(m.from);
    const b = byId(m.to);
    return `${citationOf(a)}  \u21C4  ${citationOf(b)}  \xB7  ${m.relation}`;
  });
  const tail = ALL_ACTS.filter((a) => a.repeals).slice(0, 6).map((a) => `${a.code} repeals ${a.repeals?.split(",")[0]}`.trim());
  const row = [...items, ...tail];
  return /* @__PURE__ */ jsxs("div", { className: "group relative overflow-hidden border-y border-hair bg-panel-2/70", children: [
    /* @__PURE__ */ jsx("div", { className: "flex w-max animate-marquee items-center whitespace-nowrap group-hover:[animation-play-state:paused]", children: [0, 1].map((dup) => /* @__PURE__ */ jsx("div", { className: "flex items-center", "aria-hidden": dup === 1, children: row.map((t, i) => /* @__PURE__ */ jsxs("span", { className: "flex items-center font-mono text-[11px] text-muted", children: [
      /* @__PURE__ */ jsx("span", { className: "px-5 py-2.5 transition-colors duration-200 hover:text-gold", children: t }),
      /* @__PURE__ */ jsx("span", { className: "h-3 w-px bg-hair" })
    ] }, `${dup}-${i}`)) }, dup)) }),
    /* @__PURE__ */ jsx("div", { className: "pointer-events-none absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-cream to-transparent" }),
    /* @__PURE__ */ jsx("div", { className: "pointer-events-none absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-cream to-transparent" })
  ] });
}
function Colophon() {
  return /* @__PURE__ */ jsxs("footer", { className: "relative border-t border-hair bg-ink", children: [
    /* @__PURE__ */ jsxs("div", { className: "mx-auto max-w-[1400px] px-5 py-16 sm:px-8", children: [
      /* @__PURE__ */ jsxs("div", { className: "grid gap-12 lg:grid-cols-12", children: [
        /* @__PURE__ */ jsxs("div", { className: "lg:col-span-5", children: [
          /* @__PURE__ */ jsx("p", { className: "label-xs text-gold", children: "Ad finem" }),
          /* @__PURE__ */ jsxs("p", { className: "mt-5 font-display text-[clamp(1.9rem,3.6vw,3rem)] leading-[1.02] tracking-[-0.02em] text-paper", children: [
            "The statute says what it says.",
            /* @__PURE__ */ jsx("span", { className: "block text-silver/70 italic", children: "Hector only refuses to cut it up." })
          ] }),
          /* @__PURE__ */ jsxs("div", { className: "mt-8 flex flex-wrap items-center gap-3", children: [
            /* @__PURE__ */ jsx("a", { href: "#corpus", children: /* @__PURE__ */ jsxs(Btn, { children: [
              "Open the corpus",
              /* @__PURE__ */ jsx(ArrowDown, { className: "h-3 w-3" })
            ] }) }),
            /* @__PURE__ */ jsx("a", { href: "/search", children: /* @__PURE__ */ jsx(Btn, { variant: "ghost", children: "Try Hector" }) })
          ] })
        ] }),
        /* @__PURE__ */ jsxs("div", { className: "grid gap-8 sm:grid-cols-3 lg:col-span-7", children: [
          /* @__PURE__ */ jsx(
            FooterCol,
            {
              title: "Product",
              links: [
                ["Regex boundary grammar", "#grammar"],
                ["Section comparison", "#compare"],
                ["Batch runs", "#batch"],
                ["38 bare acts", "#corpus"]
              ]
            }
          ),
          /* @__PURE__ */ jsx(
            FooterCol,
            {
              title: "Practice areas",
              links: [
                ["Criminal \xB7 BNS / BNSS / BSA", "#corpus"],
                ["Civil \xB7 CPC / ICA / SRA", "#corpus"],
                ["Family \xB7 HMA / PWDVA", "#corpus"],
                ["Regulatory \xB7 NDPS / CPA / EPA", "#corpus"]
              ]
            }
          ),
          /* @__PURE__ */ jsx(
            FooterCol,
            {
              title: "Corpus",
              links: [
                ["Repeal schedule", "#corpus"],
                ["Citation ledger", "#ledger"],
                ["Short-code collisions", "#corpus"],
                ["Index figures", "#ledger"]
              ]
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxs("div", { className: "mt-14 grid gap-6 border-t border-hair pt-8 lg:grid-cols-12", children: [
        /* @__PURE__ */ jsx("p", { className: "text-[12px] leading-relaxed text-muted lg:col-span-7", children: "Hector is a retrieval instrument for bare acts. Section text on this page is abridged for display; every provision returned by the product is printed with its act, section, clause and the character offset of the source line, and must be read against the authoritative text published by the Legislative Department before it is relied on in any proceeding. Nothing here is legal advice." }),
        /* @__PURE__ */ jsxs("div", { className: "flex flex-col justify-between gap-4 lg:col-span-5 lg:items-end", children: [
          /* @__PURE__ */ jsxs("div", { className: "flex items-center gap-3 font-mono text-[11px] text-muted", children: [
            /* @__PURE__ */ jsx("span", { children: "Hector" }),
            /* @__PURE__ */ jsx("span", { className: "h-3 w-px bg-hair" }),
            /* @__PURE__ */ jsx("span", { children: "Hierarchical Evaluation of Civil-Criminal Textual\u2019s Orchestrator & Retrieval" })
          ] }),
          /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-4 label-xs text-muted", children: [
            /* @__PURE__ */ jsxs("span", { children: [
              "\xA9 ",
              /* @__PURE__ */ jsx("span", { suppressHydrationWarning: true, children: (/* @__PURE__ */ new Date()).getFullYear() }),
              " Hector Legal Systems"
            ] }),
            /* @__PURE__ */ jsx("span", { className: "hidden h-3 w-px bg-hair sm:block" }),
            /* @__PURE__ */ jsx("a", { href: "#top", className: "text-silver transition-colors hover:text-gold", children: "Back to the top" }),
            /* @__PURE__ */ jsx("span", { className: "hidden h-3 w-px bg-hair sm:block" }),
            /* @__PURE__ */ jsx("span", { children: "Terms" }),
            /* @__PURE__ */ jsx("span", { children: "Privacy" })
          ] })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsx("div", { className: "overflow-hidden border-t border-hair py-3", children: /* @__PURE__ */ jsx("p", { className: "whitespace-nowrap text-center font-display text-[13vw] leading-[0.8] tracking-[-0.04em] text-silver/[0.055] select-none", children: "HECTOR \xB7 16 BARE ACTS \xB7 ONE GRAMMAR" }) })
  ] });
}
function FooterCol({ title, links }) {
  return /* @__PURE__ */ jsxs("div", { children: [
    /* @__PURE__ */ jsx("p", { className: "label-xs text-gold", children: title }),
    /* @__PURE__ */ jsx("ul", { className: "mt-4 space-y-0", children: links.map(([label, href]) => /* @__PURE__ */ jsx("li", { children: /* @__PURE__ */ jsxs(
      "a",
      {
        href,
        className: "group flex items-baseline gap-2 border-b border-hair/50 py-2 text-[13px] text-silver transition-colors hover:text-gold-light",
        children: [
          /* @__PURE__ */ jsx("span", { className: "h-px w-0 bg-gold transition-all duration-300 group-hover:w-3" }),
          label
        ]
      }
    ) }, label)) })
  ] });
}
export {
  Backdrop,
  Colophon,
  Masthead,
  NAV,
  Ticker
};
