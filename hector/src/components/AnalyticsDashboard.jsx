"use client";

import { useState, useEffect } from "react";
import { BarChart3, Clock, Database, TrendingUp, Search, Activity } from "lucide-react";

const API_URL = "/api";

function StatCard({ icon, label, value, sub }) {
  return (
    <div className="rounded-xl border border-slate-custom/30 bg-charcoal/40 p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-gold/60">{icon}</span>
        <span className="text-[11px] font-medium uppercase tracking-wider text-silver/50">{label}</span>
      </div>
      <p className="text-2xl font-serif font-semibold text-gold-light">{value}</p>
      {sub && <p className="text-[11px] text-silver/40 mt-1">{sub}</p>}
    </div>
  );
}

function BarRow({ label, count, total, color = "bg-gold" }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="w-28 text-[11px] text-silver/60 truncate" title={label}>{label}</span>
      <div className="flex-1 h-2 rounded-full bg-slate-custom/20 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-12 text-right text-[11px] font-mono text-silver/40">{count}</span>
    </div>
  );
}

export default function AnalyticsDashboard() {
  const [overview, setOverview] = useState(null);
  const [popular, setPopular] = useState([]);
  const [domains, setDomains] = useState([]);
  const [confidence, setConfidence] = useState({});
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const [ov, pop, dom, conf, rec] = await Promise.all([
          fetch(`${API_URL}/analytics/overview`).then(r => r.json()),
          fetch(`${API_URL}/analytics/popular?limit=10`).then(r => r.json()),
          fetch(`${API_URL}/analytics/domains`).then(r => r.json()),
          fetch(`${API_URL}/analytics/confidence`).then(r => r.json()),
          fetch(`${API_URL}/analytics/recent?limit=15`).then(r => r.json()),
        ]);
        setOverview(ov);
        setPopular(pop);
        setDomains(dom);
        setConfidence(conf);
        setRecent(rec);
      } catch (err) {
        console.error("Failed to load analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-sm text-silver/40">Loading analytics...</div>
      </div>
    );
  }

  const totalConf = Object.values(confidence).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Overview cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          icon={<Search size={14} />}
          label="Total Queries"
          value={overview?.total_queries ?? 0}
          sub={`Last ${overview?.period_days ?? 30} days`}
        />
        <StatCard
          icon={<Clock size={14} />}
          label="Avg Response"
          value={`${overview?.avg_response_ms ?? 0}ms`}
          sub="Across all queries"
        />
        <StatCard
          icon={<Database size={14} />}
          label="Cache Hit Rate"
          value={`${overview?.cache_hit_rate ?? 0}%`}
          sub="Served from cache"
        />
        <StatCard
          icon={<Activity size={14} />}
          label="Routes Active"
          value={domains.length}
          sub={domains.map(d => d.route).join(", ")}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Popular queries */}
        <div className="rounded-xl border border-slate-custom/30 bg-charcoal/40 p-5">
          <h3 className="text-[12px] font-semibold uppercase tracking-wider text-silver/50 mb-4">
            Popular Queries
          </h3>
          {popular.length === 0 ? (
            <p className="text-[12px] text-silver/30">No queries recorded yet.</p>
          ) : (
            <div className="space-y-0.5">
              {popular.map((q, i) => (
                <BarRow key={i} label={q.query} count={q.count} total={popular[0]?.count || 1} />
              ))}
            </div>
          )}
        </div>

        {/* Domain breakdown */}
        <div className="rounded-xl border border-slate-custom/30 bg-charcoal/40 p-5">
          <h3 className="text-[12px] font-semibold uppercase tracking-wider text-silver/50 mb-4">
            Domain Breakdown
          </h3>
          {domains.length === 0 ? (
            <p className="text-[12px] text-silver/30">No domain data yet.</p>
          ) : (
            <div className="space-y-0.5">
              {domains.map((d, i) => (
                <BarRow
                  key={i}
                  label={d.route?.replace(/_/g, " ") || "Unknown"}
                  count={d.count}
                  total={domains[0]?.count || 1}
                  color={i === 0 ? "bg-gold" : i === 1 ? "bg-success" : "bg-silver/30"}
                />
              ))}
            </div>
          )}
        </div>

        {/* Confidence distribution */}
        <div className="rounded-xl border border-slate-custom/30 bg-charcoal/40 p-5">
          <h3 className="text-[12px] font-semibold uppercase tracking-wider text-silver/50 mb-4">
            Confidence Distribution
          </h3>
          <div className="grid grid-cols-4 gap-2">
            {[
              { key: "high", label: "High", color: "text-success" },
              { key: "medium", label: "Medium", color: "text-gold" },
              { key: "low", label: "Low", color: "text-error" },
              { key: "very_low", label: "Very Low", color: "text-silver/40" },
            ].map(({ key, label, color }) => (
              <div key={key} className="text-center">
                <p className={`text-xl font-serif font-semibold ${color}`}>
                  {confidence[key] || 0}
                </p>
                <p className="text-[10px] text-silver/40 mt-1">{label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recent queries */}
        <div className="rounded-xl border border-slate-custom/30 bg-charcoal/40 p-5">
          <h3 className="text-[12px] font-semibold uppercase tracking-wider text-silver/50 mb-4">
            Recent Queries
          </h3>
          {recent.length === 0 ? (
            <p className="text-[12px] text-silver/30">No recent queries.</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {recent.map((q, i) => (
                <div key={i} className="flex items-center gap-2 py-1 border-b border-slate-custom/20 last:border-0">
                  <span className={`h-1.5 w-1.5 rounded-full ${q.cache_hit ? "bg-gold" : "bg-success"}`} />
                  <span className="flex-1 text-[11px] text-silver/60 truncate" title={q.query}>
                    {q.query}
                  </span>
                  <span className="text-[10px] text-silver/30 font-mono">
                    {q.response_ms ? `${Math.round(q.response_ms)}ms` : "cached"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
