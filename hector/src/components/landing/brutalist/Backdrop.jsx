"use client";

import { useEffect, useState } from "react";

/**
 * Fixed page furniture: the ruled ground everything sits on.
 * Purely decorative — no text, no claims.
 */
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

function Clock() {
  const [t, setT] = useState(null);
  useEffect(() => {
    setT(new Date());
    const id = window.setInterval(() => setT(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);
  if (!t) return null;
  let s = "";
  try {
    s = t.toLocaleTimeString("en-GB", { hour12: false, timeZone: "Asia/Kolkata" });
  } catch {
    s = t.toTimeString().slice(0, 8);
  }
  return (
    <span className="hidden items-center gap-2 font-mono text-[10.5px] text-muted 2xl:flex">
      <span className="h-1 w-1 bg-gold/70" />
      {s} IST
    </span>
  );
}

/**
 * The marquee strip of real citation correspondences.
 * Only pairs the comparison endpoint actually serves are listed, and they are
 * printed as requests rather than as settled facts about the law.
 */
export function Ticker({ pairs }) {
  const row = pairs.map((p) => `${p.act} §${p.section}  ⇄  counterpart resolved at request time`);
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

export { Clock };
