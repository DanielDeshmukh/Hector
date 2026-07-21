"use client";

import { useEffect, useRef, useState } from "react";
import { Icons } from "./Icons";
import { useCountUp } from "@/hooks/useCountUp";

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

const stats = [
  { value: 13479, suffix: "+", label: "Legal Chunks Indexed", icon: Icons.Database },
  { value: 45, suffix: "", label: "Bare Acts Covered", icon: Icons.BookOpen },
  { value: 99, suffix: ".7%", label: "Citation Accuracy", icon: Icons.Shield },
  { value: 0, suffix: "", label: "Hallucinations", icon: Icons.Zap },
];

function StatItem({
  stat,
  index,
  isVisible,
}: {
  stat: (typeof stats)[number];
  index: number;
  isVisible: boolean;
}) {
  const count = useCountUp(stat.value, 2000, isVisible);

  return (
    <div
      className={cn(
        "text-center lg:text-left transition-all duration-700",
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
      )}
      style={{ transitionDelay: `${index * 100}ms` }}
    >
      <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-slate-custom text-gold mb-4">
        <stat.icon />
      </div>
      <div className="flex items-baseline justify-center lg:justify-start gap-1">
        <span className="text-4xl lg:text-5xl font-bold text-white">
          {count}
        </span>
        <span className="text-2xl lg:text-3xl font-bold text-gold">
          {stat.suffix}
        </span>
      </div>
      <p className="text-silver mt-2">{stat.label}</p>
    </div>
  );
}

export default function StatsSection() {
  const [isVisible, setIsVisible] = useState(false);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="py-20 bg-charcoal">
      <div className="w-full px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
            {stats.map((stat, index) => (
              <StatItem
                key={stat.label}
                stat={stat}
                index={index}
                isVisible={isVisible}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
