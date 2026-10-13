"use client";

import { useMemo, useState } from "react";
import { ScanLine, TriangleAlert, Regex, Check } from "lucide-react";
import { cn } from "@/lib/landing/cn";
import { Btn, Reveal, Tag, WideHead, WideSection } from "./ui";
import { FIXTURES, CHUNK_PAGE_TEXT } from "@/lib/landing/fixtures";
import { scanUnits, anchorTotals, numParts } from "@/lib/landing/boundary";
import { SOURCE_BUNDLE } from "@/lib/landing/scannerSource";
import { useCopy } from "@/lib/landing/hooks";

/**
 * A page as it comes off a scan, assembled by injecting scan furniture around
 * real section text. The section bodies are the fixtures; only the page
 * headers, page numbers and separators between them are synthetic.
 */
const SCANNED_PAGE = (() => {
  const bns101 = FIXTURES.find((f) => f.id === "bns-101");
  const bns103 = FIXTURES.find((f) => f.id === "bns-103");
  const a = (bns101?.text || "").split("\n").filter(Boolean);
  const b = (bns103?.text || "").split("\n").filter(Boolean);
  const mid = a.slice(8, 26).join("\n").replace("culpable homicide", "culpable-\nhomicide");
  return [
    "THE BHARATIYA NYAYA SANHITA, 2023",
    "(46 of 2023, 25.12.2023)",
    "",
    a.slice(0, 8).join("\n"),
    "",
    "—9—",
    "",
    "... continued from the preceding page ...",
    "",
    mid,
    "",
    "148",
    "",
    "* * *",
    "",
    a.slice(26).join("\n"),
    "",
    b.join("\n"),
  ].join("\n");
})();

const NOT_LAW = `Memorandum for the learned Senior:
Kindly settle the bail application. The Court took a view on 14.08 that the proviso to Section 37 NDPS is
not merely procedural. Three grounds, two of which are already in the paper. Revisiting the citation is not
necessary at this stage.`;

export function TesterSection() {
  const [text, setText] = useState(SCANNED_PAGE);
  const { copied, copy } = useCopy();

  const scan = useMemo(() => scanUnits(text), [text]);
  const units = scan.units;
  const totals = useMemo(() => anchorTotals(units), [units]);
  const headsSeen = useMemo(() => {
    let n = 0;
    text.split("\n").forEach((l) => {
      if (numParts(l)) n += 1;
    });
    return n;
  }, [text]);

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
            The patterns printed above are compiled and running in this page, against whatever you put in the
            left pane. Drop in a scanned page, a clean set of sections, or a memorandum that is not law at all,
            and read what the splitter decides — including what it refuses to treat as a unit.
          </>
        }
        controls={
          <div className="flex flex-wrap items-center gap-2 lg:justify-end">
            <Btn variant="ghost" onClick={() => setText(SCANNED_PAGE)}>
              A page off a scan
            </Btn>
            <Btn variant="ghost" onClick={() => setText(CHUNK_PAGE_TEXT)}>
              Four sections, clean
            </Btn>
            <Btn variant="quiet" onClick={() => setText(NOT_LAW)}>
              Something that isn&rsquo;t law
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
              heads found {headsSeen} · units {units.length} · covered {scan.covered.toLocaleString("en-IN")} ch
              · unabsorbed {scan.residual.toLocaleString("en-IN")} ch
            </span>
            <button
              onClick={() => copy(SOURCE_BUNDLE, "src")}
              className="ml-auto flex items-center gap-1.5 border border-hair px-2 py-1 font-mono text-[10.5px] text-silver transition-colors hover:border-gold/60 hover:text-gold"
            >
              {copied === "src" ? <Check className="h-3 w-3 text-success" /> : <ScanLine className="h-3 w-3" />}
              {copied === "src" ? "source copied" : "copy all patterns"}
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
              <span className="font-mono text-[10.5px] text-muted">{scan.dropped.length} dropped</span>
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
                become a unit, and a corpus that cannot be opened at a section boundary is not a statute index —
                it is a pile.
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
                      off {u.start}–{u.end} · {u.chars} ch
                    </span>
                  </div>
                  <p className="mt-1.5 line-clamp-2 whitespace-pre-wrap font-mono text-[11.5px] leading-[1.7] text-muted transition-colors duration-200 group-hover:text-silver/85">
                    {u.lines
                      .map((l) => l.text)
                      .join(" ")
                      .replace(/\s+/g, " ")
                      .trim()
                      .slice(0, 240)}
                  </p>
                  <p className="mt-1.5 flex flex-wrap gap-x-3 font-mono text-[10.5px]">
                    {[
                      ["clause", u.anchors.clause],
                      ["proviso", u.anchors.proviso],
                      ["exception", u.anchors.exception],
                      ["explanation", u.anchors.explanation],
                      ["illustration", u.anchors.illustration],
                    ].map(([k, v]) => (
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
                ["provisos kept", String(totals.proviso)],
                ["exceptions kept", String(totals.exception)],
                ["explanations kept", String(totals.explanation)],
                ["illustrations kept", String(totals.illustration)],
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
            unabsorbed matter ({scan.residual.toLocaleString("en-IN")} ch) is text lying outside any section
            anchor — running heads, the extent note, page furniture. It is dropped, never promoted to a chunk of
            its own; matter between two anchors belongs to the unit it sits in.
          </p>
        </div>
      </div>
    </WideSection>
  );
}
