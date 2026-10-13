/**
 * A JavaScript port of the section scanner and the part planner.
 *
 * This is not a re-imagining. It follows, step for step, the two Python files
 * the index is actually built with:
 *
 *   backend/ingest_v2/v2_scanner.py     fref_strip / num_parts / is_struct_line
 *   backend/ingest_v2/step4_segment.py  _plan_parts (the cut rules and the DP)
 *
 * It runs in the browser so a visitor can watch the grammar decide, on text
 * they supply, what the pipeline decided once at ingest time.
 */

import { SECTION_HEAD, ANCHOR_KINDS, CUT_RULES, NOISE } from "./scannerSource.js";

const RESTATED_RE = SECTION_HEAD[0].js; // v2_scanner.py:27
const QUOTE_NUM_RE = SECTION_HEAD[1].js; // v2_scanner.py:28
const PROTECTED_RE = ANCHOR_KINDS[0].js; // v2_scanner.py:36
const SPLIT_LINE_RE = ANCHOR_KINDS[1].js; // v2_scanner.py:37
const SCHEDULE_HDR_RE = ANCHOR_KINDS[2].js; // v2_scanner.py:64
const FOOTNOTE_CITE_RE = ANCHOR_KINDS[3].js; // v2_scanner.py:49
const AMEND_CITE_RE = ANCHOR_KINDS[4].js; // v2_scanner.py:56
const SELF_BODY_RE = ANCHOR_KINDS[5].js; // v2_scanner.py:70

const SUBL_RE = CUT_RULES.sub.js; // step4_segment.py:35
const ORD_RE = CUT_RULES.ord.js; // step4_segment.py:39
const BLOCK_START_RE = CUT_RULES.block.js; // step4_segment.py:40
const MAX_CHARS = CUT_RULES.maxChars.value; // step4_segment.py:34

const PAGENUM_LINE_RE = NOISE[2].js; // step6_validate.py:35
const SEP_LINE_RE = NOISE[3].js; // step6_validate.py:36
const FREF_RE = NOISE[5].js; // v2_scanner.py:21

