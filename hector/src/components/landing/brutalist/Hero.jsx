"use client";

import { useCallback, useRef, useState } from "react";
import { ArrowRight, Hash, Terminal, TriangleAlert, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/landing/cn";
import { searchHector } from "@/lib/landing/api";
import { BATCH_QUERIES } from "@/lib/landing/samples";
import { Btn, Reveal, Tag, LiveCount } from "./ui";
import { Ticker } from "./Backdrop";
import { COMPARE_SECTIONS } from "@/lib/landing/samples";

const SUGGESTIONS = BATCH_QUERIES.slice(0, 4).map((b) => b.q);

/** Prints retrieved statutory text with the same anchor-aware colouring the app uses. */
function StatutoryText({ text }) {
  const lines = String(text || "").split("\n").filter(Boolean).slice(0, 60);
  return (
    <div className="font-mono text-[12px] leading-[1.8] text-paper/90 sm:text-[12.5px]">
      {lines.map((l, i) => {
        const t = l.trimStart();
        const kind = /^Provided\b/.test(t)
          ? "proviso"
          : /^(Exception|Explanation|Illustration)/.test(t)
            ? "gloss"
            : /^\d{1,4}[A-Za-z]?\.\s/.test(t)
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
              kind === "body" && "text-silver/95",
            )}
          >
            {t}
          </p>
        );
      })}
    </div>
  );
}

