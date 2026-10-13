"use client";

import { useEffect, useRef, useState } from "react";
import { fetchIndexRecords } from "./api.js";

/** Scroll reveal: fires once, honours prefers-reduced-motion. */
export function useReveal(threshold = 0.18) {
  const ref = useRef(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    if (typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches) {
      setShown(true);
      return undefined;
    }
    if (typeof IntersectionObserver === "undefined") {
      setShown(true);
      return undefined;
    }
    let raf = 0;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            cancelAnimationFrame(raf);
            raf = requestAnimationFrame(() => setShown(true));
            io.unobserve(e.target);
          }
        });
      },
      { threshold, rootMargin: "0px 0px -8% 0px" },
    );
    io.observe(el);
    return () => {
      io.disconnect();
      cancelAnimationFrame(raf);
    };
  }, [threshold]);

  return { ref, shown };
}

export function useCopy(timeout = 1600) {
  const [copied, setCopied] = useState(null);
  const copy = async (text, key = "default") => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
      } catch {
        /* clipboard unavailable */
      }
      document.body.removeChild(ta);
    }
    setCopied(key);
    window.setTimeout(() => setCopied((c) => (c === key ? null : c)), timeout);
  };
  return { copied, copy };
}

export function useScrollProgress() {
  const [p, setP] = useState(0);
  useEffect(() => {
    const onScroll = () => {
      const h = document.documentElement;
      const max = h.scrollHeight - h.clientHeight;
      setP(max > 0 ? h.scrollTop / max : 0);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);
  return p;
}

export function useActiveSection(ids) {
  const [active, setActive] = useState(ids[0] ?? "");
  const key = ids.join("|");
  useEffect(() => {
    if (typeof document === "undefined" || typeof IntersectionObserver === "undefined") return undefined;
    const list = key.split("|");
    const els = list.map((id) => document.getElementById(id)).filter(Boolean);
    if (!els.length) return undefined;
    const io = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setActive(visible.target.id);
      },
      { threshold: [0.12, 0.4], rootMargin: "-18% 0px -55% 0px" },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [key]);
  return active;
}

/** Live index size, fetched from the unauthenticated /readyz probe.
 *  Returns null until loaded and never invents a fallback figure. */
export function useIndexRecords() {
  const [state, setState] = useState({ records: null, loading: true, failed: false });
  useEffect(() => {
    let cancelled = false;
    const ctrl = new AbortController();
    const timer = window.setTimeout(() => ctrl.abort(), 8000);
    (async () => {
      try {
        const rec = await fetchIndexRecords(ctrl.signal);
        if (!cancelled) setState({ records: rec, loading: false, failed: rec === null });
      } catch {
        if (!cancelled) setState({ records: null, loading: false, failed: true });
      } finally {
        window.clearTimeout(timer);
      }
    })();
    return () => {
      cancelled = true;
      ctrl.abort();
      window.clearTimeout(timer);
    };
  }, []);
  return state;
}
