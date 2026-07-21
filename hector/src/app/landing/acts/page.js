"use client";

import Link from "next/link";
import { Icons } from "@/components/landing/Icons";

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

const allActs = [
  { name: "Bharatiya Nyaya Sanhita, 2023", short: "BNS", year: 2023, status: "Active", category: "Criminal", icon: Icons.Scale },
  { name: "Bharatiya Nagarik Suraksha Sanhita, 2023", short: "BNSS", year: 2023, status: "Active", category: "Criminal Procedure", icon: Icons.Shield },
  { name: "Bharatiya Sakshya Adhiniyam, 2023", short: "BSA", year: 2023, status: "Active", category: "Evidence", icon: Icons.FileText },
  { name: "Indian Penal Code, 1860", short: "IPC", year: 1860, status: "Repealed", category: "Criminal", icon: Icons.Scale },
  { name: "Code of Criminal Procedure, 1973", short: "CrPC", year: 1973, status: "Repealed", category: "Criminal Procedure", icon: Icons.BookOpen },
  { name: "Code of Civil Procedure, 1908", short: "CPC", year: 1908, status: "Active", category: "Civil", icon: Icons.BookOpen },
  { name: "Indian Evidence Act, 1872", short: "IEA", year: 1872, status: "Repealed", category: "Evidence", icon: Icons.FileText },
  { name: "Constitution of India", short: "Constitution", year: 1950, status: "Active", category: "Constitutional", icon: Icons.Scale },
  { name: "Indian Contract Act, 1872", short: "ICA", year: 1872, status: "Active", category: "Civil", icon: Icons.BookOpen },
  { name: "Transfer of Property Act, 1882", short: "TPA", year: 1882, status: "Active", category: "Civil", icon: Icons.BookOpen },
  { name: "Indian Trusts Act, 1882", short: "ITA", year: 1882, status: "Active", category: "Civil", icon: Icons.BookOpen },
  { name: "Easements Act, 1882", short: "EA", year: 1882, status: "Active", category: "Civil", icon: Icons.BookOpen },
  { name: "Negotiable Instruments Act, 1881", short: "NI Act", year: 1881, status: "Active", category: "Civil", icon: Icons.FileText },
  { name: "Limitation Act, 1963", short: "LA", year: 1963, status: "Active", category: "Civil", icon: Icons.FileText },
  { name: "Specific Relief Act, 1963", short: "SRA", year: 1963, status: "Active", category: "Civil", icon: Icons.FileText },
  { name: "Hindu Marriage Act, 1955", short: "HMA", year: 1955, status: "Active", category: "Family Law", icon: Icons.Scale },
  { name: "Hindu Minority and Guardianship Act, 1956", short: "HMGA", year: 1956, status: "Active", category: "Family Law", icon: Icons.Scale },
  { name: "Hindu Succession Act, 1956", short: "HSA", year: 1956, status: "Active", category: "Family Law", icon: Icons.Scale },
  { name: "Dowry Prohibition Act, 1961", short: "DPA", year: 1961, status: "Active", category: "Family Law", icon: Icons.Scale },
  { name: "Family Courts Act, 1984", short: "FCA", year: 1984, status: "Active", category: "Family Law", icon: Icons.Scale },
  { name: "Protection of Women from Domestic Violence Act, 2005", short: "PWDVA", year: 2005, status: "Active", category: "Family Law", icon: Icons.Shield },
  { name: "Juvenile Justice Act, 2015", short: "JJ Act", year: 2015, status: "Active", category: "Family Law", icon: Icons.Shield },
  { name: "Arbitration and Conciliation Act, 1996", short: "Arb Act", year: 1996, status: "Active", category: "Civil", icon: Icons.Link },
  { name: "Competition Act, 2002", short: "CA", year: 2002, status: "Active", category: "Civil", icon: Icons.FileText },
  { name: "Industrial Disputes Act, 1947", short: "IDA", year: 1947, status: "Active", category: "Labour", icon: Icons.Database },
  { name: "Factories Act, 1948", short: "FA", year: 1948, status: "Active", category: "Labour", icon: Icons.Database },
  { name: "Motor Vehicles Act, 1988", short: "MVA", year: 1988, status: "Active", category: "Labour", icon: Icons.Database },
  { name: "Arms Act, 1959", short: "AA", year: 1959, status: "Active", category: "Other", icon: Icons.Shield },
  { name: "Copyright Act, 1957", short: "CA", year: 1957, status: "Active", category: "Other", icon: Icons.FileText },
  { name: "Forest Act, 1927", short: "FA", year: 1927, status: "Active", category: "Other", icon: Icons.Database },
  { name: "Narcotic Drugs and Psychotropic Substances Act, 1985", short: "NDPS", year: 1985, status: "Active", category: "Other", icon: Icons.Shield },
  { name: "Prevention of Corruption Act, 1988", short: "PCA", year: 1988, status: "Active", category: "Other", icon: Icons.Shield },
  { name: "Environment Protection Act, 1986", short: "EPA", year: 1986, status: "Active", category: "Other", icon: Icons.Database },
  { name: "Information Technology Act, 2000", short: "ITA", year: 2000, status: "Active", category: "Other", icon: Icons.Cpu },
  { name: "Right to Information Act, 2005", short: "RTI", year: 2005, status: "Active", category: "Other", icon: Icons.FileText },
  { name: "Consumer Protection Act, 2019", short: "CPA", year: 2019, status: "Active", category: "Other", icon: Icons.Shield },
  { name: "Legal Services Authorities Act, 1987", short: "LSAA", year: 1987, status: "Active", category: "Other", icon: Icons.Scale },
  { name: "Gram Nyayalayas Act, 2008", short: "GNA", year: 2008, status: "Active", category: "Other", icon: Icons.Scale },
];

