"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, Copy, Columns2, Loader2 } from "lucide-react";
import { cn } from "@/lib/landing/cn";
import { compareHector } from "@/lib/landing/api";
import { COMPARE_SECTIONS } from "@/lib/landing/samples";
import { Reveal, Tag, Btn } from "./ui";
import { useCopy } from "@/lib/landing/hooks";

/* ---- a small LCS word diff, so the two texts can be read against each other ---- */
function tokenize(s) {
  return String(s || "")
    .split(/(\s+)/)
    .filter((t) => t.length > 0);
}

function diffWords(a, b) {
  const A = tokenize(a);
  const B = tokenize(b);
  const n = A.length;
  const m = B.length;
  if (n * m > 400000) return [{ t: "del", text: a }, { t: "add", text: b }];
  const dp = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
  for (let i = n - 1; i >= 0; i -= 1) {
    for (let j = m - 1; j >= 0; j -= 1) {
      dp[i][j] = A[i] === B[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }
  const ops = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (A[i] === B[j]) {
      ops.push({ t: "same", text: A[i] });
      i += 1;
      j += 1;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      ops.push({ t: "del", text: A[i] });
      i += 1;
    } else {
      ops.push({ t: "add", text: B[j] });
      j += 1;
    }
  }
  while (i < n) {
    ops.push({ t: "del", text: A[i] });
    i += 1;
  }
  while (j < m) {
    ops.push({ t: "add", text: B[j] });
    j += 1;
  }
  return ops;
}

const bodyOf = (src) => String(src?.matchedText || src?.fullText || "").replace(/\s+/g, " ").trim();

function Marked({ ops, side, only }) {
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
        </span>
      ))}
    </>
  );
}

