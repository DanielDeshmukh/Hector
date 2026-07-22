"use client";

import { useState } from "react";
import {
  Clock,
  Plus,
  ChevronLeft,
  ChevronRight,
  BookOpen,
  Gavel,
  FileText,
  Bookmark,
  BookmarkX,
  X,
} from "lucide-react";

export default function Sidebar({
  collapsed,
  onToggle,
  onNewQuery,
  onSelectHistory,
  history,
  bookmarks = [],
  onRemoveBookmark,
  systemStatus,
  mobileOpen,
  onMobileClose,
}) {
  const [hoveredItem, setHoveredItem] = useState(null);
  const [activeTab, setActiveTab] = useState("history");

  const domainIcon = (domain) => {
    switch (domain) {
      case "Criminal":
        return <Gavel size={14} />;
      case "Procedural":
        return <FileText size={14} />;
      case "LEGAL_RESEARCH":
      case "Legal Research":
        return <BookOpen size={14} />;
      default:
        return <BookOpen size={14} />;
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={`flex flex-col border-r border-slate-custom/60 bg-cream transition-all duration-300
          fixed inset-y-0 left-0 z-50 md:relative md:z-auto
          ${mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
          ${collapsed ? "w-[56px]" : "w-[280px]"}`}
        role="navigation"
        aria-label="Search history and bookmarks"
      >
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-slate-custom/40 px-3 py-4">
        {!collapsed && (
          <div className="flex items-center gap-2.5 animate-fade-in flex-1 min-w-0">
            <img src="/tab-icon.png" alt="HECTOR" className="h-8 w-8 rounded-md shrink-0" />
            <div className="min-w-0">
              <h1 className="font-serif text-lg font-semibold tracking-wide text-gold-light leading-none">
                HECTOR
              </h1>
              <p className="text-[10px] font-medium uppercase tracking-[0.15em] text-silver mt-0.5">
                Legal Intelligence
              </p>
            </div>
          </div>
        )}
        {!collapsed && onMobileClose && (
          <button
            onClick={onMobileClose}
            className="md:hidden flex h-7 w-7 items-center justify-center rounded-md text-silver/50 hover:bg-slate-custom/30 hover:text-silver shrink-0"
            aria-label="Close menu"
          >
            <X size={14} />
          </button>
        )}
        {collapsed && (
          <img src="/tab-icon.png" alt="HECTOR" className="h-8 w-8 rounded-md" />
        )}
      </div>

      {/* New Query Button */}
      <div className="px-2.5 pt-3 pb-1">
        <button
          onClick={onNewQuery}
          aria-label="Start new query"
          className={`flex w-full items-center gap-2.5 rounded-lg border border-slate-custom/60 px-3 py-2.5 text-sm text-silver transition-all hover:border-gold/40 hover:text-gold-light hover:bg-gold/5 ${
            collapsed ? "justify-center" : ""
          }`}
        >
          <Plus size={16} />
          {!collapsed && <span className="font-medium">New Query</span>}
        </button>
      </div>

      {/* History & Bookmarks */}
      {!collapsed && (
        <div className="flex-1 overflow-y-auto px-2.5 pt-4">
          <div className="mb-2 flex items-center gap-1 px-2">
            <button
              onClick={() => setActiveTab("history")}
              aria-label="View search history"
              aria-selected={activeTab === "history"}
              role="tab"
              className={`flex items-center gap-1 rounded px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] transition-colors ${
                activeTab === "history"
                  ? "text-gold bg-gold/10"
                  : "text-silver/60 hover:text-silver"
              }`}
            >
              <Clock size={10} />
              History
            </button>
            <button
              onClick={() => setActiveTab("bookmarks")}
              aria-label={`View saved bookmarks (${bookmarks.length} saved)`}
              aria-selected={activeTab === "bookmarks"}
              role="tab"
              className={`flex items-center gap-1 rounded px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] transition-colors ${
                activeTab === "bookmarks"
                  ? "text-gold bg-gold/10"
                  : "text-silver/60 hover:text-silver"
              }`}
            >
              <Bookmark size={10} />
              Saved ({bookmarks.length})
            </button>
          </div>

          {activeTab === "history" && (
            <div className="space-y-0.5">
              {history.length === 0 && (
                <div className="flex flex-col items-center rounded-lg border border-slate-custom/30 bg-charcoal/20 px-3 py-5 text-center">
                  <Clock size={16} className="mb-2 text-silver/25" />
                  <p className="text-[11px] leading-relaxed text-silver/35">
                    Your live HECTOR searches will appear here.
                  </p>
                </div>
              )}
              {history.map((item) => (
                <button
                  key={item.id}
                  onClick={() => onSelectHistory(item.query)}
                  onMouseEnter={() => setHoveredItem(item.id)}
                  onMouseLeave={() => setHoveredItem(null)}
                  className={`group flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2.5 text-left transition-all ${
                    hoveredItem === item.id
                      ? "bg-slate-custom/40 text-gold-light"
                      : "text-silver hover:bg-slate-custom/20 hover:text-silver"
                  }`}
                >
                  <span className="mt-0.5 shrink-0 text-silver/50 group-hover:text-gold/60">
                    {domainIcon(item.domain)}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] leading-snug">
                      {item.query}
                    </p>
                    <div className="mt-1 flex items-center gap-2 text-[10px] text-silver/40">
                      <Clock size={10} />
                      <span>
                        {new Date(item.timestamp).toLocaleDateString("en-IN", {
                          day: "numeric",
                          month: "short",
                        })}
                      </span>
                      <span className="rounded bg-slate-custom/50 px-1.5 py-0.5 text-[9px] uppercase tracking-wider">
                        {item.domain}
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {activeTab === "bookmarks" && (
            <div className="space-y-0.5">
              {bookmarks.length === 0 && (
                <div className="flex flex-col items-center rounded-lg border border-slate-custom/30 bg-charcoal/20 px-3 py-5 text-center">
                  <Bookmark size={16} className="mb-2 text-silver/25" />
                  <p className="text-[11px] leading-relaxed text-silver/35">
                    Bookmark sources from search results to save them here.
                  </p>
                </div>
              )}
              {bookmarks.map((item) => (
                <div
                  key={item.id}
                  className="group rounded-lg px-2.5 py-2.5 text-left transition-all"
                >
                  <div className="flex items-start justify-between gap-1">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[12px] font-medium text-silver/80">
                        {item.bookTitle}
                      </p>
                      <p className="mt-0.5 text-[11px] text-silver/40">
                        {item.act} &mdash; {item.section}
                      </p>
                      <p className="mt-0.5 truncate text-[11px] text-silver/30">
                        {item.query}
                      </p>
                    </div>
                    {onRemoveBookmark && (
                      <button
                        onClick={() => onRemoveBookmark(item.id)}
                        aria-label={`Remove bookmark for ${item.act} Section ${item.section}`}
                        className="shrink-0 rounded p-1 text-silver/20 opacity-0 transition-all group-hover:opacity-100 hover:text-error"
                      >
                        <BookmarkX size={12} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Footer Stats */}
      {!collapsed && (
        <div className="border-t border-slate-custom/40 px-4 py-3">
          <div className="flex items-center justify-between text-[10px] text-silver/40">
            <span>{systemStatus?.document_count ?? "\u2014"} documents indexed</span>
            <span className="flex items-center gap-1">
              <span className={`h-1.5 w-1.5 rounded-full ${systemStatus?.status === "ok" ? "bg-success" : "bg-warning"}`}></span>
              {systemStatus?.status === "ok" ? "Online" : "Checking..."}
            </span>
          </div>
        </div>
      )}

      {/* Collapse Toggle (desktop only) */}
      <button
        onClick={onToggle}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        className="absolute -right-3 top-5 z-10 hidden md:flex h-6 w-6 items-center justify-center rounded-full border border-slate-custom/60 bg-cream text-silver transition-colors hover:border-gold/40 hover:text-gold"
      >
        {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
      </button>
    </aside>
    </>
  );
}
