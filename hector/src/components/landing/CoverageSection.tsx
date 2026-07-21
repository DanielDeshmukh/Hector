import Link from "next/link";
import { Icons } from "./Icons";

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

const featuredActs = [
  { name: "Bharatiya Nyaya Sanhita (BNS)", year: "2023", status: "Active", category: "Criminal", icon: Icons.Scale },
  { name: "Bharatiya Nagarik Suraksha Sanhita (BNSS)", year: "2023", status: "Active", category: "Criminal Procedure", icon: Icons.Shield },
  { name: "Bharatiya Sakshya Adhiniyam (BSA)", year: "2023", status: "Active", category: "Evidence", icon: Icons.FileText },
  { name: "Indian Penal Code (IPC)", year: "1860", status: "Repealed", category: "Criminal", icon: Icons.Scale },
  { name: "Code of Criminal Procedure (CrPC)", year: "1973", status: "Repealed", category: "Criminal Procedure", icon: Icons.BookOpen },
  { name: "Indian Evidence Act", year: "1872", status: "Repealed", category: "Evidence", icon: Icons.FileText },
  { name: "Constitution of India", year: "1950", status: "Active", category: "Constitutional", icon: Icons.Scale },
  { name: "Indian Contract Act", year: "1872", status: "Active", category: "Civil", icon: Icons.BookOpen },
];

export default function CoverageSection() {
  return (
    <section id="coverage" className="py-24 lg:py-32 bg-charcoal">
      <div className="w-full px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="inline-block px-4 py-1.5 bg-gold-light/50 text-gold text-sm font-medium rounded-full mb-4">
              Legal Coverage
            </span>
            <h2 className="font-serif text-3xl lg:text-5xl font-semibold text-white mb-6">
              38 Bare Acts, Fully Indexed
            </h2>
            <p className="text-lg text-silver">
              Comprehensive coverage of civil and criminal law with full
              cross-referencing between legacy codes and new Sanhita laws.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {featuredActs.map((act) => (
              <div
                key={act.name}
                className="group p-6 bg-slate-custom rounded-xl border border-white/5 hover:border-gold-light hover:bg-gold-light/10 transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg bg-charcoal text-silver flex items-center justify-center group-hover:bg-gold group-hover:text-charcoal transition-colors">
                    <act.icon />
                  </div>
                  <span
                    className={cn(
                      "text-xs font-medium px-2 py-1 rounded-full",
                      act.status === "Active"
                        ? "bg-success/20 text-success"
                        : "bg-gold/20 text-gold"
                    )}
                  >
                    {act.status}
                  </span>
                </div>
                <h3 className="font-medium text-white mb-1 line-clamp-2">
                  {act.name}
                </h3>
                <p className="text-sm text-silver">
                  Year {act.year} &middot; {act.category}
                </p>
              </div>
            ))}
          </div>

          <div className="text-center mt-8">
            <Link
              href="/landing/acts"
              className="inline-flex items-center gap-2 text-gold font-medium hover:text-gold transition-colors"
            >
              View all 38 bare acts
              <Icons.ArrowRight />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