function Side({ src, ops, side, only, tag, requested }) {
  const { copied, copy } = useCopy();
  if (!src) {
    return (
      <div>
        <p className="label-xs text-muted">{tag}</p>
        <p className="mt-4 font-display text-[clamp(1.4rem,3vw,2rem)] leading-tight text-silver/70">
          {requested ? "no text returned" : "no counterpart found"}
        </p>
        <p className="mt-3 max-w-[40ch] text-[13px] leading-[1.7] text-muted">
          {requested
            ? "The request completed but matched no provision on this side."
            : "The index did not assert a correspondence for this provision. It returns nothing rather than guessing."}
        </p>
      </div>
    );
  }
  return (
    <div>
      <p className="label-xs text-muted">{tag}</p>
      <h3 className="mt-3 font-display text-[clamp(1.5rem,3vw,2.1rem)] leading-none tracking-[-0.02em] text-paper">
        Section {src.section || "—"}
      </h3>
      <p className="mt-2 text-[13.5px] leading-snug text-silver/85">{src.act || "—"}</p>
      <p className="mt-3 font-mono text-[10.5px] text-muted">
        retrieval {Math.round((src.rawScore || 0) * 100) / 100} · rerank{" "}
        {Math.round((src.rerankerScore || 0) * 100) / 100}
      </p>

      <div className="mt-6 border-t border-hair pt-5">
        <p className="font-mono text-[12.5px] leading-[1.95] sm:text-[13px]">
          <span className="text-gold">
            {src.section}. {src.act}.—
          </span>{" "}
          {ops?.length ? <Marked ops={ops} side={side} only={only} /> : bodyOf(src)}
        </p>
      </div>

      <button
        onClick={() => copy(`${src.act} §${src.section}`, src.id)}
        className="mt-6 flex items-center gap-1.5 font-mono text-[10.5px] text-muted transition-colors hover:text-gold"
      >
        {copied === src.id ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" strokeWidth={1.7} />}
        {src.act} §{src.section}
      </button>
    </div>
  );
}

export function ComparisonSection() {
  const [idx, setIdx] = useState(0);
  const [only, setOnly] = useState(false);
  const [res, setRes] = useState(null);
  const [state, setState] = useState("idle"); // idle | running | done | failed
  const { copied, copy } = useCopy();

  const pair = COMPARE_SECTIONS[idx];

  useEffect(() => {
    const ctrl = new AbortController();
    setState("running");
    setRes(null);
    compareHector(pair.section, pair.act)
      .then((out) => {
        if (ctrl.signal.aborted) return;
        setRes(out);
        setState("done");
      })
      .catch((e) => {
        if (ctrl.signal.aborted) return;
        setRes({ error: e?.message || "unreachable" });
        setState("failed");
      });
    return () => ctrl.abort();
  }, [pair]);

  const left = res?.requestedResults?.[0] || null;
  const right = res?.counterpartResults?.[0] || null;

  const ops = useMemo(() => {
    if (!left || !right) return null;
    return diffWords(bodyOf(left), bodyOf(right));
  }, [left, right]);

  const changed = ops ? ops.filter((o) => o.t !== "same").length : 0;
  const label = left ? `${left.act} §${left.section}` : `${pair.act} §${pair.section}`;
  const counterLabel = right ? `${right.act} §${right.section}` : "counterpart";

  return (
    <section id="compare" className="relative border-t border-hair">
      <div className="mx-auto w-full max-w-[1080px] px-5 py-16 sm:px-8 md:py-24">
        <Reveal y={false}>
          <div className="flex flex-col gap-5 border-b border-hair pb-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="label-xs text-gold">04 · Section comparison</p>
              <h2 className="mt-4 max-w-[24ch] font-display text-[clamp(1.9rem,4.4vw,3.1rem)] leading-[0.94] tracking-[-0.025em] text-paper">
                The old text. The new text.
                <span className="block italic text-gold-light">Resolved by the index, not by me.</span>
              </h2>
            </div>
            <p className="max-w-[40ch] text-[13.5px] leading-[1.7] text-silver">
              One request per pair. The index is given a single side and asked for the other; what is printed
              below is its answer, including the case where it declines to assert a correspondence.
            </p>
          </div>
        </Reveal>

        {/* pair selector — these are the requests, not pre-settled mappings */}
        <div className="mt-8 border-b border-hair">
          <div className="-mx-1 flex gap-7 overflow-x-auto px-1">
            {COMPARE_SECTIONS.map((p, i) => {
              const on = i === idx;
              return (
                <button
                  key={`${p.act}-${p.section}`}
                  onClick={() => setIdx(i)}
                  className={cn(
                    "group relative shrink-0 pb-4 text-left transition-opacity duration-200",
                    on ? "opacity-100" : "opacity-55 hover:opacity-90",
                  )}
                >
                  <span className="flex items-center gap-2 whitespace-nowrap font-mono text-[11.5px]">
                    <span className={on ? "text-gold" : "text-silver"}>
                      {p.act} §{p.section}
                    </span>
                    <span className="text-slate-custom">&harr;</span>
                    <span className={on ? "text-gold-light" : "text-paper/80"}>
                      {right && on ? `${right.act} §${right.section}` : "resolved live"}
                    </span>
                  </span>
                  <span
                    className={cn(
                      "absolute inset-x-0 bottom-0 h-px origin-left bg-gold transition-transform duration-300",
                      on ? "scale-x-100" : "scale-x-0 group-hover:scale-x-50",
                    )}
                  />
                </button>
              );
            })}
          </div>
        </div>

        {/* status strip */}
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 border-b border-hair bg-cream/60 px-1 py-2 font-mono text-[11px] text-muted">
          <span>
            requested.<span className="text-silver/70">{pair.act} §{pair.section}</span>
          </span>
          <span>
            resolved.<span className="text-silver/70">{right ? `${right.act} §${right.section}` : state === "failed" ? "unreachable" : state === "running" ? "…" : "none"}</span>
          </span>
          <span>
            synthesis.<span className="text-silver/70">{res?.synthesis ?? "—"}</span>
          </span>
          <span className="ml-auto">
            {state === "running" && (
              <span className="inline-flex items-center gap-1.5 text-gold">
                <Loader2 className="h-3 w-3 animate-spin" strokeWidth={1.6} />
                querying
              </span>
            )}
          </span>
        </div>

        {/* the reader */}
        {state === "failed" ? (
          <div className="py-14 text-center">
            <p className="font-display text-[24px] text-silver">The comparison endpoint did not answer.</p>
            <p className="mx-auto mt-3 max-w-md text-[13px] leading-[1.7] text-muted">
              No text is shown because none was returned. Open the app to run the same comparison directly.
            </p>
            <a href="/" className="mt-5 inline-block">
              <Btn variant="ghost">Open the app</Btn>
            </a>
          </div>
        ) : (
          <div className="grid gap-10 pt-10 md:grid-cols-2 md:gap-0">
            <div className="md:border-r md:pr-10">
              <Side src={left} ops={ops} side="l" only={only} tag="requested side" requested />
            </div>
            <div className="md:pl-10">
              <Side src={right} ops={ops} side="r" only={only} tag="resolved counterpart" />
            </div>
          </div>
        )}

        {/* the relation, as the index states it */}
        <div className="mt-12 flex flex-col gap-5 border-t border-hair pt-6 md:flex-row md:items-start md:gap-10">
          <div className="flex shrink-0 items-center gap-3">
            <span className="border border-gold/45 px-2 py-1 font-mono text-[10.5px] tracking-wide text-gold-light">
              {right ? `${label} → ${counterLabel}` : "unmapped"}
            </span>
            {right && <Tag tone="active">counterpart resolved</Tag>}
            {!right && state === "done" && <Tag tone="repealed">no counterpart asserted</Tag>}
          </div>
          <p className="flex-1 text-[13.5px] leading-[1.75] text-silver">
            {res?.groundedMessage ||
              res?.note ||
              (state === "running"
                ? "Waiting on the index."
                : "The index resolves the counterpart and prints both texts. Where it cannot find one, it says so rather than pairing the nearest neighbour.")}
          </p>
          {ops && (
            <button
              onClick={() => setOnly((v) => !v)}
              className={cn(
                "shrink-0 self-start font-mono text-[11px] underline-offset-4 transition-colors hover:underline",
                only ? "text-gold" : "text-muted",
              )}
            >
              {only ? `changes only · ${changed} runs` : "changes only"}
            </button>
          )}
          {left && (
            <button
              onClick={() => copy(`${label}  ⇄  ${counterLabel}`, "pair")}
              className="flex shrink-0 items-center gap-1.5 self-start font-mono text-[11px] text-muted transition-colors hover:text-gold"
            >
              {copied === "pair" ? (
                <Check className="h-3 w-3 text-success" />
              ) : (
                <Copy className="h-3 w-3" strokeWidth={1.7} />
              )}
              copy both citations
            </button>
          )}
        </div>

        {res?.comparisonTable?.length > 0 && (
          <div className="mt-10 border-t border-hair pt-6">
            <p className="flex items-center gap-2 label-xs text-gold">
              <Columns2 className="h-3.5 w-3.5" strokeWidth={1.6} />
              comparison table, as returned
            </p>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full border border-hair text-left">
                <tbody>
                  {res.comparisonTable.map((row, i) => (
                    <tr key={i} className="border-b border-hair/70 last:border-b-0">
                      {Object.entries(row).map(([k, v]) => (
                        <td key={k} className="border-r border-hair/60 px-3 py-2 align-top last:border-r-0">
                          <p className="label-xs text-muted">{k}</p>
                          <p className="mt-1 whitespace-pre-wrap font-mono text-[11.5px] leading-[1.6] text-silver">
                            {typeof v === "string" ? v : JSON.stringify(v)}
                          </p>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