const CHAP_HEAD_RE =
  /^\s*(?:CHAPTER)\s+(?:[IVXLCDM]){1,8}[A-Z]?(?=\s*$|\s*[-.:]|\s*\[|\s+(?![a-z]))/i;

/* ------------------------------------------------------------------ *
 * v2_scanner.py fref_strip — applied until the line stops changing
 * ------------------------------------------------------------------ */
export function frefStrip(s) {
  let prev = null;
  let out = s;
  while (prev !== out) {
    prev = out;
    out = out.replace(FREF_RE, "");
  }
  return out;
}

/* ------------------------------------------------------------------ *
 * v2_scanner.py num_parts — a real restated signature, or nothing
 * ------------------------------------------------------------------ */
export function numParts(line) {
  const t = frefStrip(line.replace(/^\s+/, ""));
  let m = RESTATED_RE.exec(t);
  if (m && t.slice(m.index + m[0].length).trim()) {
    return { number: m[1], rest: t.slice(m.index + m[0].length), via: "RESTATED_RE" };
  }
  m = QUOTE_NUM_RE.exec(t);
  if (m && t.slice(m.index + m[0].length).trim()) {
    return { number: m[1], rest: t.slice(m.index + m[0].length), via: "QUOTE_NUM_RE" };
  }
  return null;
}

function isStructLine(t) {
  if (CHAP_HEAD_RE.test(frefStrip(t).replace(/^\[/, ""))) return "chapter";
  if (SCHEDULE_HDR_RE.test(t.trim())) return "schedule";
  return null;
}

function isNoise(t) {
  if (FOOTNOTE_CITE_RE.test(t)) return "footnote-cite";
  if (AMEND_CITE_RE.test(t)) return "amendment-cite";
  if (PAGENUM_LINE_RE.test(t)) return "page-number";
  if (SEP_LINE_RE.test(t)) return "separator";
  return null;
}

function anchorKindOf(t) {
  if (!PROTECTED_RE.test(t)) return null;
  if (/^\s*Exception/i.test(t)) return "exception";
  if (/^\s*Explanation/i.test(t)) return "explanation";
  if (/^\s*Illustration/i.test(t)) return "illustration";
  return "proviso"; // "Provided that ..."
}

/** Split the marginal note from the body on a head line. */
function splitHead(rest) {
  const dash = rest.search(/[—–]/);
  if (dash >= 0 && dash < 160) {
    return { marginal: rest.slice(0, dash).replace(/[.—–-]+$/, "").trim(), bodyStart: dash };
  }
  if (SELF_BODY_RE.test(rest)) {
    const m = /\.\s{2,}/.exec(rest);
    return { marginal: rest.slice(0, m.index).trim(), bodyStart: m.index + m[0].length };
  }
  return { marginal: rest.trim(), bodyStart: rest.length };
}

/* ------------------------------------------------------------------ *
 * scanUnits — one unit per section, closed only by the next head
 * ------------------------------------------------------------------ */
export function scanUnits(text) {
  const lines = text.split("\n");
  const units = [];
  const structural = [];
  const dropped = [];
  let cursor = 0; // char offset into `text`
  let cur = null;

  const closeCur = () => {
    if (!cur) return;
    cur.end = cursor;
    cur.chars = Math.max(0, cur.end - cur.start);
    units.push(cur);
    cur = null;
  };

  for (const raw of lines) {
    const start = cursor;
    const end = start + raw.length;
    cursor = end + 1; // account for the newline

    const trimmed = raw.trim();
    if (!trimmed) continue;

    const noise = isNoise(raw);
    if (noise) {
      dropped.push({ kind: noise, text: raw, start, end });
      continue;
    }

    const struct = isStructLine(raw);
    if (struct) {
      structural.push({ kind: struct, text: raw, start, end });
      continue;
    }

    const head = numParts(raw);
    if (head) {
      closeCur();
      const { marginal, bodyStart } = splitHead(head.rest);
      cur = {
        index: units.length,
        number: head.number,
        via: head.via,
        marginal,
        lines: [{ text: raw, start, end, kind: "head" }],
        start,
        end,
        anchors: { proviso: 0, exception: 0, explanation: 0, illustration: 0, clause: 0 },
        bodyStartOffset: start + (raw.length - head.rest.length) + bodyStart,
      };
      const ak = anchorKindOf(frefStrip(raw));
      if (ak && bodyStart < head.rest.length) cur.anchors[ak] += 1;
      continue;
    }

    if (!cur) {
      // matter before the first section head: running heads, the extent note
      dropped.push({ kind: "prefatory", text: raw, start, end });
      continue;
    }

    const stripped = frefStrip(raw);
    let kind = "body";
    const ak = anchorKindOf(stripped);
    if (ak) {
      kind = ak;
      cur.anchors[ak] += 1;
    } else if (SPLIT_LINE_RE.test(stripped)) {
      kind = "clause";
      cur.anchors.clause += 1;
    }
    cur.lines.push({ text: raw, start, end, kind });
  }
  closeCur();

  return {
    units,
    structural,
    dropped,
    covered: units.reduce((n, u) => n + u.chars, 0),
    total: text.length,
    residual: Math.max(0, text.length - units.reduce((n, u) => n + u.chars, 0)),
  };
}

export function anchorTotals(units) {
  return units.reduce(
    (a, u) => ({
      proviso: a.proviso + u.anchors.proviso,
      exception: a.exception + u.anchors.exception,
      explanation: a.explanation + u.anchors.explanation,
      illustration: a.illustration + u.anchors.illustration,
      clause: a.clause + u.anchors.clause,
    }),
    { proviso: 0, exception: 0, explanation: 0, illustration: 0, clause: 0 },
  );
}

/* ------------------------------------------------------------------ *
 * step4_segment.py _plan_parts — where a unit may be cut
 * ------------------------------------------------------------------ */

/** Join cost between consecutive kept lines: 0 for a hyphen merge, 1 for a newline. */
function pairCosts(lines) {
  const out = [];
  for (let i = 0; i < lines.length - 1; i += 1) {
    const a = lines[i].text;
    const b = lines[i + 1].text;
    if (/[A-Za-z0-9]-$/.test(a) && /^[a-z]/.test(b)) out.push(0);
    else out.push(1);
  }
  return out;
}

/**
 * Mirror of step4_segment.py `_plan_parts`.
 * Returns { slices, cuts, longUnsplit } — slices are [from, to) line ranges.
 */
export function planParts(unitLines) {
  const m = unitLines.length;
  const pair = pairCosts(unitLines);
  const pref = [0];
  for (let t = 1; t <= m; t += 1) {
    let add = unitLines[t - 1].text.length;
    if (t >= 2) add += pair[t - 2];
    pref[t] = pref[t - 1] + add;
  }

  const balBefore = [0];
  for (let i = 0; i < m; i += 1) {
    const t = unitLines[i].text;
    balBefore[i + 1] =
      balBefore[i] +
      (t.match(/\(|\[/g) || []).length -
      (t.match(/\)|\]/g) || []).length;
  }

  let firstBlock = null;
  const cuts = [];
  for (let p = 1; p < m; p += 1) {
    const st = frefStrip(unitLines[p].text).replace(/^\s+/, "");
    if (BLOCK_START_RE.test(st) && firstBlock === null) firstBlock = p;
    if (!(SUBL_RE.test(st) || ORD_RE.test(st))) continue;
    if (balBefore[p] !== 0) continue;
    if (firstBlock !== null && firstBlock < p) continue;
    cuts.push(p);
  }

  const INF = Infinity;
  const dp = new Array(m + 1).fill(INF);
  const prev = new Array(m + 1).fill(-1);
  dp[0] = 0;
  const stops = [0, ...cuts];
  for (let j = 1; j <= m; j += 1) {
    for (const k of stops) {
      if (k >= j || dp[k] === INF) continue;
      if (pref[j] - pref[k] <= MAX_CHARS && dp[k] + 1 < dp[j]) {
        dp[j] = dp[k] + 1;
        prev[j] = k;
      }
    }
  }

  if (dp[m] === INF) {
    return { slices: [[0, m]], cuts, longUnsplit: pref[m], parts: 1 };
  }

  const bounds = [];
  for (let j = m; j > 0; j = prev[j]) bounds.push(j);
  bounds.push(0);
  bounds.reverse();
  const slices = [];
  for (let i = 0; i < bounds.length - 1; i += 1) slices.push([bounds[i], bounds[i + 1]]);
  const used = new Set(bounds.slice(1, -1));
  return { slices, cuts: cuts.filter((p) => used.has(p)), longUnsplit: null, parts: slices.length };
}

/* ------------------------------------------------------------------ *
 * the baseline every other stack runs: fixed windows with overlap
 * ------------------------------------------------------------------ */
export function fixedWindows(text, size, overlap) {
  const out = [];
  const step = Math.max(1, size - overlap);
  for (let i = 0, n = 0; i < text.length; i += step, n += 1) {
    const slice = text.slice(i, i + size);
    if (!slice.trim()) {
      if (i + size >= text.length) break;
      continue;
    }
    const opensAtAnchor = /^\s{0,8}(?:\d{1,4}[A-Za-z]{0,2}\.)/.test(slice);
    const endsMidSentence = !/[.:;’”"]\s*$/.test(slice.trimEnd()) && i + size < text.length;
    const lost = [];
    if (PROTECTED_RE.test(slice.replace(/^\s*/, "  "))) lost.push("carve-out detached from the rule it qualifies");
    if (/^\s*[—–-]\s*\(/.test(slice)) lost.push("clause list severed from its opening words");
    if (endsMidSentence) lost.push("sentence severed at the window edge");
    out.push({
      index: n,
      text: slice,
      start: i,
      end: Math.min(text.length, i + size),
      orphaned: !opensAtAnchor,
      midSentence: endsMidSentence,
      lostAnchors: lost,
    });
    if (i + size >= text.length) break;
  }
  return out;
}

/** Does a fixed window land on top of a real section boundary? */
export function boundaryOffsets(units) {
  return units.map((u) => u.start);
}
