import { useMemo, useState } from "react";
import { ScanLine, TriangleAlert, Regex, Check } from "lucide-react";
import { cn } from "../utils/cn";
import { Btn, Reveal, Tag, WideHead, WideSection } from "./ui";
import { BOUNDARY_SOURCE, canon, regexUnits } from "../lib/text";
import { byId } from "../data/corpus";
import { useCopy } from "../lib/hooks";

const MESSY = `THE BHARATIYA NYAYA SANHITA, 2023
(46 of 2023, 25.12.2023)
101. Culpable homicide.—Whoever causes death by doing an act with the intention of causing death, or with such intention as aforesaid, shall be punishable with imprisonment for life or with fine which may extend to ten years.
102. Murder.—Except in the cases hereinafter excepted, culpable homicide is murder,—
first, if the act by which the death is caused is done with the intention of causing death;
secondly, if it is done with the intention of causing such bodily injury as the offender knows to be likely to cause death.
Exception 1.—Culpable homicide is not murder if the offender, whilst deprived of the power of self-control by grave and sudden provocation, causes the death of the person who gave the provocation.
Illustration.—A is provoked by B and kills him in the heat of passion.
Short title and commencement.
103. Punishment for murder.—Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.`;

const CLEAN = [byId("ipc-124a"), byId("bns-152")].map((s) => canon(s!)).join("\n");

const NOT_LAW = `Memorandum for the learned Senior:
Kindly settle the bail application. The Court took a view on 14.08 that the proviso to Section 37 NDPS is not merely procedural. Three grounds, two of which are already in thePaper. Revisiting the citation is not necessary at this stage.`;

