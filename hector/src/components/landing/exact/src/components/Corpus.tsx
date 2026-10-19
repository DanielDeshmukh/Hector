import { useMemo, useState } from "react";
import { Search, X, ChevronRight, BookOpen, Hash, Layers, ArrowRight } from "lucide-react";
import { cn } from "../utils/cn";
import { Reveal, Tag, WideHead, WideSection } from "./ui";
import {
  ACT_CATEGORIES,
  ACTIVE_ACTS,
  ALL_ACTS,
  REPEALED_ACTS,
  REPEAL_LINKS,
  TOTAL_ACTS,
  type Act,
} from "../data/acts";
import { SHORT_CODE_COLLISIONS, CORPUS } from "../data/corpus";
import { canon, digest } from "../lib/text";

const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function Mark({ text, term }: { text: string; term: string }) {
  if (!term.trim()) return <>{text}</>;
  const parts = text.split(new RegExp(`(${esc(term.trim())})`, "gi"));
  return (
    <>
      {parts.map((p, i) =>
        i % 2 === 1 ? (
          <mark key={i} className="bg-gold/25 text-gold-light">
            {p}
          </mark>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </>
  );
}

export function CorpusSection() {
  const [term, setTerm] = useState("");
  const [cat, setCat] = useState<string>("all");
  const [status, setStatus] = useState<"all" | "Active" | "Repealed">("all");
  const [open, setOpen] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const t = term.trim().toLowerCase();
    return ACT_CATEGORIES.map((c) => {
      if (cat !== "all" && c.slug !== cat) return { ...c, acts: [] as Act[] };
      return {
        ...c,
        acts: c.acts.filter((a) => {
          if (status !== "all" && a.status !== status) return false;
          if (!t) return true;
          return (
            a.name.toLowerCase().includes(t) ||
            a.code.toLowerCase().includes(t) ||
            c.title.toLowerCase().includes(t) ||
            String(a.year).includes(t) ||
            (a.repeals ?? "").toLowerCase().includes(t)
          );
        }),
      };
    }).filter((c) => c.acts.length);
  }, [term, cat, status]);

  const shown = filtered.reduce((n, c) => n + c.acts.length, 0);
  const flat = filtered.flatMap((c) => c.acts.map((a) => ({ ...a, category: c.title })));

  return (
    <WideSection id="corpus">
      <WideHead
        no="01"
        kicker="The indexed corpus"
        title={
          <>
            Thirty-eight bare acts.
            <span className="block italic text-gold-light">Nothing between you and the text.</span>
          </>
        }
        lede={
          <>
            The index holds the statute as printed — long title, preamble, chapters, parts, sections, sub-sections,
            provisos, explanations, illustrations and schedules. Commentary, digests and headnotes are excluded,
            because a retrieval set should not be able to pass off a editorial summary as an enactment.
          </>
        }
        controls={
          <div className="flex flex-wrap items-center gap-2 lg:justify-end">
            <Tag tone="gold">{TOTAL_ACTS} statutes</Tag>
            <Tag tone="active">{ACTIVE_ACTS} in force</Tag>
            <Tag tone="repealed">{REPEALED_ACTS} repealed · still indexed</Tag>
          </div>
        }
      />

      {/* controls */}
      <div className="mt-10 flex flex-col gap-3 border border-hair bg-panel-2/60 p-3 lg:flex-row lg:items-center">
        <label className="group flex flex-1 items-center gap-3 border border-hair bg-cream px-3 py-2 transition-colors focus-within:border-gold/60">
          <Search className="h-3.5 w-3.5 text-muted transition-colors group-focus-within:text-gold" strokeWidth={1.7} />
          <input
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="Search statute, short code, year or the act it repealed — try “420”, “maintenance”, “1860”"
            className="min-w-0 flex-1 bg-transparent font-mono text-[12px] text-paper outline-none placeholder:text-muted/70"
          />
          {term && (
            <button onClick={() => setTerm("")} aria-label="Clear search" className="text-muted hover:text-gold">
              <X className="h-3.5 w-3.5" strokeWidth={1.7} />
            </button>
          )}
        </label>

        <div className="flex flex-wrap items-center gap-1.5">
          {[{ slug: "all", title: `All ${ACT_CATEGORIES.length}` }, ...ACT_CATEGORIES.map((c) => ({ slug: c.slug, title: `${c.title} ${c.acts.length}` }))].map(
            (c) => (
              <button
                key={c.slug}
                onClick={() => setCat(c.slug)}
                className={cn(
                  "border px-2 py-1 font-mono text-[10.5px] transition-colors duration-200",
                  cat === c.slug
                    ? "border-gold/70 bg-gold/10 text-gold-light"
                    : "border-hair text-muted hover:border-slate-custom hover:text-silver",
                )}
              >
                {c.title}
              </button>
            ),
          )}
          <span className="mx-1 hidden h-4 w-px bg-hair sm:block" />
          {(["all", "Active", "Repealed"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className={cn(
                "border px-2 py-1 font-mono text-[10.5px] uppercase tracking-wider transition-colors duration-200",
                status === s ? "border-silver/60 bg-slate-custom/30 text-paper" : "border-hair text-muted hover:text-silver",
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* table */}
      <div className="mt-px border border-hair bg-cream">
        <div className="hidden grid-cols-[44px_minmax(0,1fr)_88px_120px_120px_40px] gap-4 border-b border-hair bg-panel-2 px-4 py-2 label-xs text-muted md:grid">
          <span>#</span>
          <span>statute as printed</span>
          <span>year</span>
          <span>short code</span>
          <span>status</span>
          <span />
        </div>

        {filtered.length === 0 && (
          <div className="px-4 py-14 text-center">
            <p className="font-display text-[22px] italic text-silver/70">No enactment answers to “{term}”.</p>
            <p className="mt-2 text-[12px] text-muted">The index holds {TOTAL_ACTS} statutes; try a short code instead.</p>
          </div>
        )}

        {filtered.map((c) => (
          <div key={c.slug}>
            <div className="flex items-center gap-3 border-y border-hair bg-panel/70 px-4 py-1.5 first:border-t-0">
              <span className="label-xs text-gold">{c.title}</span>
              <span className="h-px flex-1 bg-hair" />
              <span className="font-mono text-[10.5px] text-muted">{c.acts.length} act{c.acts.length > 1 ? "s" : ""}</span>
            </div>
            {c.acts.map((a) => {
              const key = `${c.slug}-${a.code}-${a.year}`;
              const on = open === key;
              return (
                <div key={key} className="border-b border-hair/60 last:border-b-0">
                  <button
                    onClick={() => setOpen(on ? null : key)}
                    className={cn(
                      "group grid w-full grid-cols-[44px_minmax(0,1fr)_40px] items-center gap-4 px-4 py-3 text-left transition-colors duration-200 md:grid-cols-[44px_minmax(0,1fr)_88px_120px_120px_40px]",
                      on ? "bg-gold/[0.06]" : "hover:bg-panel/50",
                    )}
                  >
                    <span className="font-mono text-[10.5px] text-muted">
                      {String(ALL_ACTS.indexOf(a) + 1).padStart(2, "0")}
                    </span>
                    <span className="min-w-0">
                      <span className="block truncate text-[14px] leading-snug text-paper transition-colors duration-200 group-hover:text-gold-light">
                        <Mark text={a.name} term={term} />
                      </span>
                      {a.repeals && (
                        <span className="mt-0.5 block truncate font-mono text-[10.5px] text-muted">
                          repeals <Mark text={a.repeals} term={term} />
                        </span>
                      )}
                    </span>
                    <span className="hidden font-mono text-[11.5px] text-silver md:block">
                      <Mark text={String(a.year)} term={term} />
                    </span>
                    <span className="hidden md:block">
                      <span className="inline-flex items-center border border-slate-custom/80 px-1.5 py-0.5 font-mono text-[10.5px] text-gold-light">
                        <Mark text={a.code} term={term} />
                      </span>
                    </span>
                    <span className="hidden md:block">
                      <Tag tone={a.status === "Active" ? "active" : "repealed"}>{a.status}</Tag>
                    </span>
                    <ChevronRight
                      className={cn(
                        "h-3.5 w-3.5 text-muted transition-transform duration-300",
                        on && "rotate-90 text-gold",
                      )}
                      strokeWidth={1.7}
                    />
                  </button>

                  {on && (
                    <div className="grid gap-px border-t border-hair bg-hair md:grid-cols-[minmax(0,1fr)_260px]">
                      <div className="bg-panel px-4 py-4">
                        <p className="label-xs text-muted">reading note</p>
                        <p className="mt-2 max-w-[62ch] text-[13px] leading-[1.7] text-silver">
                          {a.note ?? `${a.name} is held as a single canonical string, amended text folded to the date of the last Gazette correction in the index. Units are addressed as ${a.code} § n.`}
                        </p>
                        <div className="mt-4 flex flex-wrap gap-x-8 gap-y-2 font-mono text-[11px]">
                          <span className="text-muted">
                            anchors.{" "}
                            <span className="text-silver">
                              {a.code === "Constitution" ? "ARTICLE · PART · SCHEDULE" : "SECTION · CHAPTER · PART · SCHEDULE"}
                            </span>
                          </span>
                          <span className="text-muted">
                            status. <span className={a.status === "Active" ? "text-success" : "text-error/80"}>{a.status}</span>
                          </span>
                          <span className="text-muted">
                            repeal entry. <span className="text-silver">{a.repeals ?? "none asserted"}</span>
                          </span>
                        </div>
                      </div>
                      <div className="bg-panel px-4 py-4">
                        <p className="label-xs text-muted">index digest</p>
                        <p className="mt-2 flex items-center gap-1.5 font-mono text-[11.5px] text-paper/90">
                          <Hash className="h-3 w-3 text-gold" strokeWidth={1.7} />
                          {a.code.toLowerCase()}-{digest(`${a.name}|${a.year}|${a.status}`).slice(0, 8)}
                        </p>
                        <p className="mt-3 text-[11.5px] leading-relaxed text-muted">
                          {CORPUS.filter((s) => s.code === a.code).length} unit(s) from this act are open for
                          inspection on this page.
                        </p>
                        <a href="#grammar" className="group mt-3 inline-flex items-center gap-1.5 label-xs text-gold hover:text-gold-light">
                          see the grammar
                          <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ))}

        <div className="flex flex-wrap items-center gap-4 border-t border-hair bg-panel-2 px-4 py-2.5 font-mono text-[10.5px] text-muted">
          <span>
            showing <span className="text-gold-light">{shown}</span> of {TOTAL_ACTS}
          </span>
          <span className="h-3 w-px bg-hair" />
          <span>filter: {cat === "all" ? "all categories" : cat} · {status}</span>
          <span className="ml-auto flex items-center gap-1.5">
            <Layers className="h-3 w-3" strokeWidth={1.6} /> {flat.length ? "click a row for the index entry" : ""}
          </span>
        </div>
      </div>

      {/* side bands */}
      <div className="mt-4 grid gap-px bg-hair lg:grid-cols-3">
        <div className="bg-cream px-4 py-4">
          <p className="flex items-center gap-2 label-xs text-gold">
            <BookOpen className="h-3.5 w-3.5" strokeWidth={1.6} />
            repeal entries carried on the index
          </p>
          <ul className="mt-3 space-y-2">
            {ALL_ACTS.filter((a) => a.repeals).map((a) => (
              <li key={`${a.code}-${a.year}`} className="flex items-baseline gap-2 border-b border-hair/60 pb-1.5 font-mono text-[11px] text-silver">
                <span className="text-gold-light">{a.code}</span>
                <span className="text-muted">{a.year}</span>
                <span className="text-muted">→</span>
                <span className="text-paper/80">{a.repeals}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-[11.5px] leading-relaxed text-muted">
            {REPEAL_LINKS} statutes in the index carry an express repeal. Both texts stay addressable — the repealed
            one is what a pre-commencement offence is charged under.
          </p>
        </div>

        <div className="bg-cream px-4 py-4">
          <p className="label-xs text-gold">short-code collisions</p>
          <p className="mt-2 text-[12.5px] leading-[1.6] text-silver">
            Three abbreviations are claimed twice across {TOTAL_ACTS} statutes. The resolver keeps both and pins the
            full long title before it answers, so a citation to “CA” is never silently resolved.
          </p>
          <ul className="mt-3 space-y-2">
            {SHORT_CODE_COLLISIONS.map((c) => (
              <li key={c} className="border-l-2 border-warning/50 py-1 pl-3 font-mono text-[11px] text-warning/85">
                {c}
              </li>
            ))}
          </ul>
        </div>

        <Reveal y={false} className="bg-cream">
          <div className="px-4 py-4">
            <p className="label-xs text-gold">unit extract on this page</p>
            <p className="mt-2 font-display text-[40px] leading-none text-paper">
              {CORPUS.length}
              <span className="ml-2 font-sans text-[12px] font-light italic text-silver">sections, whole</span>
            </p>
            <p className="mt-2 text-[11.5px] leading-relaxed text-muted">
              Opened so the grammar can be inspected rather than described: the criminal succession, the procedural
              pair, a bail provision, and two civil sections that every chambers asks about.
            </p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {CORPUS.slice(0, 8).map((s) => (
                <span key={s.id} className="border border-hair px-1.5 py-0.5 font-mono text-[10px] text-silver">
                  {s.code} §{s.section.replace(/^Article\s+/, "Art. ")}
                </span>
              ))}
              <span className="border border-hair px-1.5 py-0.5 font-mono text-[10px] text-muted">
                +{Math.max(0, CORPUS.length - 8)}
              </span>
            </div>
          </div>
        </Reveal>
      </div>
    </WideSection>
  );
}

export const canonOf = (id: string) => {
  const s = CORPUS.find((x) => x.id === id);
  return s ? canon(s) : "";
};
