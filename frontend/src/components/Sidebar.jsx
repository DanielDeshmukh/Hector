import { useState } from "react";
import {
  Scale,
  Clock,
  Plus,
  ChevronLeft,
  ChevronRight,
  BookOpen,
  Gavel,
  FileText,
} from "lucide-react";

export default function Sidebar({
  collapsed,
  onToggle,
  onNewQuery,
  onSelectHistory,
  history,
}) {
  const [hoveredItem, setHoveredItem] = useState(null);

  const domainIcon = (domain) => {
    switch (domain) {
      case "Criminal":
        return <Gavel size={14} />;
      case "Procedural":
        return <FileText size={14} />;
      case "LEGAL_RESEARCH":
      case "Legal Research":
        return <Scale size={14} />;
      default:
        return <BookOpen size={14} />;
    }
  };

  return (
    <aside
      className={`relative flex flex-col border-r border-slate-custom/60 bg-cream transition-all duration-300 ${
        collapsed ? "w-[56px]" : "w-[280px]"
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-slate-custom/40 px-3 py-4">
        {!collapsed && (
          <div className="flex items-center gap-2.5 animate-fade-in">
            <div className="flex h-8 w-8 items-center justify-center rounded-md border border-gold/30 bg-gold/10">
              <Scale size={16} className="text-gold" />
            </div>
            <div>
              <h1 className="font-serif text-lg font-semibold tracking-wide text-gold-light leading-none">
                HECTOR
              </h1>
              <p className="text-[10px] font-medium uppercase tracking-[0.15em] text-silver mt-0.5">
                Legal Intelligence
              </p>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="flex h-8 w-8 items-center justify-center rounded-md border border-gold/30 bg-gold/10">
            <Scale size={16} className="text-gold" />
          </div>
        )}
      </div>

      {/* New Query Button */}
      <div className="px-2.5 pt-3 pb-1">
        <button
          onClick={onNewQuery}
          className={`flex w-full items-center gap-2.5 rounded-lg border border-slate-custom/60 px-3 py-2.5 text-sm text-silver transition-all hover:border-gold/40 hover:text-gold-light hover:bg-gold/5 ${
            collapsed ? "justify-center" : ""
          }`}
        >
          <Plus size={16} />
          {!collapsed && <span className="font-medium">New Query</span>}
        </button>
      </div>

      {/* History */}
      {!collapsed && (
        <div className="flex-1 overflow-y-auto px-2.5 pt-4">
          <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-silver/60">
            Recent Queries
          </p>
          <div className="space-y-0.5">
            {history.length === 0 && (
              <div className="rounded-lg border border-slate-custom/30 bg-charcoal/20 px-3 py-3 text-[12px] leading-relaxed text-silver/35">
                Your live HECTOR searches will appear here.
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
        </div>
      )}

      {/* Footer Stats */}
      {!collapsed && (
        <div className="border-t border-slate-custom/40 px-4 py-3">
          <div className="flex items-center justify-between text-[10px] text-silver/40">
            <span>20+ Legal Texts Indexed</span>
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-success"></span>
              Online
            </span>
          </div>
        </div>
      )}

      {/* Collapse Toggle */}
      <button
        onClick={onToggle}
        className="absolute -right-3 top-5 z-10 flex h-6 w-6 items-center justify-center rounded-full border border-slate-custom/60 bg-cream text-silver transition-colors hover:border-gold/40 hover:text-gold"
      >
        {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
      </button>
    </aside>
  );
}
