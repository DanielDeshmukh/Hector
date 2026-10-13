"use client";

/**
 * Landing-page access to the live index.
 *
 * Search and compare reuse the app's own wrapper so the landing page and the
 * product hit the same endpoint with the same key. The only new call is
 * /readyz, which is unauthenticated and is what supplies the one live figure
 * shown on this page.
 */

import { searchHector, compareHector } from "@/api/hectorApi";

export { searchHector, compareHector };

export const API_URL =
  process.env.NEXT_PUBLIC_HECTOR_API_URL || process.env.VITE_HECTOR_API_URL || "/api";

/** Live record count. Never fabricates a fallback — null means unavailable. */
export async function fetchIndexRecords(signal) {
  const res = await fetch(`${API_URL}/readyz`, { signal, cache: "no-store" });
  if (!res.ok) throw new Error(`readyz ${res.status}`);
  const data = await res.json();
  const rec = data?.checks?.pinecone?.records;
  return typeof rec === "number" ? rec : null;
}

/** Serialised so a batch does not trip the per-minute limit. */
export async function runSearchSeries(queries, { signal, onEach, concurrency = 1 } = {}) {
  const out = [];
  for (let i = 0; i < queries.length; i += concurrency) {
    if (signal?.aborted) break;
    const slice = queries.slice(i, i + concurrency);
    const settled = await Promise.allSettled(
      slice.map((q) => searchHector(q)),
    );
    settled.forEach((r, j) => {
      const idx = i + j;
      const row =
        r.status === "fulfilled"
          ? { ok: true, data: r.value }
          : { ok: false, error: r.reason?.message || "unresolved" };
      out[idx] = row;
      onEach?.(idx, row);
    });
  }
  return out;
}
