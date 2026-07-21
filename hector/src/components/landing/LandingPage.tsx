"use client";

import Navigation from "./Navigation";
import HeroSection from "./HeroSection";
import StatsSection from "./StatsSection";
import FeaturesSection from "./FeaturesSection";
import TechnologySection from "./TechnologySection";
import CoverageSection from "./CoverageSection";
import FAQSection from "./FAQSection";
import CTASection from "./CTASection";
import Footer from "./Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-cream font-sans text-white">
      <Navigation />
      <main>
        <HeroSection />
        <StatsSection />
        <FeaturesSection />
        <TechnologySection />
        <CoverageSection />
        <FAQSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
