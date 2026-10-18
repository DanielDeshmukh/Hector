import { cn } from "@/lib/landing/cn";
import { useReveal, useCopy } from "@/lib/landing/hooks";

/* ------------------------------------------------------------------ *
 * layout                                                              *
 * ------------------------------------------------------------------ */

/** Full-width section head: title left, controls right. */
export function WideHead({ no, kicker, title, lede, controls }) {
  return (
    <Reveal y={false}>
      <div className="grid items-end gap-8 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <Kicker no={no}>{kicker}</Kicker>
          <h2 className="mt-5 font-display text-[clamp(2.1rem,5vw,4rem)] leading-[0.92] tracking-[-0.025em] text-paper">
            {title}
          </h2>
        </div>
        <div className="lg:col-span-5">
          {lede && (
            <p className="max-w-[52ch] text-[14.5px] leading-[1.72] text-silver lg:ml-auto">{lede}</p>
          )}
          {controls && <div className="mt-6 lg:text-right">{controls}</div>}
        </div>
      </div>
    </Reveal>
  );
}

/** Section with the head in a narrow left column and the body in a wide right column. */
export function SectionShell({ id, no, kicker, title, lede, aside, children, className }) {
  return (
    <section id={id} className={cn("relative border-t border-hair/90", className)}>
      <div className="mx-auto w-full max-w-[1400px] px-5 py-16 sm:px-8 md:py-24">
        <div className="grid gap-8 md:grid-cols-12 md:gap-10">
          <div className="md:col-span-5 lg:col-span-4">
            <Reveal y={false}>
              <Kicker no={no}>{kicker}</Kicker>
              <h2 className="mt-5 font-display text-[clamp(2rem,4.4vw,3.5rem)] leading-[0.95] tracking-[-0.02em] text-paper">
                {title}
              </h2>
              {lede && (
                <p className="mt-5 max-w-md text-[15px] leading-[1.75] text-silver [&_em]:font-display [&_em]:italic [&_em]:text-gold-light">
                  {lede}
                </p>
              )}
              {aside && <div className="mt-7">{aside}</div>}
            </Reveal>
          </div>
          <div className="md:col-span-7 lg:col-span-8">
            <Reveal delay={90}>{children}</Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}

export function WideSection({ id, children, className, tint = false }) {
  return (
    <section id={id} className={cn("relative border-t border-hair", tint && "bg-ink/40", className)}>
      <div className="mx-auto w-full max-w-[1400px] px-5 py-16 sm:px-8 md:py-24">{children}</div>
    </section>
  );
}

/* ------------------------------------------------------------------ *
 * motion                                                              *
 * ------------------------------------------------------------------ */

export function Reveal({ children, delay = 0, className, y = true }) {
  const { ref, shown } = useReveal();
  return (
    <div
      ref={ref}
      className={cn("will-change-[opacity,transform]", className)}
      style={{
        opacity: shown ? 1 : 0,
        transform: shown ? "none" : y ? "translate3d(0,26px,0)" : "none",
        transition: shown
          ? `opacity .8s cubic-bezier(.16,.84,.28,1) ${delay}ms, transform .8s cubic-bezier(.16,.84,.28,1) ${delay}ms`
          : "none",
      }}
    >
      {children}
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * marks                                                               *
 * ------------------------------------------------------------------ */

export function Kicker({ no, children }) {
  return (
    <div className="flex items-center gap-3 label-xs text-gold">
      <span className="text-silver/70">{no}</span>
      <span className="h-px w-8 bg-gold/45" />
      <span>{children}</span>
    </div>
  );
}

export function Tag({ children, tone = "neutral", className }) {
  const tones = {
    neutral: "border-slate-custom/70 text-silver",
    gold: "border-gold/55 text-gold",
    active: "border-success/40 text-success/90",
    repealed: "border-error/40 text-error/85",
    muted: "border-hair text-muted",
  };
  return (
    <span className={cn("inline-flex items-center gap-1.5 border px-1.5 py-[3px] label-xs", tones[tone], className)}>
      {children}
    </span>
  );
}

export function Corner({ className }) {
  return <span aria-hidden className={cn("pointer-events-none absolute h-2.5 w-2.5 border-gold/60", className)} />;
}

export function Panel({ children, className, corners = true }) {
  return (
    <div className={cn("relative border border-hair bg-panel", className)}>
      {corners && (
        <>
          <Corner className="-left-px -top-px border-l border-t" />
          <Corner className="-right-px -top-px border-r border-t" />
          <Corner className="-bottom-px -left-px border-b border-l" />
          <Corner className="-bottom-px -right-px border-b border-r" />
        </>
      )}
      {children}
    </div>
  );
}

export function StatRow({ k, v, mono = true }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-hair/70 py-2">
      <span className="label-xs text-muted">{k}</span>
      <span className={cn("text-[12px] text-paper/90", mono && "font-mono")}>{v}</span>
    </div>
  );
}

export function Btn({ children, onClick, href, variant = "solid", className, type = "button", disabled, title }) {
  const variants = {
    solid: "border-gold/70 bg-gold text-ink hover:bg-gold-light hover:border-gold-light active:translate-y-px",
    ghost: "border-slate-custom text-paper hover:border-gold hover:text-gold-light",
    quiet: "border-transparent text-silver hover:text-gold-light hover:border-hair",
  };
  const cls = cn(
    "group inline-flex items-center justify-center gap-2 whitespace-nowrap border px-4 py-2.5 label-xs transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40",
    variants[variant],
    className,
  );
  if (href) {
    return (
      <a href={href} title={title} className={cls}>
        {children}
      </a>
    );
  }
  return (
    <button type={type} title={title} onClick={onClick} disabled={disabled} className={cls}>
      {children}
    </button>
  );
}

/* ------------------------------------------------------------------ *
 * source display                                                      *
 * ------------------------------------------------------------------ */

/** A block of Python as printed on this page: file, line, verbatim source. */
export function CodeBlock({ file, line, python, children, tone = "neutral", compact = false }) {
  const { copied, copy } = useCopy();
  return (
    <div className={cn("relative border bg-ink/70", tone === "gold" ? "border-gold/30" : "border-hair")}>
      <div className="flex items-center gap-3 border-b border-hair/80 bg-panel/60 px-3 py-1.5">
        <span className="label-xs text-gold">{file}</span>
        <span className="font-mono text-[10px] text-muted">L{line}</span>
        <span className="ml-auto flex items-center gap-2">
          {python && (
            <button
              onClick={() => copy(python)}
              className="label-xs text-muted transition-colors hover:text-gold"
              title="Copy the Python source"
            >
              {copied ? "copied" : "copy"}
            </button>
          )}
        </span>
      </div>
      <pre
        className={cn(
          "overflow-x-auto font-mono text-[11.5px] leading-[1.75] text-silver",
          compact ? "px-3 py-2" : "px-4 py-3",
        )}
      >
        <code>{python ?? children}</code>
      </pre>
    </div>
  );
}

/** The live reading from the index, or nothing at all. */
export function LiveCount({ records, loading, failed, className }) {
  if (loading) {
    return (
      <span className={cn("whitespace-nowrap font-mono text-[11px] text-muted", className)}>
        <span className="animate-pulse">reading index…</span>
      </span>
    );
  }
  if (failed || records === null) return null;
  return (
    <span className={cn("inline-flex shrink-0 items-baseline gap-1.5 whitespace-nowrap font-mono text-[11px] text-gold", className)}>
      <span className="relative flex h-1.5 w-1.5 translate-y-[-2px]">
        <span className="absolute inline-flex h-full w-full animate-ping bg-success/60" />
        <span className="relative inline-flex h-1.5 w-1.5 bg-success" />
      </span>
      <span className="tabular-nums">{records.toLocaleString("en-IN")}</span>
      <span className="text-muted">records live</span>
    </span>
  );
}

/** Small status chip used wherever a live request is in flight. */
export function Busy({ on, label = "querying index" }) {
  if (!on) return null;
  return (
    <span className="inline-flex items-center gap-2 font-mono text-[10.5px] text-gold">
      <span className="h-1 w-1 animate-pulse bg-gold" />
      {label}
    </span>
  );
}

/** Renders nothing when a live call failed, so the page never invents a figure. */
export function OrFallback({ ok, children, failedNote = "index unreachable — nothing shown" }) {
  if (ok) return children;
  return <p className="font-mono text-[11px] text-muted">{failedNote}</p>;
}
