import { useMemo, useState } from "react";
import { Check, Copy } from "lucide-react";
import { cn } from "../utils/cn";
import { Reveal } from "./ui";
import { CORPUS, MAPPINGS, byId, type Section } from "../data/corpus";
import { citationOf, diffWords, type DiffOp } from "../lib/text";
import { useCopy } from "../lib/hooks";

const bodyOf = (s: Section) =>
  s.parts
    .map((p) => (p.kind === "section" ? p.text : `${p.label ? `${p.label} ` : ""}${p.text}`))
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();

const sig = (s: Section) => (/^article/i.test(s.section) ? s.section : `s. ${s.section}`);

function Marked({ ops, side, only }: { ops: DiffOp[]; side: "l" | "r"; only: boolean }) {
  const keep = ops.filter((o) => (side === "l" ? o.t !== "add" : o.t !== "del"));
  const show = only ? keep.filter((o) => o.t !== "same") : keep;
  if (!show.length) return <span className="text-muted italic">— no change on this side —</span>;
  return (
    <>
      {show.map((o, i) => (
        <span
          key={i}
          className={cn(
            o.t === "same"
              ? "text-silver/85"
              : side === "l"
                ? "bg-error/[0.10] text-error/85 line-through decoration-error/40"
                : "bg-gold/[0.16] text-gold-light",
          )}
        >
          {o.text}
          {only && i < show.length - 1 ? " " : ""}
        </span>
      ))}
    </>
  );
}

