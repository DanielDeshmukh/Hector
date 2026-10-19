import type { ReactNode } from "react";
import { cn } from "../utils/cn";
import { useReveal } from "../lib/hooks";

/** Full-width section head: title on the left, controls on the right. */
export function WideHead({
  no,
  kicker,
  title,
  lede,
  controls,
}: {
  no: string;
  kicker: string;
  title: ReactNode;
  lede?: ReactNode;
  controls?: ReactNode;
}) {
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

export function WideSection({
  id,
  children,
  className,
  tint = false,
}: {
  id: string;
  children: ReactNode;
  className?: string;
  tint?: boolean;
}) {
  return (
    <section
      id={id}
      className={cn("relative border-t border-hair", tint && "bg-ink/40", className)}
    >
      <div className="mx-auto w-full max-w-[1400px] px-5 py-16 sm:px-8 md:py-24">{children}</div>
    </section>
  );
}

export function Reveal({
  children,
  delay = 0,
  className,
  y = true,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  y?: boolean;
}) {
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

export function Kicker({ no, children }: { no: string; children: ReactNode }) {
  return (
    <div className="flex items-center gap-3 label-xs text-gold">
      <span className="text-silver/70">{no}</span>
      <span className="h-px w-8 bg-gold/45" />
      <span>{children}</span>
    </div>
  );
}

export function SectionShell({
  id,
  no,
  kicker,
  title,
  lede,
  aside,
  children,
  className,
}: {
  id: string;
  no: string;
  kicker: string;
  title: ReactNode;
  lede?: ReactNode;
  aside?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
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

export function Tag({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: "neutral" | "gold" | "active" | "repealed" | "muted";
  className?: string;
}) {
  const tones: Record<string, string> = {
    neutral: "border-slate-custom/70 text-silver",
    gold: "border-gold/55 text-gold",
    active: "border-success/40 text-success/90",
    repealed: "border-error/40 text-error/85",
    muted: "border-hair text-muted",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 border px-1.5 py-[3px] label-xs",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Btn({
  children,
  onClick,
  variant = "solid",
  className,
  type = "button",
  disabled,
  title,
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "solid" | "ghost" | "quiet";
  className?: string;
  type?: "button" | "submit";
  disabled?: boolean;
  title?: string;
}) {
  const variants: Record<string, string> = {
    solid:
      "border-gold/70 bg-gold text-ink hover:bg-gold-light hover:border-gold-light active:translate-y-px",
    ghost: "border-slate-custom text-paper hover:border-gold hover:text-gold-light",
    quiet: "border-transparent text-silver hover:text-gold-light hover:border-hair",
  };
  return (
    <button
      type={type}
      title={title}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "group inline-flex items-center justify-center gap-2 border px-4 py-2.5 label-xs transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40",
        variants[variant],
        className,
      )}
    >
      {children}
    </button>
  );
}

/** Monospace statutory line, printed like a legal report. */
export function StatRow({ k, v, mono = true }: { k: string; v: ReactNode; mono?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-hair/70 py-2">
      <span className="label-xs text-muted">{k}</span>
      <span className={cn("text-[12px] text-paper/90", mono && "font-mono")}>{v}</span>
    </div>
  );
}

export function Corner({ className }: { className?: string }) {
  return (
    <span
      aria-hidden
      className={cn("pointer-events-none absolute h-2.5 w-2.5 border-gold/60", className)}
    />
  );
}

export function Panel({
  children,
  className,
  corners = true,
}: {
  children: ReactNode;
  className?: string;
  corners?: boolean;
}) {
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
