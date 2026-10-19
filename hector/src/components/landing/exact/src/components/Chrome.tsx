import { useEffect, useState } from "react";
import { Scale, ArrowRight, ArrowDown, ScanLine } from "lucide-react";
import { cn } from "../utils/cn";
import { useActiveSection, useScrollProgress } from "../lib/hooks";
import { MAPPINGS, byId } from "../data/corpus";
import { citationOf } from "../lib/text";
import { ALL_ACTS, TOTAL_ACTS } from "../data/acts";
import { Btn } from "./ui";

export const NAV = [
  { id: "corpus", label: "Corpus" },
  { id: "grammar", label: "Grammar" },
  { id: "chunking", label: "Chunking" },
  { id: "tester", label: "Tester" },
  { id: "compare", label: "Compare" },
  { id: "batch", label: "Batch" },
  { id: "ledger", label: "Ledger" },
  { id: "access", label: "Access" },
];

/* ------------------------------------------------------------------ */
/* backdrop                                                            */
/* ------------------------------------------------------------------ */

export function Backdrop() {
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

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 bg-cream" />
      <div className="absolute inset-0 rule-grid" />
      <div className="absolute inset-0 ledger-lines opacity-70" />
      <div
        className="absolute inset-x-0 top-0 h-[70vh]"
        style={{
          background:
            "radial-gradient(78% 58% at 50% -14%, rgba(201,169,98,0.085), rgba(17,19,21,0) 68%)",
          transform: `translate3d(0, ${y * -0.06}px, 0)`,
        }}
      />
      <div
        className="absolute inset-x-0 bottom-0 h-[55vh]"
        style={{ background: "linear-gradient(to top, rgba(58,70,89,0.16), rgba(17,19,21,0))" }}
      />
      <div className="absolute inset-y-0 left-[max(0px,calc(50%-700px))] w-px bg-silver/[0.09]" />
      <div className="absolute inset-y-0 right-[max(0px,calc(50%-700px))] w-px bg-silver/[0.09]" />
      <div className="grain-layer absolute inset-0 opacity-[0.055] mix-blend-soft-light" />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* masthead                                                            */
/* ------------------------------------------------------------------ */

function Clock() {
  const [t, setT] = useState(() => new Date());
  useEffect(() => {
    const id = window.setInterval(() => setT(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);
  let s = "";
  try {
    s = t.toLocaleTimeString("en-GB", { hour12: false, timeZone: "Asia/Kolkata" });
  } catch {
    s = t.toTimeString().slice(0, 8);
  }
  return (
    <span className="hidden items-center gap-2 font-mono text-[10.5px] text-muted 2xl:flex">
      <span className="h-1 w-1 bg-gold/70" />
      <span suppressHydrationWarning>{s} IST</span>
    </span>
  );
}

export function Masthead() {
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

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 border-b bg-cream/96 transition-all duration-500",
        compact ? "border-hair" : "border-transparent",
      )}
    >
      <div className="mx-auto flex max-w-[1400px] items-center gap-6 px-5 sm:px-8">
        <a href="#top" className="group flex shrink-0 items-center gap-3 py-3.5">
          <span className="grid h-8 w-8 place-items-center border border-gold/50 text-gold transition-colors duration-300 group-hover:bg-gold group-hover:text-ink">
            <Scale className="h-[15px] w-[15px]" strokeWidth={1.4} />
          </span>
          <span className="flex items-baseline gap-2">
            <span className="font-display text-[19px] font-semibold uppercase leading-none tracking-[0.3em] text-paper">
              Hector
            </span>
            <span className="hidden label-xs text-muted sm:inline">grammar 4.2</span>
          </span>
        </a>

        <nav className="ml-auto hidden items-center gap-0.5 xl:flex">
          {NAV.map((n) => (
            <a
              key={n.id}
              href={`#${n.id}`}
              className={cn(
                "group relative flex items-baseline gap-1.5 px-3 py-2 label-xs transition-colors duration-200",
                active === n.id ? "text-gold" : "text-silver hover:text-paper",
              )}
            >
              <span className={cn("mr-0.5 h-1 w-1 translate-y-[-1px]", active === n.id ? "bg-gold" : "bg-slate-custom group-hover:bg-silver")} />
              {n.label}
              <span
                className={cn(
                  "absolute inset-x-2 -bottom-px h-px origin-left bg-gold transition-transform duration-300",
                  active === n.id ? "scale-x-100" : "scale-x-0 group-hover:scale-x-100",
                )}
              />
            </a>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-4 lg:ml-0">
          <Clock />
          <span className="hidden items-center gap-2 label-xs text-muted xl:flex">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping bg-success/60" />
              <span className="relative inline-flex h-1.5 w-1.5 bg-success" />
            </span>
            {TOTAL_ACTS} acts indexed
          </span>
          <a href="#access" className="hidden sm:block">
            <Btn className="px-3.5 py-2">
              Request access
              <ArrowRight className="h-3 w-3 transition-transform duration-200 group-hover:translate-x-0.5" />
            </Btn>
          </a>
          <button
            onClick={() => setOpen((o) => !o)}
            aria-label="Toggle navigation"
            className="grid h-8 w-8 place-items-center border border-hair text-silver xl:hidden"
          >
            <ScanLine className="h-4 w-4" strokeWidth={1.5} />
          </button>
        </div>
      </div>

      <div className="relative h-px w-full bg-hair/60">
        <div
          className="h-full bg-gold/80"
          style={{ width: `${Math.max(0.5, p * 100)}%`, transition: "width .12s linear" }}
        />
      </div>

      {open && (
        <div className="border-t border-hair bg-panel px-5 pb-4 xl:hidden">
          <div className="grid grid-cols-2 gap-x-6">
            {NAV.map((n, i) => (
              <a
                key={n.id}
                href={`#${n.id}`}
                onClick={() => setOpen(false)}
                className="flex items-baseline gap-2 border-b border-hair/70 py-2.5 font-mono text-[12px] text-silver"
              >
                <span className="text-[9px] text-muted">{String(i + 1).padStart(2, "0")}</span>
                {n.label}
              </a>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}

/* ------------------------------------------------------------------ */
/* ticker                                                              */
/* ------------------------------------------------------------------ */

export function Ticker() {
  const items = MAPPINGS.map((m) => {
    const a = byId(m.from)!;
    const b = byId(m.to)!;
    return `${citationOf(a)}  ⇄  ${citationOf(b)}  ·  ${m.relation}`;
  });
  const tail = ALL_ACTS.filter((a) => a.repeals)
    .slice(0, 6)
    .map((a) => `${a.code} repeals ${a.repeals?.split(",")[0]}`.trim());
  const row = [...items, ...tail];

  return (
    <div className="group relative overflow-hidden border-y border-hair bg-panel-2/70">
      <div className="flex w-max animate-marquee items-center whitespace-nowrap group-hover:[animation-play-state:paused]">
        {[0, 1].map((dup) => (
          <div key={dup} className="flex items-center" aria-hidden={dup === 1}>
            {row.map((t, i) => (
              <span key={`${dup}-${i}`} className="flex items-center font-mono text-[11px] text-muted">
                <span className="px-5 py-2.5 transition-colors duration-200 hover:text-gold">{t}</span>
                <span className="h-3 w-px bg-hair" />
              </span>
            ))}
          </div>
        ))}
      </div>
      <div className="pointer-events-none absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-cream to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-cream to-transparent" />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* colophon / footer                                                   */
/* ------------------------------------------------------------------ */

export function Colophon() {
  return (
    <footer className="relative border-t border-hair bg-ink">
      <div className="mx-auto max-w-[1400px] px-5 py-16 sm:px-8">
        <div className="grid gap-12 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <p className="label-xs text-gold">Ad finem</p>
            <p className="mt-5 font-display text-[clamp(1.9rem,3.6vw,3rem)] leading-[1.02] tracking-[-0.02em] text-paper">
              The statute says what it says.
              <span className="block text-silver/70 italic">Hector only refuses to cut it up.</span>
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a href="#corpus">
                <Btn>
                  Open the corpus
                  <ArrowDown className="h-3 w-3" />
                </Btn>
              </a>
              <a href="#access">
                <Btn variant="ghost">Request an index key</Btn>
              </a>
            </div>
          </div>

          <div className="grid gap-8 sm:grid-cols-3 lg:col-span-7">
            <FooterCol
              title="Product"
              links={[
                ["Regex boundary grammar", "#grammar"],
                ["Section comparison", "#compare"],
                ["Batch runs", "#batch"],
                ["38 bare acts", "#corpus"],
              ]}
            />
            <FooterCol
              title="Practice areas"
              links={[
                ["Criminal · BNS / BNSS / BSA", "#corpus"],
                ["Civil · CPC / ICA / SRA", "#corpus"],
                ["Family · HMA / PWDVA", "#corpus"],
                ["Regulatory · NDPS / CPA / EPA", "#corpus"],
              ]}
            />
            <FooterCol
              title="Corpus"
              links={[
                ["Repeal schedule", "#corpus"],
                ["Citation ledger", "#ledger"],
                ["Short-code collisions", "#corpus"],
                ["Index figures", "#ledger"],
              ]}
            />
          </div>
        </div>

        <div className="mt-14 grid gap-6 border-t border-hair pt-8 lg:grid-cols-12">
          <p className="text-[12px] leading-relaxed text-muted lg:col-span-7">
            Hector is a retrieval instrument for bare acts. Section text on this page is abridged for
            display; every provision returned by the product is printed with its act, section, clause and
            the character offset of the source line, and must be read against the authoritative text
            published by the Legislative Department before it is relied on in any proceeding. Nothing here
            is legal advice.
          </p>
          <div className="flex flex-col justify-between gap-4 lg:col-span-5 lg:items-end">
            <div className="flex items-center gap-3 font-mono text-[11px] text-muted">
              <span>Hector</span>
              <span className="h-3 w-px bg-hair" />
              <span>Hierarchical Evaluation of Civil-Criminal Textual’s Orchestrator &amp; Retrieval</span>
            </div>
            <div className="flex flex-wrap items-center gap-4 label-xs text-muted">
              <span>© <span suppressHydrationWarning>{new Date().getFullYear()}</span> Hector Legal Systems</span>
              <span className="hidden h-3 w-px bg-hair sm:block" />
              <a href="#top" className="text-silver transition-colors hover:text-gold">
                Back to the top
              </a>
              <span className="hidden h-3 w-px bg-hair sm:block" />
              <span>Terms</span>
              <span>Privacy</span>
            </div>
          </div>
        </div>
      </div>
      <div className="overflow-hidden border-t border-hair py-3">
        <p className="whitespace-nowrap text-center font-display text-[13vw] leading-[0.8] tracking-[-0.04em] text-silver/[0.055] select-none">
          HECTOR · 38 BARE ACTS · ONE GRAMMAR
        </p>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: [string, string][] }) {
  return (
    <div>
      <p className="label-xs text-gold">{title}</p>
      <ul className="mt-4 space-y-0">
        {links.map(([label, href]) => (
          <li key={label}>
            <a
              href={href}
              className="group flex items-baseline gap-2 border-b border-hair/50 py-2 text-[13px] text-silver transition-colors hover:text-gold-light"
            >
              <span className="h-px w-0 bg-gold transition-all duration-300 group-hover:w-3" />
              {label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