const categories = [...new Set(allActs.map((a) => a.category))];

export default function ActsPage() {
  return (
    <div className="min-h-screen bg-cream font-sans text-white">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-cream/90 backdrop-blur-md shadow-sm border-b border-white/5">
        <div className="w-full px-6 lg:px-12">
          <div className="flex items-center justify-between h-16 lg:h-20">
            <Link href="/landing" className="flex items-center gap-3 group">
              <img
                src="/tab-icon.png"
                alt="HECTOR"
                className="w-10 h-10 rounded-lg shadow-lg shadow-charcoal/20"
              />
              <div className="hidden sm:block">
                <span className="font-serif text-lg font-semibold text-white tracking-tight">
                  HECTOR
                </span>
                <span className="block text-[10px] uppercase tracking-widest text-silver font-medium">
                  Legal Intelligence
                </span>
              </div>
            </Link>
            <Link
              href="/landing"
              className="text-sm font-medium text-silver hover:text-gold transition-colors"
            >
              &larr; Back to Home
            </Link>
          </div>
        </div>
      </nav>

      <main className="pt-24 pb-20">
        <div className="w-full px-6 lg:px-12">
          <div className="max-w-7xl mx-auto">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <span className="inline-block px-4 py-1.5 bg-gold-light/50 text-gold text-sm font-medium rounded-full mb-4">
                Legal Coverage
              </span>
              <h1 className="font-serif text-3xl lg:text-5xl font-semibold text-white mb-6">
                All 38 Bare Acts
              </h1>
              <p className="text-lg text-silver">
                Complete list of Indian legal texts indexed in HECTOR. Each act
                has been parsed into searchable chunks with IPC-to-BNS
                cross-referencing.
              </p>
            </div>

            {categories.map((category) => {
              const categoryActs = allActs.filter(
                (a) => a.category === category
              );
              return (
                <div key={category} className="mb-12">
                  <h2 className="font-serif text-xl font-semibold text-white mb-4 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-gold" />
                    {category}
                    <span className="text-sm text-silver font-normal">
                      ({categoryActs.length})
                    </span>
                  </h2>
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {categoryActs.map((act) => (
                      <div
                        key={act.name}
                        className="group p-5 bg-slate-custom rounded-xl border border-white/5 hover:border-gold-light hover:bg-gold-light/10 transition-all"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-lg bg-charcoal text-silver flex items-center justify-center group-hover:bg-gold group-hover:text-charcoal transition-colors flex-shrink-0">
                            <act.icon />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-medium text-white text-sm truncate">
                                {act.name}
                              </h3>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-silver">
                                {act.year}
                              </span>
                              <span className="text-xs text-silver">&middot;</span>
                              <span className="text-xs text-silver font-mono">
                                {act.short}
                              </span>
                              <span
                                className={cn(
                                  "text-[10px] font-medium px-1.5 py-0.5 rounded-full ml-auto",
                                  act.status === "Active"
                                    ? "bg-success/20 text-success"
                                    : "bg-gold/20 text-gold"
                                )}
                              >
                                {act.status}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </main>
    </div>
  );
}
