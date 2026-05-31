const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY || "hector-dev-key";

const completedPipeline = [
  {
    id: "stage-1",
    name: "Intent Routing",
    status: "completed",
    detail: "Query routed by HECTOR backend.",
  },
  {
    id: "stage-2",
    name: "Hybrid Retrieval",
    status: "completed",
    detail: "Semantic and keyword retrieval completed.",
  },
  {
    id: "stage-3",
    name: "Hierarchical Context",
    status: "completed",
    detail: "Retrieved legal context prepared for display.",
  },
  {
    id: "stage-4",
    name: "Citation Grounding",
    status: "completed",
    detail: "Response returned with source material.",
  },
];

function getCitationValue(citation, key, fallback = "") {
  return citation?.[key] ?? citation?.[key.toLowerCase()] ?? fallback;
}

function toSourceReference(item, index) {
  const citation = item.citation || {};
  const metadata = item.metadata || {};
  const score = Number(item.score || 0);
  const relevanceScore = score > 1 ? score / 100 : score;
  const snippet = item.snippet || "";

  return {
    id: item.id || `source-${index + 1}`,
    bookTitle:
      metadata.book_title ||
      metadata.title ||
      getCitationValue(citation, "book") ||
      getCitationValue(citation, "source") ||
      "Retrieved Legal Source",
    author: metadata.author || getCitationValue(citation, "author") || "HECTOR corpus",
    chapter: metadata.chapter || getCitationValue(citation, "chapter") || "Retrieved context",
    section:
      metadata.section ||
      getCitationValue(citation, "section") ||
      getCitationValue(citation, "provision") ||
      "Relevant provision",
    page: Number(metadata.page || getCitationValue(citation, "page", 0)) || 0,
    paragraph: Number(metadata.paragraph || getCitationValue(citation, "paragraph", index + 1)) || index + 1,
    relevanceScore,
    matchedText: snippet,
    fullText: snippet,
    act: item.act || metadata.act || getCitationValue(citation, "act") || "Legal corpus",
    highlightRanges: snippet ? [{ start: 0, end: Math.min(snippet.length, 180) }] : [],
  };
}

function confidenceFromItems(items) {
  if (!items?.length) return 0;
  const bestScore = Number(items[0].score || 0);
  return Math.round((bestScore > 1 ? bestScore : bestScore * 100) * 10) / 10;
}

function toUiResponse(payload) {
  const sources = (payload.items || []).map(toSourceReference);

  return {
    id: `${payload.route || "search"}-${payload.retrieved_at || Date.now()}`,
    query: payload.query,
    answer:
      payload.generated_response ||
      "HECTOR returned source matches, but no generated response was available for this query.",
    domain: payload.route || "Search",
    confidence: confidenceFromItems(payload.items),
    sources,
    pipeline: completedPipeline,
    timestamp: payload.retrieved_at || new Date().toISOString(),
    raw: payload,
  };
}

export async function searchHector(query) {
  const response = await fetch(`${API_URL}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
    },
    body: JSON.stringify({
      query,
      page: 1,
      page_size: 5,
      verify: true,
      format: "summary",
      include_related: true,
    }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HECTOR search failed with status ${response.status}`);
  }

  return toUiResponse(await response.json());
}
