"use client";

import { useEffect, useState } from "react";
import { Icons } from "./Icons";

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

const navLinks = [
  { label: "Features", href: "#features" },
  { label: "Technology", href: "#technology" },
  { label: "Coverage", href: "#coverage" },
  { label: "FAQ", href: "#faq" },
];

export default function Navigation() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        isScrolled
          ? "bg-cream/90 backdrop-blur-md shadow-sm border-b border-white/5"
          : "bg-transparent"
      )}
    >
      <div className="w-full px-6 lg:px-12">
        <div className="flex items-center justify-between h-16 lg:h-20">
          <a href="#" className="flex items-center gap-3 group">
            <img
              src="/tab-icon.png"
              alt="HECTOR"
              className="w-10 h-10 rounded-lg shadow-lg shadow-charcoal/20 group-hover:shadow-charcoal/30 transition-shadow"
            />
            <div className="hidden sm:block">
              <span className="font-serif text-lg font-semibold text-white tracking-tight">
                HECTOR
              </span>
              <span className="block text-[10px] uppercase tracking-widest text-silver font-medium">
                Legal Intelligence
              </span>
            </div>
          </a>

          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-sm font-medium text-silver hover:text-gold transition-colors relative group"
              >
                {link.label}
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gold transition-all group-hover:w-full" />
              </a>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-4">
            <a
              href="#demo"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-gold text-charcoal text-sm font-medium rounded-lg hover:bg-gold-light transition-colors"
            >
              Try HECTOR
              <Icons.ArrowRight />
            </a>
          </div>

          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 text-silver hover:text-white"
          >
            {isMobileMenuOpen ? <Icons.X /> : <Icons.Menu />}
          </button>
        </div>
      </div>

      {isMobileMenuOpen && (
        <div className="md:hidden bg-charcoal border-t border-white/5 shadow-lg">
          <div className="px-6 py-4 space-y-3">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                onClick={() => setIsMobileMenuOpen(false)}
                className="block py-2 text-silver hover:text-gold font-medium"
              >
                {link.label}
              </a>
            ))}
            <a
              href="#demo"
              onClick={() => setIsMobileMenuOpen(false)}
              className="block w-full py-3 px-4 bg-gold text-charcoal text-center font-medium rounded-lg mt-4"
            >
              Try HECTOR
            </a>
          </div>
        </div>
      )}
    </nav>
  );
}
