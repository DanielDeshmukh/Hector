import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useRef, useState } from "react";
import { Check, Copy, Download, Play, Square } from "lucide-react";
import { cn } from "../utils/cn";
import { Btn, Reveal } from "./ui";
import { CORPUS } from "../data/corpus";
import { TOTAL_ACTS } from "../data/acts";
import { digest, parseQuery, retrieve, SAMPLE_BATCH } from "../lib/text";
import { useCopy } from "../lib/hooks";
const MAX = 50;
const normalise = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
function build(raw) {
  const lines = raw.split("\n").map((l) => l.trim()).filter(Boolean).slice(0, MAX);
  const seen = /* @__PURE__ */ new Map();
  return lines.map((text, i) => {
    const p = parseQuery(text);
    const key = `${p.code ?? "auto"}#${p.number ?? normalise(text).split(" ").filter((w) => w.length > 4).slice(0, 3).join("")}`;
    const dupOf = seen.get(key);
    if (dupOf === void 0) seen.set(key, i + 1);
    return {
      id: i + 1,
      text,
      status: dupOf ? "duplicate" : "queued",
      code: p.code,
      number: p.number,
      hits: [],
      ms: 0,
      dupOf
    };
  });
}
const run = (text) => {
  const hits = retrieve(text, 3);
  return {
    hits,
    ms: hits.length ? 6 + parseInt(digest(text).slice(0, 3), 16) % 29 : 0
  };
};
const dot = (r) => r.status === "resolved" ? "bg-success" : r.status === "unresolved" ? "bg-warning" : r.status === "duplicate" ? "bg-slate-custom" : r.status === "resolving" ? "bg-gold" : "bg-slate-custom/60";
function BatchSection() {
  const [line, setLine] = useState("");
  const [paste, setPaste] = useState("");
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState([]);
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const cur = useRef(-1);
  const ref = useRef([]);
  const { copied, copy } = useCopy();
  const queue = open ? paste : line;
  const count = queue.split("\n").map((l) => l.trim()).filter(Boolean).length;
  const start = () => {
    const built = build(queue);
    if (!built.length) return;
    ref.current = built;
    setRows(built);
    cur.current = -1;
    setElapsed(0);
    setRunning(true);
  };
  const addLine = () => {
    if (!line.trim()) return;
    setPaste((p) => p ? `${p}
${line.trim()}` : line.trim());
    setOpen(true);
    setLine("");
  };
  useEffect(() => {
    if (!running) return;
    const tick = window.setInterval(() => {
      const n = cur.current + 1;
      if (n >= ref.current.length) {
        setRunning(false);
        window.clearInterval(tick);
        return;
      }
      cur.current = n;
      setRows(
        (rs) => rs.map((r, i) => {
          if (i !== n || r.status === "duplicate") return r;
          const out = run(r.text);
          return { ...r, ...out, status: out.hits.length ? "resolved" : "unresolved" };
        })
      );
    }, 90);
    const clock = window.setInterval(() => setElapsed((e) => e + 90), 90);
    return () => {
      window.clearInterval(tick);
      window.clearInterval(clock);
    };
  }, [running]);
  const done = rows.filter((r) => r.status === "resolved" || r.status === "unresolved").length;
  const stats = useMemo(
    () => ({
      resolved: rows.filter((r) => r.status === "resolved").length,
      unresolved: rows.filter((r) => r.status === "unresolved").length,
      dups: rows.filter((r) => r.status === "duplicate").length
    }),
    [rows]
  );
  const csv = useMemo(() => {
    const head = "n,query,act,section,status,citation,ms";
    const body = rows.map((r) => {
      const t = r.hits[0];
      const esc = (v) => `"${v.replace(/"/g, '""')}"`;
      return [
        r.id,
        esc(r.text),
        r.code ?? "",
        r.number ?? "",
        r.status,
        esc(t ? `${t.section.act}, ${t.section.section}` : "unresolved"),
        r.ms
      ].join(",");
    });
    return [head, ...body].join("\n");
  }, [rows]);
  const annexure = rows.filter((r) => r.hits[0]).map((r) => `${r.id}.  ${r.hits[0].section.act}, ${r.hits[0].section.section} [${r.hits[0].section.status}]`).join("\n");
  const export_csv = () => {
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `hector-batch-${rows.length}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };
  return /* @__PURE__ */ jsx("section", { id: "batch", className: "relative border-t border-hair bg-ink/40", children: /* @__PURE__ */ jsxs("div", { className: "mx-auto w-full max-w-[1080px] px-5 py-16 sm:px-8 md:py-24", children: [
    /* @__PURE__ */ jsx(Reveal, { y: false, children: /* @__PURE__ */ jsxs("div", { className: "flex flex-col gap-5 border-b border-hair pb-6 lg:flex-row lg:items-end lg:justify-between", children: [
      /* @__PURE__ */ jsxs("div", { children: [
        /* @__PURE__ */ jsx("p", { className: "label-xs text-gold", children: "05 \xB7 Batch runs" }),
        /* @__PURE__ */ jsxs("h2", { className: "mt-4 max-w-[22ch] font-display text-[clamp(1.9rem,4.4vw,3.1rem)] leading-[0.94] tracking-[-0.025em] text-paper", children: [
          "Fifty questions.",
          /* @__PURE__ */ jsx("span", { className: "block italic text-gold-light", children: "One queue." })
        ] })
      ] }),
      /* @__PURE__ */ jsx("p", { className: "max-w-[40ch] text-[13.5px] leading-[1.7] text-silver", children: "Type a question and press enter, or paste a list. Each resolves to one citation, one line, in order." })
    ] }) }),
    /* @__PURE__ */ jsxs("div", { className: "mt-8 border border-hair bg-panel", children: [
      /* @__PURE__ */ jsxs("div", { className: "flex items-center gap-3 px-4 py-3", children: [
        /* @__PURE__ */ jsx("span", { className: "font-mono text-[13px] text-gold", children: "\u203A" }),
        /* @__PURE__ */ jsx(
          "input",
          {
            value: line,
            onChange: (e) => setLine(e.target.value),
            onKeyDown: (e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addLine();
              }
            },
            spellCheck: false,
            placeholder: "what replaced Section 420 IPC?",
            className: "min-w-0 flex-1 bg-transparent font-mono text-[13px] text-paper outline-none placeholder:text-muted/70"
          }
        ),
        /* @__PURE__ */ jsx(
          "button",
          {
            onClick: addLine,
            className: "shrink-0 border border-hair px-2.5 py-1 font-mono text-[10.5px] text-silver transition-colors hover:border-gold hover:text-gold",
            children: "add"
          }
        )
      ] }),
      open && /* @__PURE__ */ jsx(
        "textarea",
        {
          value: paste,
          onChange: (e) => setPaste(e.target.value),
          spellCheck: false,
          placeholder: "one question per line\u2026",
          className: "h-[168px] w-full resize-none border-t border-hair bg-cream/40 px-4 py-3 font-mono text-[12.5px] leading-[1.85] text-paper outline-none placeholder:text-muted/60"
        }
      ),
      /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-hair px-4 py-2.5", children: [
        /* @__PURE__ */ jsxs("span", { className: "font-mono text-[11px] text-muted", children: [
          /* @__PURE__ */ jsx("span", { className: cn(count > MAX ? "text-error" : "text-gold"), children: Math.min(count, MAX) }),
          " / ",
          MAX,
          count > MAX && /* @__PURE__ */ jsxs("span", { className: "ml-2 text-error/80", children: [
            count - MAX,
            " beyond the cap"
          ] })
        ] }),
        /* @__PURE__ */ jsx(
          "button",
          {
            onClick: () => {
              setOpen((v) => !v);
              if (!open && !paste) setPaste(SAMPLE_BATCH);
            },
            className: "font-mono text-[11px] text-muted underline-offset-4 transition-colors hover:text-gold hover:underline",
            children: open ? "hide the list" : "paste a list instead"
          }
        ),
        /* @__PURE__ */ jsx(
          "button",
          {
            onClick: () => {
              setRows([]);
              setPaste("");
              setLine("");
              setOpen(false);
              setRunning(false);
              setElapsed(0);
            },
            className: "font-mono text-[11px] text-muted transition-colors hover:text-silver",
            children: "clear"
          }
        ),
        /* @__PURE__ */ jsx(Btn, { onClick: running ? () => setRunning(false) : start, className: "ml-auto px-4 py-2", children: running ? /* @__PURE__ */ jsxs(Fragment, { children: [
          /* @__PURE__ */ jsx(Square, { className: "h-3 w-3 fill-current" }),
          " stop"
        ] }) : /* @__PURE__ */ jsxs(Fragment, { children: [
          /* @__PURE__ */ jsx(Play, { className: "h-3 w-3 fill-current" }),
          " run"
        ] }) })
      ] })
    ] }),
    /* @__PURE__ */ jsxs("ol", { className: "divide-y divide-hair border-x border-b border-hair", children: [
      rows.length === 0 && /* @__PURE__ */ jsxs("li", { className: "px-4 py-12 text-center", children: [
        /* @__PURE__ */ jsx("p", { className: "font-display text-[22px] italic text-silver/55", children: "Nothing queued." }),
        /* @__PURE__ */ jsx("p", { className: "mx-auto mt-2 max-w-[38ch] text-[12.5px] leading-relaxed text-muted", children: "Add a question above, or paste a list \u2014 a matter index, a proof affidavit, whatever the desk is holding." })
      ] }),
      rows.map((r) => {
        const t = r.hits[0];
        return /* @__PURE__ */ jsxs(
          "li",
          {
            className: cn(
              "flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-3.5 transition-colors duration-200",
              r.status === "resolving" ? "bg-gold/[0.05]" : "hover:bg-panel/50"
            ),
            children: [
              /* @__PURE__ */ jsx("span", { className: "w-6 shrink-0 font-mono text-[10.5px] text-muted", children: String(r.id).padStart(2, "0") }),
              /* @__PURE__ */ jsx("span", { className: "min-w-[200px] flex-1 text-[13.5px] leading-snug text-paper/90", children: r.text }),
              /* @__PURE__ */ jsxs("span", { className: "flex shrink-0 items-center gap-2", children: [
                /* @__PURE__ */ jsx("span", { className: cn("h-1 w-1", dot(r)) }),
                /* @__PURE__ */ jsxs(
                  "span",
                  {
                    className: cn(
                      "font-mono text-[10.5px]",
                      r.status === "resolved" ? "text-success/80" : r.status === "unresolved" ? "text-warning/85" : "text-muted"
                    ),
                    children: [
                      r.status === "queued" ? "\u2014 \u2014 \u2014" : r.status === "resolving" ? "resolving" : r.status,
                      r.dupOf ? ` \xB7 of ${String(r.dupOf).padStart(2, "0")}` : ""
                    ]
                  }
                )
              ] }),
              /* @__PURE__ */ jsx("span", { className: "w-full shrink-0 font-mono text-[11.5px] sm:w-[268px] sm:text-right", children: t ? /* @__PURE__ */ jsxs("span", { className: "text-gold-light", children: [
                t.section.code,
                " ",
                /^article/i.test(t.section.section) ? t.section.section : `s. ${t.section.section}`,
                /* @__PURE__ */ jsx("span", { className: "ml-2 text-muted", children: t.section.status.toLowerCase() })
              ] }) : r.status === "unresolved" ? /* @__PURE__ */ jsx("span", { className: "text-warning/70", children: "no unit \u2014 name the act" }) : null })
            ]
          },
          r.id
        );
      })
    ] }),
    /* @__PURE__ */ jsxs("div", { className: "flex flex-wrap items-center gap-x-8 gap-y-3 border-x border-b border-hair px-4 py-3", children: [
      /* @__PURE__ */ jsxs("span", { className: "font-mono text-[11px] text-muted", children: [
        /* @__PURE__ */ jsx("span", { className: "text-success/85", children: stats.resolved }),
        " resolved",
        /* @__PURE__ */ jsx("span", { className: "mx-2 text-slate-custom", children: "\xB7" }),
        /* @__PURE__ */ jsx("span", { className: "text-warning/85", children: stats.unresolved }),
        " unresolved",
        /* @__PURE__ */ jsx("span", { className: "mx-2 text-slate-custom", children: "\xB7" }),
        stats.dups,
        " de-duped",
        /* @__PURE__ */ jsx("span", { className: "mx-2 text-slate-custom", children: "\xB7" }),
        (elapsed / 1e3).toFixed(2),
        "s"
      ] }),
      /* @__PURE__ */ jsxs("span", { className: "ml-auto flex items-center gap-4", children: [
        /* @__PURE__ */ jsxs(
          "button",
          {
            onClick: export_csv,
            disabled: !done,
            className: "flex items-center gap-1.5 font-mono text-[11px] text-muted transition-colors hover:text-gold disabled:opacity-35",
            children: [
              /* @__PURE__ */ jsx(Download, { className: "h-3 w-3", strokeWidth: 1.8 }),
              " CSV"
            ]
          }
        ),
        /* @__PURE__ */ jsxs(
          "button",
          {
            onClick: () => copy(annexure, "annex"),
            disabled: !stats.resolved,
            className: "flex items-center gap-1.5 font-mono text-[11px] text-muted transition-colors hover:text-gold disabled:opacity-35",
            children: [
              copied === "annex" ? /* @__PURE__ */ jsx(Check, { className: "h-3 w-3 text-success" }) : /* @__PURE__ */ jsx(Copy, { className: "h-3 w-3", strokeWidth: 1.8 }),
              "citation annexure"
            ]
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ jsxs("p", { className: "mt-4 max-w-[70ch] font-mono text-[10.5px] leading-[1.7] text-muted", children: [
      "Demonstration runner \xB7 resolves against the ",
      CORPUS.length,
      "-unit extract on this page, by the same parse \u2192 statutory identity \u2192 unit sequence the hosted index runs over ",
      TOTAL_ACTS,
      " statutes."
    ] })
  ] }) });
}
export {
  BatchSection
};
