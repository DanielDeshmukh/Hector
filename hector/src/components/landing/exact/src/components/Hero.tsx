import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowRight, Hash, Terminal, TriangleAlert } from "lucide-react";
import { cn } from "../utils/cn";
import { Btn, Reveal, Tag } from "./ui";
import { Ticker } from "./Chrome";
import { CORPUS, MAPPINGS } from "../data/corpus";
import { TOTAL_ACTS, ACT_CATEGORIES, REPEAL_LINKS } from "../data/acts";
import { canon, digest, parseQuery, retrieve, SAMPLE_QUERY, type Hit } from "../lib/text";

const SUGGESTIONS = [
  "Section 302 IPC punishment for murder",
  "BNS section corresponding to 420 IPC",
  "Inherent powers of the High Court BNSS",
  "NDPS Section 37 bail commercial quantity",
];

const STEPS = [
  "parse query · extract § / act identity",
  "compile boundary grammar · 9 groups",
  "resolve statutory identity before text",
  "open unit · provisos, exceptions, illustrations attached",
  "stamp citations · char offsets on every sentence",
];

/** prints statutory text with anchor-aware colouring */
function StatutoryText({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <div className="font-mono text-[12.5px] leading-[1.85] text-paper/90 sm:text-[13px]">
      {lines.map((l, i) => {
        const trimmed = l.trimStart();
        const kind = /^Provided\b/.test(trimmed)
          ? "proviso"
          : /^(Exception|Explanation|Illustration)/.test(trimmed)
            ? "gloss"
            : /^\d{1,4}[A-Za-z]?\.\s|^[Aa]rticle\s/.test(trimmed)
              ? "head"
              : "body";
        return (
          <p
            key={i}
            className={cn(
              "whitespace-pre-wrap",
              kind === "head" && "text-gold",
              kind === "proviso" && "text-warning/90 italic",
              kind === "gloss" && "text-info/85",
              kind === "body" && "pl-0 text-silver/95",
            )}
          >
            {kind === "head" ? (
              <span className="font-semibold tracking-tight">
                {trimmed.split(".")[0]}.
                <span className="text-paper/90 font-normal italic"> {trimmed.split(".").slice(1).join(".").trim()}</span>
              </span>
            ) : kind === "gloss" ? (
              <>
                <span className="text-paper/45">{"\t"}</span>
                <span className="font-medium">{trimmed.split(".—")[0]}.—</span>
                <span className="text-silver/90">{trimmed.split(".—").slice(1).join(".—")}</span>
              </>
            ) : (
              <>
                {kind === "proviso" && <span>{"\t"}</span>}
                {trimmed}
              </>
            )}
          </p>
        );
      })}
    </div>
  );
}

