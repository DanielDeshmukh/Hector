const API_URL = "/api";
const API_KEY = "";

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
      getMetadataValue(metadata, ["real_act_name", "act_name", "source", "book_title", "title", "filename"]) ||
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
    act: item.act || getMetadataValue(metadata, ["real_act_name", "act_name", "act"]) || getCitationValue(citation, "act") || "Legal corpus",
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
  if (payload.answer_confidence !== undefined && payload.answer_confidence !== null) {
    return Math.round(payload.answer_confidence * 10) / 10;
  }
  const items = payload.items || [];
  if (!items.length) return 0;
  const firstScore = Number(items[0].similarity_score ?? items[0].score ?? 0);
  return Math.round((firstScore > 1 ? firstScore : firstScore * 100) * 10) / 10;
}

function buildPipelineFromPayload(payload) {
  const t = payload.stage_timings || {};
  const stages = [
    {
      id: "stage-1",
      name: "Intent Routing",
      status: payload.route ? "completed" : "pending",
      detail: payload.route
        ? `Routed as: ${payload.route.replace(/_/g, " ")}${t.route_ms ? ` (${Math.round(t.route_ms)}ms)` : ""}`
        : "Awaiting routing...",
      timing: t.route_ms || null,
    },
    {
      id: "stage-2",
      name: "Hybrid Retrieval",
      status: (payload.items?.length > 0) ? "completed" : "pending",
      detail: payload.items?.length
        ? `${payload.items.length} results retrieved${t.retrieve_ms ? ` (${Math.round(t.retrieve_ms)}ms)` : ""}`
        : "Awaiting retrieval...",
      timing: t.retrieve_ms || null,
    },
    {
      id: "stage-3",
      name: "Hierarchical Context",
      status: (payload.answer_sections?.length > 0 || payload.source_sections?.length > 0) ? "completed" : "pending",
      detail: payload.source_sections?.length
        ? `${payload.source_sections.length} source sections resolved`
        : "Awaiting context...",
      timing: null,
    },
    {
      id: "stage-4",
      name: "Citation Grounding",
      status: payload.verification_enabled ? "completed" : "pending",
      detail: payload.verification_enabled
        ? "Citations verified"
        : "Awaiting verification...",
      timing: t.generate_ms || null,
    },
  ];
  return stages;
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
    confidenceLevel: payload.confidence_level || "unknown",
    confidenceWarning: payload.confidence_warning || null,
    hallucinationCheck: payload.hallucination_check || null,
    answerSections: payload.answer_sections || [],
    sourceSections: payload.source_sections || [],
    citations: payload.citations || [],
    relatedProvisions: payload.related_provisions || [],
    normalizedQuery: payload.normalized_query || null,
    sources,
    pipeline: buildPipelineFromPayload(payload),
    stageTimings: payload.stage_timings || null,
    timestamp: payload.retrieved_at || new Date().toISOString(),
    raw: payload,
  };
}

function authHeaders() {
  return {
    "Content-Type": "application/json",
  };
}

export async function searchHector(query) {
  const response = await fetch(`${API_URL}/search`, {
    method: "POST",
    headers: authHeaders(),
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

export async function compareHector(section, act = "IPC") {
  const response = await fetch(`${API_URL}/compare`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ section, act, page_size: 3 }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HECTOR compare failed with status ${response.status}`);
  }

  const data = await response.json();
  return {
    requestedAct: data.requested_act,
    requestedSection: data.requested_section,
    counterpartAct: data.counterpart_act,
    counterpartSection: data.counterpart_section,
    note: data.note,
    requestedResults: (data.requested_results || []).map(toSourceReference),
    counterpartResults: (data.counterpart_results || []).map(toSourceReference),
    comparedAt: data.compared_at,
  };
}

export async function routeHector(query) {
  const response = await fetch(`${API_URL}/route`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HECTOR route failed with status ${response.status}`);
  }

  const data = await response.json();
  return {
    route: data.route,
    confidence: data.confidence,
    response: data.hector_response,
    normalizedQuery: data.normalized_query,
    mappings: data.mappings,
  };
}

export async function getStatusHector() {
  const response = await fetch(`${API_URL}/status`, {
    method: "GET",
    headers: authHeaders(),
  });

  if (!response.ok) {
    throw new Error(`HECTOR status failed with status ${response.status}`);
  }

  return await response.json();
}

export function createSearchWebSocket(query, onEvent, onError, _retries = 0, _maxRetries = 3) {
  const wsUrl = API_URL.replace(/^http/, "ws") + `/ws/search?api_key=${API_KEY}`;
  const ws = new WebSocket(wsUrl);
  let retries = _retries;
  const maxRetries = _maxRetries;

  ws.onopen = () => {
    ws.send(JSON.stringify({
      query,
      page: 1,
      page_size: 5,
      verify: true,
      format: "summary",
      include_related: true,
    }));
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent(data);
    } catch (e) {
      console.error("WebSocket parse error:", e);
    }
  };

  ws.onerror = (error) => {
    if (onError) onError(error);
  };

  ws.onclose = (event) => {
    if (event.code === 1000 || event.code === 1001) return;
    if (retries >= maxRetries) {
      if (onError) onError(new Error(`WebSocket closed after ${maxRetries} retries`));
      return;
    }
    retries++;
    const delay = Math.min(1000 * Math.pow(2, retries - 1), 10000);
    setTimeout(() => {
      createSearchWebSocket(query, onEvent, onError, authHeaders, retries, maxRetries);
    }, delay);
  };

  return ws;
}