export function Hero({ records, recordsLoading, recordsFailed }) {
  const [q, setQ] = useState("");
  const [state, setState] = useState("idle"); // idle | running | done | failed
  const [res, setRes] = useState(null);
  const [openHit, setOpenHit] = useState(0);
  const abort = useRef(null);

  const run = useCallback(async (query) => {
    const value = String(query || "").trim();
    if (!value) return;
    abort.current?.abort();
    const ctrl = new AbortController();
    abort.current = ctrl;
    setState("running");
    setRes(null);
    setOpenHit(0);
    try {
      const out = await searchHector(value);
      if (ctrl.signal.aborted) return;
      setRes(out);
      setState("done");
    } catch (e) {
      if (ctrl.signal.aborted) return;
      setState("failed");
      setRes({ error: e?.message || "unreachable" });
    }
  }, []);

  const sources = res?.sources || [];
  const hit = sources[openHit];

  return (
    <section id="top" className="relative">
      <div className="mx-auto w-full max-w-[1400px] px-5 pb-12 pt-24 sm:px-8 md:pt-28 lg:pb-16 lg:pt-32">
        <div className="grid gap-12 lg:grid-cols-12 lg:gap-10">
          {/* -------------------------------------------------- title block */}
          <div className="lg:col-span-5 lg:pr-10">
            <Reveal y={false}>
              <div className="flex flex-wrap items-center gap-3 label-xs text-muted">
                <span className="text-gold">Bare Acts of India</span>
                <span className="h-3 w-px bg-hair" />
                <span>Verbatim corpus</span>
                <span className="h-3 w-px bg-hair" />
                <LiveCount records={records} loading={recordsLoading} failed={recordsFailed} />
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
                HECTOR's current PDF ingestion path recognises printed section headings and groups text around
                those boundaries. Sections longer than 4,000 characters may be split at sub-section or paragraph
                boundaries; very short sections may be merged with a neighbour. Search responses can include
                source citations, which should be checked against the published statute.
              </p>
            </Reveal>

            <Reveal delay={200}>
              <div className="mt-8 border-l border-gold/40 bg-panel/40 py-4 pl-5 pr-4">
                <p className="font-mono text-[12.5px] leading-[1.9] text-silver/90">
                  <span className="text-gold">Illustrative wording, not a statutory extract.</span>
                  <br />
                  <span className="text-gold">2. Definitions.</span>&mdash;In this instrument, unless the context otherwise
                  requires,&mdash;
                  <br />
                  <span className="pl-4">
                    <span className="text-gold/80">(a)</span> &ldquo;unit&rdquo; means the whole of a section, from its number to
                    the next;
                  </span>
                  <br />
                  <span className="pl-4">
                    <span className="text-gold/80">(b)</span> &ldquo;window&rdquo; means any fragment produced otherwise, and is
                    not admissible.
                  </span>
                </p>
              </div>
            </Reveal>

            <Reveal delay={260}>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <a href="#corpus">
                  <Btn>
                    See how it is built
                    <ArrowRight className="h-3 w-3 transition-transform duration-200 group-hover:translate-x-0.5" />
                  </Btn>
                </a>
                <a href="#compare">
                  <Btn variant="ghost">Compare IPC &harr; BNS</Btn>
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
                <Tag tone="neutral">batch runs</Tag>
                <Tag tone="active">
                  <span className="h-1 w-1 bg-success" /> source citations may appear
                </Tag>
              </div>
              <p className="mt-5 max-w-[52ch] font-mono text-[10.5px] leading-[1.7] text-muted">
                HECTOR &mdash; Hierarchical Evaluation of Civil-Criminal Textual&rsquo;s{" "}
                <span className="text-silver/80">Orchestrator &amp; Retrieval</span> &middot; statutory text only
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
                    <span className="hidden sm:inline">live endpoint</span>
                    <span
                      className={cn(
                        "h-1.5 w-1.5",
                        state === "running" ? "animate-pulse bg-warning" : state === "failed" ? "bg-error" : "bg-success",
                      )}
                    />
                    {state === "running" ? "querying" : state === "failed" ? "unreachable" : "ready"}
                  </div>
                </div>

                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    run(q);
                  }}
                  className="flex items-stretch gap-0 border-b border-hair"
                >
                  <span className="grid place-items-center pl-4 pr-2 font-mono text-[13px] text-gold">&sect;</span>
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
                    disabled={state === "running"}
                    className="group flex items-center gap-2 border-l border-hair bg-gold px-4 text-ink transition-colors duration-200 hover:bg-gold-light disabled:opacity-50"
                  >
                    <span className="label-xs">{state === "running" ? "…" : "Run"}</span>
                    <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
                  </button>
                </form>

                {/* Values below come from the live search response. */}
                <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 border-b border-hair bg-cream/60 px-4 py-2 font-mono text-[11px] text-muted">
                  <span>
                    route.<span className="text-silver/70">{res?.domain ?? "awaiting"}</span>
                  </span>
                  <span>
                    confidence.<span className="text-silver/70">{res?.confidence ?? "—"}</span>
                  </span>
                  <span>
                    sources.<span className="text-silver/70">{sources.length || "—"}</span>
                  </span>
                  <span className="ml-auto hidden sm:inline">
                    cache.<span className="text-silver/70">{res ? (res.cacheHit ? "hit" : "miss") : "—"}</span>
                  </span>
                </div>

                {state === "running" && (
                  <ul className="divide-y divide-hair/70 border-b border-hair">
                    <li className="flex items-center gap-3 px-4 py-2 font-mono text-[11.5px] text-muted">
                      <span className="h-1.5 w-1.5 animate-pulse bg-gold/70" />
                      Waiting for the search API response
                    </li>
                  </ul>
                )}

                {state === "failed" && (
                  <div className="px-4 py-10 text-center">
                    <p className="font-mono text-[12px] text-silver">The index did not answer.</p>
                    <p className="mx-auto mt-2 max-w-sm text-[12px] leading-relaxed text-muted">
                      This page does not fall back to a stored answer. Open the app to query the same endpoint
                      directly.
                    </p>
                    <a href="/search" className="mt-4 inline-block">
                      <Btn variant="ghost">Open the app</Btn>
                    </a>
                  </div>
                )}

                {state === "done" && !hit && (
                  <div className="px-4 py-10 text-center">
                    <p className="font-mono text-[12px] text-silver">No sources returned.</p>
                    <p className="mx-auto mt-2 max-w-sm text-[12px] leading-relaxed text-muted">
                      The request completed but the index matched no provision for that wording. Try a section
                      number, or one of the queries below.
                    </p>
                  </div>
                )}

                {state === "done" && hit && (
                  <div>
                    <div className="flex flex-wrap items-center gap-2 border-b border-hair px-4 py-3">
                      <span className="label-xs text-muted">returned source</span>
                      <div className="flex flex-wrap gap-1">
                        {sources.slice(0, 5).map((s, i) => (
                          <button
                            key={`${s.id}-${i}`}
                            onClick={() => setOpenHit(i)}
                            className={cn(
                              "border px-2 py-1 font-mono text-[11px] transition-colors duration-200",
                              i === openHit
                                ? "border-gold/70 bg-gold/10 text-gold-light"
                                : "border-hair text-muted hover:border-slate-custom hover:text-silver",
                            )}
                          >
                            {s.section || s.act}
                          </button>
                        ))}
                      </div>
                      <span className="ml-auto flex items-center gap-2">
                        {res?.confidenceWarning && (
                          <Tag tone="repealed">low confidence</Tag>
                        )}
                        <span className="font-mono text-[11px] text-muted">
                          score {Math.min(99, Math.round((hit.relevanceScore || 0) * 100))}
                        </span>
                      </span>
                    </div>

                    {res?.answer && (
                      <div className="border-b border-hair bg-ink/40 px-4 py-4 sm:px-6">
                        <p className="mb-2 flex items-center gap-2 label-xs text-gold">
                          <ShieldCheck className="h-3 w-3" strokeWidth={1.6} />
                          answer, grounded on the provision below
                        </p>
                        <p className="max-w-[80ch] whitespace-pre-wrap text-[13.5px] leading-[1.75] text-silver">
                          {res.answer}
                        </p>
                      </div>
                    )}

                    <div className="relative max-h-[300px] overflow-y-auto px-4 py-5 sm:px-6">
                      <p className="mb-3 flex flex-wrap items-center gap-2 label-xs text-gold">
                        <Hash className="h-3 w-3" strokeWidth={1.6} />
                        {hit.act}
                        {hit.section && <span className="text-muted">· {hit.section}</span>}
                      </p>
                      <StatutoryText text={hit.matchedText || hit.fullText} />
                    </div>

                    <div className="grid gap-px border-t border-hair bg-hair sm:grid-cols-4">
                      {[
                        ["citation", `${hit.act || "—"} ${hit.section || ""}`.trim()],
                        ["retrieval", `${Math.round((hit.rawScore || 0) * 100) / 100}`],
                        ["reranker", `${Math.round((hit.rerankerScore || 0) * 100) / 100}`],
                        ["cache", res?.cacheHit ? "hit" : "miss"],
                      ].map(([k, v]) => (
                        <div key={k} className="bg-panel px-4 py-3">
                          <p className="label-xs text-muted">{k}</p>
                          <p className="mt-1.5 font-mono text-[11.5px] text-paper/90">{v}</p>
                        </div>
                      ))}
                    </div>
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
                      className="border border-hair px-2 py-1 text-left font-mono text-[11px] text-silver transition-all duration-200 hover:-translate-y-px hover:border-gold/60 hover:text-gold-light"
                    >
                      {s.length > 58 ? `${s.slice(0, 56)}…` : s}
                    </button>
                  ))}
                </div>
              </div>
              <p className="mt-3 font-mono text-[10.5px] leading-relaxed text-muted">
                Runs on submit only. Each click issues one request to the live index; the answer and the
                scores above are whatever it returned.
              </p>
            </Reveal>
          </div>
        </div>
      </div>

      <Ticker pairs={COMPARE_SECTIONS} />

      {/* ---------------------------------------------- index figures */}
      <div className="mx-auto w-full max-w-[1400px] px-5 sm:px-8">
        <div className="grid grid-cols-2 gap-px border-x border-b border-hair bg-hair md:grid-cols-4">
          {[
            {
              v: recordsLoading ? "…" : recordsFailed || records === null ? "—" : records.toLocaleString("en-IN"),
              k: "records in the live index",
              s: "read from /readyz on page load",
            },
            { v: "1", k: "boundary grammar", s: "section heads, then safe cuts" },
            { v: "9", k: "validation gates", s: "every act must pass all nine" },
            { v: "2-pane", k: "section comparison", s: `${COMPARE_SECTIONS.length} pairs offered below` },
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
            Figures are live. The index reports its own size; this page does not hardcode one.
          </span>
        </div>
      </div>
    </section>
  );
}