export function Hero() {
  const [q, setQ] = useState("");
  const [phase, setPhase] = useState<"idle" | "running" | "done">("idle");
  const [step, setStep] = useState(0);
  const [hits, setHits] = useState<Hit[]>([]);
  const [openHit, setOpenHit] = useState(0);
  const timers = useRef<number[]>([]);

  const clearTimers = () => {
    timers.current.forEach((t) => window.clearTimeout(t));
    timers.current = [];
  };

  const run = useCallback((query: string) => {
    const value = query.trim();
    if (!value) return;
    clearTimers();
    setPhase("running");
    setStep(0);
    setOpenHit(0);
    STEPS.forEach((_, i) => {
      timers.current.push(
        window.setTimeout(() => setStep(i + 1), 105 + i * 92),
      );
    });
    timers.current.push(
      window.setTimeout(
        () => {
          setHits(retrieve(value, 3));
          setPhase("done");
        },
        105 + STEPS.length * 92,
      ),
    );
  }, []);

  // one automatic demonstration on first load
  useEffect(() => {
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const start = Date.now();
    let raf = 0;
    if (reduce) {
      setQ(SAMPLE_QUERY);
      run(SAMPLE_QUERY);
    } else {
      const tick = () => {
        const elapsed = Date.now() - start - 700;
        if (elapsed < 0) {
          raf = requestAnimationFrame(tick);
          return;
        }
        const n = Math.min(SAMPLE_QUERY.length, Math.floor(elapsed / 26));
        setQ(SAMPLE_QUERY.slice(0, n));
        if (n < SAMPLE_QUERY.length) raf = requestAnimationFrame(tick);
        else run(SAMPLE_QUERY);
      };
      raf = requestAnimationFrame(tick);
    }
    return () => {
      cancelAnimationFrame(raf);
      clearTimers();
    };
  }, [run]);

  const parsed = parseQuery(q);
  const hit = hits[openHit];

  return (
    <section id="top" className="relative">
      <div className="mx-auto w-full max-w-[1400px] px-5 pb-12 pt-24 sm:px-8 md:pt-28 lg:pb-16 lg:pt-32">
        <div className="grid gap-12 lg:grid-cols-12 lg:gap-10">
          {/* -------------------------------------------------- title block */}
          <div className="lg:col-span-5 lg:pr-10">
            <Reveal y={false}>
              <div className="flex flex-wrap items-center gap-3 label-xs text-muted">
                <span className="text-gold">Act No. IV of 2025</span>
                <span className="h-3 w-px bg-hair" />
                <span>In force</span>
                <span className="h-3 w-px bg-hair" />
                <span>Ref. HECTOR/RET/38</span>
              </div>
            </Reveal>

            <Reveal delay={70}>
              <h1 className="mt-7 font-display text-[clamp(2.9rem,7.4vw,5.9rem)] font-medium leading-[0.87] tracking-[-0.035em] text-paper">
                A section
                <span className="block pl-[0.06em]">is the unit.</span>
                <span className="mt-2 block font-display text-[clamp(1.15rem,2.5vw,1.95rem)] italic leading-tight tracking-[-0.01em] text-gold-light">
                  Everything else is a fragment.
                </span>
              </h1>
            </Reveal>

            <Reveal delay={140}>
              <p className="mt-8 max-w-[46ch] text-[15.5px] leading-[1.78] text-silver">
                Hector is a retrieval instrument over <span className="text-paper">38 Indian bare acts</span>. The
                corpus is not sliced to fit a window — it is divided by one deterministic regular expression that
                recognises a single boundary: the printed section number. Provisos, exceptions, explanations and
                illustrations therefore travel with the rule they qualify, and every sentence returned can be traced
                to a clause and a character offset.
              </p>
            </Reveal>

            <Reveal delay={200}>
              <div className="mt-8 border-l border-gold/40 bg-panel/40 py-4 pl-5 pr-4">
                <p className="font-mono text-[12.5px] leading-[1.9] text-silver/90">
                  <span className="text-gold">2. Definitions.</span>—In this instrument, unless the context otherwise
                  requires,—
                  <br />
                  <span className="pl-4">
                    <span className="text-gold/80">(a)</span> “unit” means the whole of a section, from its number to
                    the next;
                  </span>
                  <br />
                  <span className="pl-4">
                    <span className="text-gold/80">(b)</span> “window” means any fragment produced otherwise, and is
                    not admissible.
                  </span>
                </p>
              </div>
            </Reveal>

            <Reveal delay={260}>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <a href="#corpus">
                  <Btn>
                    Browse the 38 acts
                    <ArrowRight className="h-3 w-3 transition-transform duration-200 group-hover:translate-x-0.5" />
                  </Btn>
                </a>
                <a href="#compare">
                  <Btn variant="ghost">
                    Compare IPC ⇄ BNS
                  </Btn>
                </a>
                <a href="#grammar">
                  <Btn variant="quiet" className="underline-offset-4 hover:underline">
                    Read the grammar
                  </Btn>
                </a>
              </div>
            </Reveal>

            <Reveal delay={320}>
              <div className="mt-9 flex flex-wrap gap-2">
                <Tag tone="gold">regex chunking</Tag>
                <Tag tone="neutral">section comparison</Tag>
                <Tag tone="neutral">batch ≤ 50</Tag>
                <Tag tone="active">
                  <span className="h-1 w-1 bg-success" /> offset-level citation
                </Tag>
              </div>
              <p className="mt-5 max-w-[52ch] font-mono text-[10.5px] leading-[1.7] text-muted">
                HECTOR — Hierarchical Evaluation of Civil-Criminal Textual’s{" "}
                <span className="text-silver/80">Orchestrator &amp; Retrieval</span> · index of 38 bare acts ·
                statutory text only
              </p>
            </Reveal>
          </div>

          {/* -------------------------------------------------- the console */}
          <div className="lg:col-span-7">
            <Reveal delay={120}>
              <div className="relative border border-hair bg-panel shadow-[0_40px_120px_-40px_rgba(0,0,0,0.9)]">
                <div className="flex items-center justify-between gap-3 border-b border-hair bg-panel-2 px-4 py-2.5">
                  <div className="flex items-center gap-2.5 label-xs text-silver">
                    <Terminal className="h-3.5 w-3.5 text-gold" strokeWidth={1.5} />
                    hector://index/query
                  </div>
                  <div className="flex items-center gap-3 label-xs text-muted">
                    <span className="hidden sm:inline">grammar 4.2 · gm</span>
                    <span className={cn("h-1.5 w-1.5", phase === "running" ? "bg-warning animate-pulse" : "bg-success")} />
                    {phase === "running" ? "resolving" : "ready"}
                  </div>
                </div>

                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    run(q);
                  }}
                  className="flex items-stretch gap-0 border-b border-hair"
                >
                  <span className="grid place-items-center pl-4 pr-2 font-mono text-[13px] text-gold">§</span>
                  <input
                    value={q}
                    onChange={(e) => setQ(e.target.value)}
                    spellCheck={false}
                    aria-label="Ask the statutory index"
                    placeholder="Ask for a provision, a section number, or an old Code citation"
                    className="min-w-0 flex-1 bg-transparent py-4 pr-3 font-mono text-[13px] text-paper placeholder:text-muted/80"
                  />
                  <button
                    type="submit"
                    className="group flex items-center gap-2 border-l border-hair bg-gold px-4 text-ink transition-colors duration-200 hover:bg-gold-light"
                  >
                    <span className="label-xs">Run</span>
                    <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
                  </button>
                </form>

                {/* parse readout */}
                <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 border-b border-hair bg-cream/60 px-4 py-2 font-mono text-[11px] text-muted">
                  <span>
                    act.<span className={cn(parsed.code ? "text-gold-light" : "text-silver/50")}>{parsed.code ?? "auto"}</span>
                  </span>
                  <span>
                    §.<span className={cn(parsed.number ? "text-gold-light" : "text-silver/50")}>{parsed.number ?? "inferred"}</span>
                  </span>
                  <span>
                    terms.<span className="text-silver/70">{parsed.words.length}</span>
                  </span>
                  <span className="ml-auto hidden sm:inline">
                    corpus.<span className="text-silver/70">{CORPUS.length} shown · {TOTAL_ACTS} acts</span>
                  </span>
                </div>

                {/* pipeline trace */}
                {phase === "running" && (
                  <ul className="divide-y divide-hair/70 border-b border-hair">
                    {STEPS.map((s, i) => (
                      <li
                        key={s}
                        className={cn(
                          "flex items-center gap-3 px-4 py-2 font-mono text-[11.5px] transition-colors duration-200",
                          i < step ? "text-silver" : "text-muted/45",
                        )}
                      >
                        <span className={cn("w-4 text-right", i < step ? "text-success" : "text-muted/40")}>
                          {i < step ? "✓" : "·"}
                        </span>
                        {s}
                        {i === step && <span className="ml-auto h-px w-10 animate-pulse bg-gold/70" />}
                      </li>
                    ))}
                  </ul>
                )}

                {/* answer */}
                {phase === "done" && hit && (
                  <div>
                    <div className="flex flex-wrap items-center gap-2 border-b border-hair px-4 py-3">
                      <span className="label-xs text-muted">returned unit</span>
                      <div className="flex flex-wrap gap-1">
                        {hits.map((h, i) => (
                          <button
                            key={h.section.id}
                            onClick={() => setOpenHit(i)}
                            className={cn(
                              "border px-2 py-1 font-mono text-[11px] transition-colors duration-200",
                              i === openHit
                                ? "border-gold/70 bg-gold/10 text-gold-light"
                                : "border-hair text-muted hover:border-slate-custom hover:text-silver",
                            )}
                          >
                            {h.section.code} §{h.section.section.replace(/^Article\s/, "Art. ")}
                          </button>
                        ))}
                      </div>
                      <span className="ml-auto flex items-center gap-2">
                        <Tag tone={hit.section.status === "Active" ? "active" : "repealed"}>
                          {hit.section.status}
                        </Tag>
                        <span className="font-mono text-[11px] text-muted">
                          score {Math.min(99, Math.round(hit.score))}
                        </span>
                      </span>
                    </div>

                    <div className="relative max-h-[340px] overflow-y-auto px-4 py-5 sm:px-6">
                      <p className="mb-3 flex flex-wrap items-center gap-2 label-xs text-gold">
                        <Hash className="h-3 w-3" strokeWidth={1.6} />
                        {hit.section.act}
                        <span className="text-muted">· {hit.section.chapter}</span>
                      </p>
                      <StatutoryText text={canon(hit.section)} />
                      {hit.chars > 560 && (
                        <p className="mt-4 flex items-start gap-2 border-t border-hair/70 pt-3 text-[11.5px] leading-relaxed text-muted">
                          <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning/80" strokeWidth={1.5} />
                          Unit printed whole — {hit.chars.toLocaleString("en-IN")} characters. Nothing was truncated
                          to fit the pane.
                        </p>
                      )}
                    </div>

                    <div className="grid gap-px border-t border-hair bg-hair sm:grid-cols-4">
                      {[
                        ["citation", `${hit.section.code} §${hit.section.section.replace(/^Article\s+/, "Art. ")}`],
                        ["unit id", `u-${digest(canon(hit.section))}`],
                        ["anchors", `${hit.anchors.proviso}P · ${hit.anchors.exception}E · ${hit.anchors.explanation}X · ${hit.anchors.illustration}I`],
                        ["offset", `${hit.chars ? `${Math.round(hit.chars * 0.31)}` : "0"}–${hit.chars.toLocaleString("en-IN")}`],
                      ].map(([k, v]) => (
                        <div key={k} className="bg-panel px-4 py-3">
                          <p className="label-xs text-muted">{k}</p>
                          <p className="mt-1.5 font-mono text-[11.5px] text-paper/90">{v}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {phase === "done" && !hit && (
                  <div className="px-4 py-10 text-center">
                    <p className="font-mono text-[12px] text-silver">
                      No unit in the demonstration extract answers that query.
                    </p>
                    <p className="mx-auto mt-2 max-w-sm text-[12px] leading-relaxed text-muted">
                      The live index resolves across all {TOTAL_ACTS} statutes; this page ships a{" "}
                      {CORPUS.length}-unit extract so the grammar can be inspected rather than described.
                    </p>
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-2 border-t border-hair bg-panel-2 px-4 py-3">
                  <span className="label-xs text-muted">try</span>
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => {
                        setQ(s);
                        run(s);
                      }}
                      className="border border-hair px-2 py-1 font-mono text-[11px] text-silver transition-all duration-200 hover:-translate-y-px hover:border-gold/60 hover:text-gold-light"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            </Reveal>
          </div>
        </div>
      </div>

      <Ticker />

      {/* ---------------------------------------------- index figures */}
      <div className="mx-auto w-full max-w-[1400px] px-5 sm:px-8">
        <div className="grid grid-cols-2 gap-px border-x border-b border-hair bg-hair md:grid-cols-5">
          {[
            { v: String(TOTAL_ACTS), k: "bare acts indexed", s: "8 categories · 3 repealed" },
            { v: "1", k: "boundary grammar", s: "9 capture groups" },
            { v: "≤50", k: "queries per batch", s: "one queue, one table" },
            { v: "2-pane", k: "section comparison", s: `${MAPPINGS.length} mapped pairs live` },
            { v: String(REPEAL_LINKS), k: "repeal entries", s: "repealed statutes pinned" },
          ].map((f) => (
            <Reveal key={f.k} className="bg-cream last:col-span-2 md:last:col-span-1">
              <div className="group px-5 py-6 transition-colors duration-300 hover:bg-panel/60">
                <p className="font-display text-[clamp(1.7rem,3.2vw,2.6rem)] leading-none tracking-tight text-paper transition-colors duration-300 group-hover:text-gold-light">
                  {f.v}
                </p>
                <p className="mt-3 label-xs text-silver">{f.k}</p>
                <p className="mt-1 font-mono text-[10.5px] text-muted">{f.s}</p>
              </div>
            </Reveal>
          ))}
        </div>
        <div className="border-b border-hair bg-cream px-3 py-2.5 text-[11px] text-muted">
          <span className="font-mono">
            Categories: {ACT_CATEGORIES.map((c) => `${c.title} (${c.acts.length})`).join(" · ")}
          </span>
        </div>
      </div>
    </section>
  );
}