export function TesterSection() {
  const [text, setText] = useState(MESSY);
  const { copied, copy } = useCopy();

  const units = useMemo(() => regexUnits(text), [text]);
  const covered = units.reduce((n, u) => n + u.text.length, 0);
  const residual = Math.max(0, text.length - covered);
  const totalAnchors = units.reduce(
    (a, u) => ({
      proviso: a.proviso + u.anchors.proviso,
      exception: a.exception + u.anchors.exception,
      explanation: a.explanation + u.anchors.explanation,
      illustration: a.illustration + u.anchors.illustration,
      clause: a.clause + u.anchors.clause,
    }),
    { proviso: 0, exception: 0, explanation: 0, illustration: 0, clause: 0 },
  );

  return (
    <WideSection id="tester">
      <WideHead
        no="03A"
        kicker="Insertion · live boundary test"
        title={
          <>
            Paste your own text.
            <span className="block italic text-gold-light">Run the grammar on it.</span>
          </>
        }
        lede={
          <>
            The pattern compiled above is running in this page. Drop in a section, a page torn out of a bare act, or
            a memorandum that is not law at all — and read what the splitter decides, including what it refuses to
            treat as a chunk.
          </>
        }
        controls={
          <div className="flex flex-wrap items-center gap-2 lg:justify-end">
            <Btn variant="ghost" onClick={() => setText(MESSY)}>
              Messy bare-act page
            </Btn>
            <Btn variant="ghost" onClick={() => setText(CLEAN)}>
              Two mapped sections
            </Btn>
            <Btn variant="quiet" onClick={() => setText(NOT_LAW)}>
              Something that isn’t law
            </Btn>
          </div>
        }
      />

      <div className="mt-10 grid gap-px bg-hair lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
        <div className="bg-cream">
          <div className="flex items-center justify-between border-b border-hair bg-panel-2 px-4 py-2.5">
            <span className="flex items-center gap-2 label-xs text-silver">
              <Regex className="h-3.5 w-3.5 text-gold" strokeWidth={1.5} />
              input · as printed
            </span>
            <span className="font-mono text-[10.5px] text-muted">{text.length.toLocaleString("en-IN")} ch</span>
          </div>
          <textarea
            value={text}
            spellCheck={false}
            onChange={(e) => setText(e.target.value)}
            className="h-[360px] w-full resize-none bg-transparent px-4 py-4 font-mono text-[12px] leading-[1.9] text-paper/90 outline-none placeholder:text-muted"
            placeholder="Paste a section here…"
          />
          <div className="flex flex-wrap items-center gap-2 border-t border-hair bg-panel-2 px-4 py-2.5">
            <span className="font-mono text-[10.5px] text-muted">
              units {units.length} · covered {covered.toLocaleString("en-IN")} ch · unabsorbed {residual.toLocaleString("en-IN")} ch
            </span>
            <button
              onClick={() => copy(BOUNDARY_SOURCE, "src")}
              className="ml-auto flex items-center gap-1.5 border border-hair px-2 py-1 font-mono text-[10.5px] text-silver transition-colors hover:border-gold/60 hover:text-gold"
            >
              {copied === "src" ? <Check className="h-3 w-3 text-success" /> : <ScanLine className="h-3 w-3" />}
              {copied === "src" ? "source copied" : "copy pattern"}
            </button>
          </div>
        </div>

        <div className="bg-cream">
          <div className="flex items-center justify-between border-b border-hair bg-panel-2 px-4 py-2.5">
            <span className="label-xs text-silver">units emitted</span>
            <span className="flex items-center gap-2">
              {units.length ? (
                <Tag tone="active">
                  <span className="h-1 w-1 bg-success" /> boundary-respected
                </Tag>
              ) : (
                <Tag tone="repealed">
                  <span className="h-1 w-1 bg-error" /> refused
                </Tag>
              )}
              <span className="font-mono text-[10.5px] text-muted">/g</span>
            </span>
          </div>

          {units.length === 0 ? (
            <div className="flex h-[360px] flex-col justify-center px-6">
              <p className="flex items-center gap-2 font-display text-[26px] leading-tight text-paper">
                <TriangleAlert className="h-5 w-5 text-error/80" strokeWidth={1.5} />
                The grammar found no section anchor.
              </p>
              <p className="mt-3 max-w-[54ch] text-[13px] leading-[1.7] text-silver">
                Nothing was invented to fill the gap. Input that is not drafted as a numbered provision does not
                become a unit, and a corpus that cannot be opened at a section boundary is not a statute index — it is
                a pile.
              </p>
              <p className="mt-4 border-l-2 border-error/50 pl-3 font-mono text-[11.5px] leading-relaxed text-muted">
                expected: a line beginning with a section number and a marginal note, e.g.
                <br />
                <span className="text-gold-light">103. Punishment for murder.—</span>Whoever commits murder…
              </p>
            </div>
          ) : (
            <ol className="max-h-[360px] divide-y divide-hair/70 overflow-y-auto">
              {units.map((u) => (
                <li key={u.index} className="group px-4 py-3.5 transition-colors duration-200 hover:bg-panel/60">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span className="font-mono text-[11px] text-gold">u{String(u.index + 1).padStart(2, "0")}</span>
                    <span className="font-mono text-[12.5px] text-paper">§ {u.number}</span>
                    <span className="truncate text-[13px] italic text-silver/90">{u.marginal || "—"}</span>
                    <span className="ml-auto font-mono text-[10.5px] text-muted">
                      off {u.start}–{u.end} · {u.text.length} ch
                    </span>
                  </div>
                  <p className="mt-1.5 line-clamp-2 whitespace-pre-wrap font-mono text-[11.5px] leading-[1.7] text-muted transition-colors duration-200 group-hover:text-silver/85">
                    {u.text.replace(/\s+/g, " ").trim()}
                  </p>
                  <p className="mt-1.5 flex flex-wrap gap-x-3 font-mono text-[10.5px]">
                    {(
                      [
                        ["clause", u.anchors.clause],
                        ["proviso", u.anchors.proviso],
                        ["exception", u.anchors.exception],
                        ["explanation", u.anchors.explanation],
                        ["illustration", u.anchors.illustration],
                      ] as const
                    ).map(([k, v]) => (
                      <span key={k} className={cn(v ? "text-gold/80" : "text-slate-custom")}>
                        {k} {v}
                      </span>
                    ))}
                  </p>
                </li>
              ))}
            </ol>
          )}

          <Reveal y={false}>
            <div className="grid grid-cols-2 gap-px border-t border-hair bg-hair sm:grid-cols-5">
              {[
                ["units", String(units.length)],
                ["provisos kept", String(totalAnchors.proviso)],
                ["exceptions kept", String(totalAnchors.exception)],
                ["explanations kept", String(totalAnchors.explanation)],
                ["illustrations kept", String(totalAnchors.illustration)],
              ].map(([k, v]) => (
                <div key={k} className="bg-cream px-3 py-2.5">
                  <p className="label-xs text-muted">{k}</p>
                  <p className={cn("mt-1 font-display text-[20px] leading-none", v === "0" ? "text-slate-custom" : "text-gold-light")}>
                    {v}
                  </p>
                </div>
              ))}
            </div>
          </Reveal>
          <p className="border-t border-hair bg-panel px-4 py-2.5 font-mono text-[10.5px] leading-relaxed text-muted">
            unabsorbed matter ({residual.toLocaleString("en-IN")} ch) is text lying outside any anchor — running
            heads, the extent note, page furniture. It is dropped, never promoted to a chunk of its own; matter
            between two anchors belongs to the unit it sits in.
          </p>
        </div>
      </div>
    </WideSection>
  );
}
