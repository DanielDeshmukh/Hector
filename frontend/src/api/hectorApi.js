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

function getMetadataValue(metadata, keys, fallback = "") {
  for (const key of keys) {
    if (metadata?.[key] !== undefined && metadata?.[key] !== null && metadata?.[key] !== "") {
      return metadata[key];
    }
  }
  return fallback;
}

function toSourceReference(item, index) {
  const citation = item.citation || {};
  const metadata = item.metadata || {};
  const score = Number(item.score || 0);
  const similarityScore = Number(item.similarity_score ?? item.score ?? 0);
  const relevanceScore = similarityScore > 1 ? similarityScore / 100 : similarityScore;
  const snippet = item.snippet || "";
  const document = item.document || snippet;
  const page = Number(
    getMetadataValue(metadata, ["page", "page_number"], getCitationValue(citation, "page", 0))
  );
  const paragraph = Number(
    getMetadataValue(metadata, ["paragraph", "para"], getCitationValue(citation, "paragraph", index + 1))
  );

  return {
    id: item.id || `source-${index + 1}`,
    bookTitle:
      getMetadataValue(metadata, ["source", "book_title", "title", "filename"]) ||
      getCitationValue(citation, "book") ||
      getCitationValue(citation, "source") ||
      "Retrieved Legal Source",
    author: getMetadataValue(metadata, ["author", "publisher"]) || getCitationValue(citation, "author") || "HECTOR corpus",
    chapter: getMetadataValue(metadata, ["chapter", "chapter_title"]) || getCitationValue(citation, "chapter") || "Retrieved context",
    section:
      getMetadataValue(metadata, ["section_number", "section", "section_title"]) ||
      getCitationValue(citation, "section") ||
      getCitationValue(citation, "provision") ||
      "Relevant provision",
    page: Number.isFinite(page) ? page : null,
    paragraph: Number.isFinite(paragraph) ? paragraph : null,
    relevanceScore,
    matchedText: snippet,
    fullText: document,
    act: item.act || getMetadataValue(metadata, ["act_name", "act"]) || getCitationValue(citation, "act") || "Legal corpus",
    highlightRanges: document ? [{ start: 0, end: Math.min(document.length, 180) }] : [],
    citation,
    metadata,
    reasons: item.reasons || [],
    rawScore: score,
    similarityScore,
    rerankerScore: Number(item.reranker_score ?? similarityScore),
    hybridScore: Number(item.hybrid_score ?? 0),
    retrievalScore: Number(item.retrieval_score ?? 0),
    boostScore: Number(item.boost_score ?? 0),
    semanticScore: Number(item.semantic_score ?? 0),
    bm25Score: Number(item.bm25_score ?? 0),
    raw: item,
  };
}

function confidenceFromItems(items) {
  if (!items?.length) return 0;
  const bestScore = Number(items[0].similarity_score ?? items[0].score ?? 0);
  return Math.round((bestScore > 1 ? bestScore : bestScore * 100) * 10) / 10;
}

function confidenceFromPayload(payload) {
  const answerConfidence = Number(payload.answer_confidence ?? 0);
  if (answerConfidence > 0) return Math.round(answerConfidence * 10) / 10;
  return confidenceFromItems(payload.items);
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
    confidence: confidenceFromPayload(payload),
    answerSections: payload.answer_sections || [],
    sourceSections: payload.source_sections || [],
    citations: payload.citations || [],
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
