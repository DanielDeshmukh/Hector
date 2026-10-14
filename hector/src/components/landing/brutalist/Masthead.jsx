"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Scale, ArrowRight, Menu, X } from "lucide-react";
import { cn } from "@/lib/landing/cn";
import { useActiveSection, useScrollProgress } from "@/lib/landing/hooks";
import { Btn, LiveCount } from "./ui";
import { Clock } from "./Backdrop";

export const NAV = [
  { id: "corpus", label: "Corpus" },
  { id: "grammar", label: "Grammar" },
  { id: "chunking", label: "Chunking" },
  { id: "tester", label: "Tester" },
  { id: "compare", label: "Compare" },
  { id: "batch", label: "Batch" },
  { id: "ledger", label: "Ledger" },
  { id: "faq", label: "FAQ" },
];

/**
 * Fixed top bar. The only figure it shows is the live record count, read
 * from the index when the page mounts. If the read fails the figure is
 * simply absent.
 */
export function Masthead({ records, recordsLoading, recordsFailed }) {
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
            <span className="hidden label-xs text-muted sm:inline">bare-act retrieval</span>
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
              <span
                className={cn(
                  "mr-0.5 h-1 w-1 translate-y-[-1px]",
                  active === n.id ? "bg-gold" : "bg-slate-custom group-hover:bg-silver",
                )}
              />
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
          <LiveCount records={records} loading={recordsLoading} failed={recordsFailed} className="hidden xl:inline-flex" />
          <Link href="/search" className="hidden sm:block">
            <Btn className="px-3.5 py-2">
              Open the app
              <ArrowRight className="h-3 w-3 transition-transform duration-200 group-hover:translate-x-0.5" />
            </Btn>
          </Link>
          <button
            onClick={() => setOpen((o) => !o)}
            aria-label="Toggle navigation"
            aria-expanded={open}
            className="grid h-8 w-8 place-items-center border border-hair text-silver xl:hidden"
          >
            {open ? <X className="h-4 w-4" strokeWidth={1.5} /> : <Menu className="h-4 w-4" strokeWidth={1.5} />}
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
          <div className="mt-4 flex items-center justify-between">
            <LiveCount records={records} loading={recordsLoading} failed={recordsFailed} />
            <Link href="/search" onClick={() => setOpen(false)}>
              <Btn className="px-3.5 py-2">Open the app</Btn>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