function Side({
  s,
  ops,
  side,
  only,
  tag,
}: {
  s: Section;
  ops: DiffOp[];
  side: "l" | "r";
  only: boolean;
  tag: string;
}) {
  const { copied, copy } = useCopy();
  return (
    <div>
      <p className="label-xs text-muted">{tag}</p>
      <h3 className="mt-3 font-display text-[clamp(1.5rem,3vw,2.1rem)] leading-none tracking-[-0.02em] text-paper">
        {/^article/i.test(s.section) ? s.section : `Section ${s.section}`}
      </h3>
      <p className="mt-2 text-[13.5px] leading-snug text-silver/85">{s.note}</p>
      <p className="mt-3 flex flex-wrap items-center gap-2 font-mono text-[10.5px] text-muted">
        <span className="text-gold/85">{s.act}</span>
        <span className="h-2 w-px bg-hair" />
        <span className={s.status === "Active" ? "text-success/80" : "text-error/70"}>{s.status}</span>
      </p>

      <div className="mt-6 border-t border-hair pt-5">
        <p className="font-mono text-[12.5px] leading-[1.95] sm:text-[13px]">
          <span className="text-gold">
            {sig(s)}. {s.note}.—
          </span>
          <Marked ops={ops} side={side} only={only} />
        </p>
      </div>

      <button
        onClick={() => copy(citationOf(s), s.id)}
        className="mt-6 flex items-center gap-1.5 font-mono text-[10.5px] text-muted transition-colors hover:text-gold"
      >
        {copied === s.id ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" strokeWidth={1.7} />}
        {citationOf(s)}
      </button>
    </div>
  );
}

export function ComparisonSection() {
  const [idx, setIdx] = useState(0);
  const [only, setOnly] = useState(false);
  const [custom, setCustom] = useState<{ l: string; r: string } | null>(null);
  const { copied, copy } = useCopy();

  const m = MAPPINGS[idx];
  const left = custom ? byId(custom.l)! : byId(m.from)!;
  const right = custom ? byId(custom.r)! : byId(m.to)!;
  const ops = useMemo(() => diffWords(bodyOf(left), bodyOf(right)), [left, right]);
  const changed = ops.filter((o) => o.t !== "same").length;

  return (
    <section id="compare" className="relative border-t border-hair">
      <div className="mx-auto w-full max-w-[1080px] px-5 py-16 sm:px-8 md:py-24">
        <Reveal y={false}>
          <div className="flex flex-col gap-5 border-b border-hair pb-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="label-xs text-gold">04 · Section comparison</p>
              <h2 className="mt-4 max-w-[24ch] font-display text-[clamp(1.9rem,4.4vw,3.1rem)] leading-[0.94] tracking-[-0.025em] text-paper">
                The old text. The new text.
                <span className="block italic text-gold-light">Nothing in between.</span>
              </h2>
            </div>
            <p className="max-w-[40ch] text-[13.5px] leading-[1.7] text-silver">
              One pair at a time, printed whole, with the changed words marked and the relation named.
            </p>
          </div>
        </Reveal>

        {/* pair selector */}
        <div className="mt-8 border-b border-hair">
          {custom ? (
            <div className="flex flex-wrap items-end gap-3 pb-4">
              {(
                [
                  ["l", "prior text"],
                  ["r", "operative text"],
                ] as const
              ).map(([k, label]) => (
                <label key={k} className="min-w-[240px] flex-1">
                  <span className="label-xs text-muted">{label}</span>
                  <select
                    value={custom[k]}
                    onChange={(e) =>
                      setCustom((c) => ({ ...c!, [k]: e.target.value }) as { l: string; r: string })
                    }
                    className="mt-2 w-full border-b border-hair bg-transparent pb-2 font-mono text-[12px] text-paper outline-none transition-colors focus:border-gold"
                  >
                    {CORPUS.filter((s) => s.id !== custom[k === "l" ? "r" : "l"]).map((s) => (
                      <option key={s.id} value={s.id} className="bg-panel text-paper">
                        {s.code} {sig(s)} — {s.note}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
              <button
                onClick={() => setCustom(null)}
                className="pb-2 font-mono text-[11px] text-muted underline-offset-4 transition-colors hover:text-gold hover:underline"
              >
                back to the mapped pairs
              </button>
            </div>
          ) : (
            <div className="-mx-1 flex gap-7 overflow-x-auto px-1">
              {MAPPINGS.map((mp, i) => {
                const a = byId(mp.from)!;
                const b = byId(mp.to)!;
                const on = i === idx;
                return (
                  <button
                    key={`${mp.from}-${mp.to}`}
                    onClick={() => setIdx(i)}
                    className={cn(
                      "group relative shrink-0 pb-4 text-left transition-opacity duration-200",
                      on ? "opacity-100" : "opacity-55 hover:opacity-90",
                    )}
                  >
                    <span className="flex items-center gap-2 font-mono text-[11.5px] whitespace-nowrap">
                      <span className={on ? "text-gold" : "text-silver"}>
                        {a.code} {sig(a)}
                      </span>
                      <span className="text-slate-custom">⇄</span>
                      <span className={on ? "text-gold-light" : "text-paper/80"}>
                        {b.code} {sig(b)}
                      </span>
                    </span>
                    <span className="mt-1.5 block font-mono text-[10px] text-muted">{mp.relation}</span>
                    <span
                      className={cn(
                        "absolute inset-x-0 bottom-0 h-px origin-left bg-gold transition-transform duration-300",
                        on ? "scale-x-100" : "scale-x-0 group-hover:scale-x-50",
                      )}
                    />
                  </button>
                );
              })}
              <button
                onClick={() => setCustom({ l: left.id, r: right.id })}
                className="shrink-0 pb-4 font-mono text-[11px] text-muted transition-colors hover:text-gold"
              >
                + any two provisions
              </button>
            </div>
          )}
        </div>

        {/* the reader */}
        <div className="grid gap-10 pt-10 md:grid-cols-2 md:gap-0">
          <div className="md:border-r md:pr-10">
            <Side s={left} ops={ops} side="l" only={only} tag={custom ? "selected · a" : "prior text"} />
          </div>
          <div className="md:pl-10">
            <Side s={right} ops={ops} side="r" only={only} tag={custom ? "selected · b" : "operative text"} />
          </div>
        </div>

        {/* relation */}
        <div className="mt-12 flex flex-col gap-5 border-t border-hair pt-6 md:flex-row md:items-start md:gap-10">
          <div className="flex shrink-0 items-center gap-3">
            <span className="border border-gold/45 px-2 py-1 font-mono text-[10.5px] tracking-wide text-gold-light">
              {custom ? "unmapped" : m.relation}
            </span>
            {!custom && (
              <span className="flex items-center gap-1.5 font-mono text-[10.5px] text-muted">
                {[0, 1, 2].map((n) => (
                  <span
                    key={n}
                    className={cn(
                      "h-2.5 w-[3px]",
                      n < (m.risk === "low" ? 1 : m.risk === "medium" ? 2 : 3)
                        ? m.risk === "low"
                          ? "bg-success"
                          : m.risk === "medium"
                            ? "bg-warning"
                            : "bg-error"
                        : "bg-slate-custom",
                    )}
                  />
                ))}
                {m.risk}
              </span>
            )}
          </div>
          <p className="flex-1 text-[13.5px] leading-[1.75] text-silver">
            {custom
              ? "Manual pairing. The index asserts no relation here — it returns both texts and lets you read them against each other."
              : m.delta}
          </p>
          <button
            onClick={() => setOnly((v) => !v)}
            className={cn(
              "shrink-0 self-start font-mono text-[11px] underline-offset-4 transition-colors hover:underline",
              only ? "text-gold" : "text-muted",
            )}
          >
            {only ? `changes only · ${changed} runs` : "changes only"}
          </button>
          <button
            onClick={() => copy(`${citationOf(left)}  ⇄  ${citationOf(right)}`, "pair")}
            className="flex shrink-0 items-center gap-1.5 self-start font-mono text-[11px] text-muted transition-colors hover:text-gold"
          >
            {copied === "pair" ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" strokeWidth={1.7} />}
            copy both citations
          </button>
        </div>
      </div>
    </section>
  );
}
