import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { cn } from "../utils/cn";
import { useReveal } from "../lib/hooks";
function WideHead({
  no,
  kicker,
  title,
  lede,
  controls
}) {
  return /* @__PURE__ */ jsx(Reveal, { y: false, children: /* @__PURE__ */ jsxs("div", { className: "grid items-end gap-8 lg:grid-cols-12", children: [
    /* @__PURE__ */ jsxs("div", { className: "lg:col-span-7", children: [
      /* @__PURE__ */ jsx(Kicker, { no, children: kicker }),
      /* @__PURE__ */ jsx("h2", { className: "mt-5 font-display text-[clamp(2.1rem,5vw,4rem)] leading-[0.92] tracking-[-0.025em] text-paper", children: title })
    ] }),
    /* @__PURE__ */ jsxs("div", { className: "lg:col-span-5", children: [
      lede && /* @__PURE__ */ jsx("p", { className: "max-w-[52ch] text-[14.5px] leading-[1.72] text-silver lg:ml-auto", children: lede }),
      controls && /* @__PURE__ */ jsx("div", { className: "mt-6 lg:text-right", children: controls })
    ] })
  ] }) });
}
function WideSection({
  id,
  children,
  className,
  tint = false
}) {
  return /* @__PURE__ */ jsx(
    "section",
    {
      id,
      className: cn("relative border-t border-hair", tint && "bg-ink/40", className),
      children: /* @__PURE__ */ jsx("div", { className: "mx-auto w-full max-w-[1400px] px-5 py-16 sm:px-8 md:py-24", children })
    }
  );
}
function Reveal({
  children,
  delay = 0,
  className,
  y = true
}) {
  const { ref, shown } = useReveal();
  return /* @__PURE__ */ jsx(
    "div",
    {
      ref,
      className: cn("will-change-[opacity,transform]", className),
      style: {
        opacity: shown ? 1 : 0,
        transform: shown ? "none" : y ? "translate3d(0,26px,0)" : "none",
        transition: shown ? `opacity .8s cubic-bezier(.16,.84,.28,1) ${delay}ms, transform .8s cubic-bezier(.16,.84,.28,1) ${delay}ms` : "none"
      },
      children
    }
  );
}
function Kicker({ no, children }) {
  return /* @__PURE__ */ jsxs("div", { className: "flex items-center gap-3 label-xs text-gold", children: [
    /* @__PURE__ */ jsx("span", { className: "text-silver/70", children: no }),
    /* @__PURE__ */ jsx("span", { className: "h-px w-8 bg-gold/45" }),
    /* @__PURE__ */ jsx("span", { children })
  ] });
}
function SectionShell({
  id,
  no,
  kicker,
  title,
  lede,
  aside,
  children,
  className
}) {
  return /* @__PURE__ */ jsx("section", { id, className: cn("relative border-t border-hair/90", className), children: /* @__PURE__ */ jsx("div", { className: "mx-auto w-full max-w-[1400px] px-5 py-16 sm:px-8 md:py-24", children: /* @__PURE__ */ jsxs("div", { className: "grid gap-8 md:grid-cols-12 md:gap-10", children: [
    /* @__PURE__ */ jsx("div", { className: "md:col-span-5 lg:col-span-4", children: /* @__PURE__ */ jsxs(Reveal, { y: false, children: [
      /* @__PURE__ */ jsx(Kicker, { no, children: kicker }),
      /* @__PURE__ */ jsx("h2", { className: "mt-5 font-display text-[clamp(2rem,4.4vw,3.5rem)] leading-[0.95] tracking-[-0.02em] text-paper", children: title }),
      lede && /* @__PURE__ */ jsx("p", { className: "mt-5 max-w-md text-[15px] leading-[1.75] text-silver [&_em]:font-display [&_em]:italic [&_em]:text-gold-light", children: lede }),
      aside && /* @__PURE__ */ jsx("div", { className: "mt-7", children: aside })
    ] }) }),
    /* @__PURE__ */ jsx("div", { className: "md:col-span-7 lg:col-span-8", children: /* @__PURE__ */ jsx(Reveal, { delay: 90, children }) })
  ] }) }) });
}
function Tag({
  children,
  tone = "neutral",
  className
}) {
  const tones = {
    neutral: "border-slate-custom/70 text-silver",
    gold: "border-gold/55 text-gold",
    active: "border-success/40 text-success/90",
    repealed: "border-error/40 text-error/85",
    muted: "border-hair text-muted"
  };
  return /* @__PURE__ */ jsx(
    "span",
    {
      className: cn(
        "inline-flex items-center gap-1.5 border px-1.5 py-[3px] label-xs",
        tones[tone],
        className
      ),
      children
    }
  );
}
function Btn({
  children,
  onClick,
  variant = "solid",
  className,
  type = "button",
  disabled,
  title
}) {
  const variants = {
    solid: "border-gold/70 bg-gold text-ink hover:bg-gold-light hover:border-gold-light active:translate-y-px",
    ghost: "border-slate-custom text-paper hover:border-gold hover:text-gold-light",
    quiet: "border-transparent text-silver hover:text-gold-light hover:border-hair"
  };
  return /* @__PURE__ */ jsx(
    "button",
    {
      type,
      title,
      onClick,
      disabled,
      className: cn(
        "group inline-flex items-center justify-center gap-2 border px-4 py-2.5 label-xs transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40",
        variants[variant],
        className
      ),
      children
    }
  );
}
function StatRow({ k, v, mono = true }) {
  return /* @__PURE__ */ jsxs("div", { className: "flex items-baseline justify-between gap-4 border-b border-hair/70 py-2", children: [
    /* @__PURE__ */ jsx("span", { className: "label-xs text-muted", children: k }),
    /* @__PURE__ */ jsx("span", { className: cn("text-[12px] text-paper/90", mono && "font-mono"), children: v })
  ] });
}
function Corner({ className }) {
  return /* @__PURE__ */ jsx(
    "span",
    {
      "aria-hidden": true,
      className: cn("pointer-events-none absolute h-2.5 w-2.5 border-gold/60", className)
    }
  );
}
function Panel({
  children,
  className,
  corners = true
}) {
  return /* @__PURE__ */ jsxs("div", { className: cn("relative border border-hair bg-panel", className), children: [
    corners && /* @__PURE__ */ jsxs(Fragment, { children: [
      /* @__PURE__ */ jsx(Corner, { className: "-left-px -top-px border-l border-t" }),
      /* @__PURE__ */ jsx(Corner, { className: "-right-px -top-px border-r border-t" }),
      /* @__PURE__ */ jsx(Corner, { className: "-bottom-px -left-px border-b border-l" }),
      /* @__PURE__ */ jsx(Corner, { className: "-bottom-px -right-px border-b border-r" })
    ] }),
    children
  ] });
}
export {
  Btn,
  Corner,
  Kicker,
  Panel,
  Reveal,
  SectionShell,
  StatRow,
  Tag,
  WideHead,
  WideSection
};
