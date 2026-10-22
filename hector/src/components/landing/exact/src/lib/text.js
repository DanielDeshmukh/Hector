import { CORPUS } from "../data/corpus";
function partToText(p) {
  switch (p.kind) {
    case "section":
      return p.text.trim();
    case "clause": {
      const l = (p.label ?? "").trim();
      if (/^\([a-zA-Z0-9]+\)$/.test(l)) return `
	${l} ${p.text.trim()}`;
      return `
	\u2014${l ? `${l},` : ""} ${p.text.trim()}`;
    }
    case "exception":
      return `
	${p.label ?? "Exception"}.\u2014${p.text.trim()}`;
    case "illustration":
      return `
	${p.label ?? "Illustration"}.\u2014${p.text.trim()}`;
    case "explanation":
      return `
	${p.label ?? "Explanation"}.\u2014${p.text.trim()}`;
    case "proviso": {
      const t = p.text.trim();
      if (/^provided\b/i.test(t)) return `
	${t}`;
      return `
	Provided that ${t.charAt(0).toLowerCase()}${t.slice(1)}`;
    }
    default:
      return p.text.trim();
  }
}
function canon(s) {
  const isArticle = /^article/i.test(s.section);
  const head = isArticle ? `${s.section}. ${s.note}.\u2014` : `${s.section}. ${s.note}.\u2014`;
  const body = s.parts.map((p) => p.kind === "section" ? p.text.trim() : partToText(p)).join("");
  return `${head}${body}`;
}
const canonById = (id) => {
  const s = CORPUS.find((x) => x.id === id);
  return s ? canon(s) : "";
};
const BOUNDARY_SOURCE = String.raw`(?:^|\n)(?:[Ss]ection|[Ss]ec\.?|s\.)\s*(\d{1,4}[A-Z]?)\.?\s+|(?:^|\n)(\d{1,4}[A-Z]?)\.\s+[^a-z\d]`;
const BOUNDARY = new RegExp(BOUNDARY_SOURCE, "gm");
const countAll = (haystack, re) => (haystack.match(re) ?? []).length;
const TITLE_CUT_RE = /\.\s*[-\u2013\u2014]|--|[\u2013\u2014]/;
function marginalOf(unit) {
  const first = unit.split("\n").find((l) => l.trim()) ?? "";
  const after = first.replace(/^\s*(?:[Ss]ection|[Ss]ec\.?|s\.)?\s*\d{1,4}[A-Z]?\.\s*/, "");
  const cut = after.search(TITLE_CUT_RE);
  return (cut >= 0 ? after.slice(0, cut) : after).trim();
}
function anchorMap(text) {
  return {
    proviso: countAll(text, /^[ \t]*Provided\s+(?:that|also|further|nevertheless)/gim),
    exception: countAll(text, /^[ \t]*Exception/gim),
    explanation: countAll(text, /^[ \t]*Explanation/gim),
    illustration: countAll(text, /^[ \t]*Illustration/gim),
    clause: countAll(text, /\([a-zA-Z0-9]+\)\s+/g)
  };
}
function regexUnits(text) {
  const out = [];
  const re = new RegExp(BOUNDARY_SOURCE, "gm");
  const marks = [];
  let m;
  while ((m = re.exec(text)) !== null) {
    marks.push({ at: m.index, number: (m[1] ?? m[2] ?? "").trim() });
    if (m[0].length === 0) re.lastIndex++;
  }
  for (let i = 0; i < marks.length; i++) {
    const raw = marks[i].at;
    const start = text[raw] === "\n" ? raw + 1 : raw;
    const end = i + 1 < marks.length ? marks[i + 1].at : text.length;
    const body = text.slice(start, end);
    out.push({
      index: i,
      number: marks[i].number,
      marginal: marginalOf(body),
      text: body,
      start,
      end,
      anchors: anchorMap(body)
    });
  }
  return out;
}
function fixedWindows(text, size, overlap) {
  const out = [];
  const step = Math.max(1, size - overlap);
  for (let i = 0, n = 0; i < text.length; i += step, n++) {
    const slice = text.slice(i, i + size);
    if (!slice.trim()) continue;
    const opensAtAnchor = /^[ \t]{0,8}(?:\d{1,4}[A-Za-z]?\.|[Aa]rticle\s+\d+[A-Z]*\.)/.test(slice);
    const endsMidSentence = !/[.:;\u2019\u201d"]\s*$/.test(slice.trimEnd()) && i + size < text.length;
    const lost = [];
    if (/^[ \t]*(?:Provided\b|Exception\b|Explanation\b|Illustration\b)/.test(slice))
      lost.push("carve-out detached from the rule it qualifies");
    if (/^[ \t]*[—–-]\s*\(/.test(slice)) lost.push("clause list severed from its opening words");
    if (endsMidSentence) lost.push("sentence severed at the window edge");
    if (opensAtAnchor && /—/.test(slice) && !/Provided|Exception|Explanation|Illustration/.test(slice))
      lost.push("unit opened but never closed inside the window");
    out.push({
      index: n,
      text: slice,
      start: i,
      end: Math.min(text.length, i + size),
      orphaned: !opensAtAnchor,
      midSentence: endsMidSentence,
      lostAnchors: lost
    });
    if (i + size >= text.length) break;
  }
  return out;
}
const CODE_RE = /\b(BNS|BNSS|BSA|IPC|CrPC|Cr\.P\.C|IEA|Evidence Act|CPC|ICA|Contract Act|TPA|ITA|Trusts Act|Easements? Act|NI Act|Negotiable|Limitation Act|SRA|Specific Relief|Arb(?:itration)? Act|Constitution|HMA|HMGA|HSA|DPA|FCA|PWDVA|Domestic Violence|JJ Act|Industrial Disputes|Factories Act|Motor Vehicles|MVA|Arms Act|Copyright Act|Forest Act|NDPS|Prevention of Corruption|Environment Protection|IT Act|RTI|Consumer Protection|CPA|LSAA|Gram Nyayalaya)\b/i;
const SECTION_RE = /(?:§|section\s*(?:no\.?)?\s*|s\.?\s*|sec\.?\s*)(\d{1,4}[A-Za-z]?)/i;
const ARTICLE_RE = /(?:article\s*(?:no\.?)?\s*)(\d{1,4}[A-Za-z]*)/i;
const CODE_ALIASES = {
  BNS: ["bns", "nyaya sanhita", "sanhita"],
  BNSS: ["bnss", "nagarik suraksha"],
  BSA: ["bsa", "sakshya"],
  IPC: ["ipc", "indian penal code", "penal code"],
  CrPC: ["crpc", "cr.p.c", "code of criminal procedure", "criminal procedure code"],
  IEA: ["iea", "evidence act", "indian evidence"],
  CPC: ["cpc", "code of civil procedure"],
  ICA: ["ica", "contract act"],
  Constitution: ["constitution", "const", "art"],
  NDPS: ["ndps", "narcotic"]
};
function parseQuery(raw) {
  const codeHit = raw.match(CODE_RE);
  let code = codeHit ? codeHit[1].toUpperCase().replace(/\./g, "") : null;
  if (code === "CR.P.C") code = "CRPC";
  if (code === "EVIDENCE ACT") code = "IEA";
  if (code === "CONTRACT ACT") code = "ICA";
  if (code === "TRUSTS ACT") code = "ITA";
  if (code === "SANHITA") code = "BNS";
  const num = raw.match(SECTION_RE)?.[1] ?? raw.match(ARTICLE_RE)?.[1] ?? null;
  const words = raw.toLowerCase().replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter((w) => w.length > 3 && !STOP.has(w));
  return { raw, code, number: num, words };
}
const STOP = /* @__PURE__ */ new Set([
  "the",
  "and",
  "that",
  "this",
  "with",
  "what",
  "when",
  "under",
  "section",
  "which",
  "whether",
  "does",
  "case",
  "cases",
  "file",
  "court",
  "your",
  "have",
  "from",
  "about",
  "can",
  "for",
  "are",
  "provision",
  "provide",
  "whereas",
  "shall",
  "must",
  "need",
  "into",
  "than",
  "them",
  "they"
]);
const citationOf = (s) => `${s.act}, ${/^article/i.test(s.section) ? s.section : `s. ${s.section}`}`;
function retrieve(raw, limit = 3) {
  const q = parseQuery(raw);
  const scored = CORPUS.map((s) => {
    let score = 0;
    if (q.code) {
      const aliases = CODE_ALIASES[s.code] ?? [s.code.toLowerCase()];
      if (aliases.some((a) => a === q.code.toLowerCase())) score += 60;
    }
    if (q.number) {
      const target = q.number.toUpperCase();
      if (s.section.toUpperCase() === target) score += 44;
      else if (s.section.toUpperCase().endsWith(target)) score += 30;
    }
    const hay = `${s.note} ${s.act} ${s.chapter} ${s.parts.map((p) => `${p.label ?? ""} ${p.text}`).join(" ")}`.toLowerCase();
    for (const w of q.words) {
      if (s.note.toLowerCase().includes(w)) score += 7;
      else if (hay.includes(w)) score += Math.min(4, 1.4 + w.length / 6);
    }
    const anchors = anchorMap(canon(s));
    return {
      section: s,
      score,
      chars: canon(s).length,
      anchors,
      citation: citationOf(s),
      exact: Boolean(q.code && q.number)
    };
  }).filter((h) => h.score >= 8).sort((a, b) => b.score - a.score);
  return scored.slice(0, limit);
}
function diffWords(a, b) {
  const A = a.split(/(\s+)/).filter((t) => t.length);
  const B = b.split(/(\s+)/).filter((t) => t.length);
  const n = A.length;
  const m = B.length;
  if (n * m > 4e5) {
    return [{ t: "del", text: a }, { t: "add", text: b }];
  }
  const dp = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
  for (let i2 = n - 1; i2 >= 0; i2--) {
    for (let j2 = m - 1; j2 >= 0; j2--) {
      dp[i2][j2] = A[i2] === B[j2] ? dp[i2 + 1][j2 + 1] + 1 : Math.max(dp[i2 + 1][j2], dp[i2][j2 + 1]);
    }
  }
  const out = [];
  const push = (t, text) => {
    const last = out[out.length - 1];
    if (last && last.t === t) last.text += text;
    else out.push({ t, text });
  };
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (A[i] === B[j]) {
      push("same", A[i]);
      i++;
      j++;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      push("del", A[i++]);
    } else {
      push("add", B[j++]);
    }
  }
  while (i < n) push("del", A[i++]);
  while (j < m) push("add", B[j++]);
  return out.map((op) => ({ ...op, text: op.text.replace(/\s+/g, " ").trimEnd() }));
}
function digest(input) {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h.toString(16).padStart(8, "0");
}
const pct = (n) => `${Math.round(n * 100)}%`;
function highlight(text, terms) {
  if (!terms.length) return [{ t: text, hit: false }];
  const re = new RegExp(`(${terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "gi");
  return text.split(re).filter(Boolean).map((t) => ({ t, hit: re.test(t) && terms.some((x) => x.toLowerCase() === t.toLowerCase()) }));
}
const SAMPLE_BATCH = `Is the punishment for murder identical under the new criminal law?
What is the BNS section corresponding to Section 420 IPC?
Sedition \u2014 has it been replaced under BNS?
Inherent powers of the High Court under BNSS
Maintenance claim by a parent under BNSS Section 144
Previous good character \u2014 relevant under BSA?
Bail conditions for commercial quantity under NDPS Section 37
Cognizance of suits of a civil nature \u2014 CPC Section 9
Which sections replaced CrPC 482 and CrPC 125?
Can a dying declaration convict without corroboration?`;
const SAMPLE_QUERY = "Section 302 IPC punishment for murder";
export {
  BOUNDARY,
  BOUNDARY_SOURCE,
  SAMPLE_BATCH,
  SAMPLE_QUERY,
  anchorMap,
  canon,
  canonById,
  citationOf,
  diffWords,
  digest,
  fixedWindows,
  highlight,
  parseQuery,
  partToText,
  pct,
  regexUnits,
  retrieve
};
