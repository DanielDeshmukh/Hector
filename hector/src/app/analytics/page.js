"use client";

import AnalyticsDashboard from "@/components/AnalyticsDashboard";
import Link from "next/link";

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen bg-cream">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-serif text-2xl font-semibold text-gold-light">
              Search Analytics
            </h1>
            <p className="text-[12px] text-silver/40 mt-1">
              Usage patterns, response times, and query insights
            </p>
          </div>
          <Link
            href="/"
            className="rounded-lg border border-slate-custom/60 px-4 py-2 text-[12px] font-medium text-silver/60 transition-colors hover:border-gold/40 hover:text-gold"
          >
            Back to HECTOR
          </Link>
        </div>
        <AnalyticsDashboard />
      </div>
    </div>
  );
}
