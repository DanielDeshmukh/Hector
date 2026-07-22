"use client";

import { useState } from "react";
import { Icons } from "./Icons";

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

const faqs = [
  {
    question: "What makes HECTOR different from other legal AI tools?",
    answer:
      "HECTOR is built specifically for Indian law with a focus on zero hallucinations. Unlike general AI tools, every citation is verified against primary sources before being included in responses. We also provide IPC-to-BNS cross-referencing, which is essential during India's legal code transition.",
  },
  {
    question: "How does the chain-of-verification work?",
    answer:
      "Every response goes through a multi-layer verification pipeline. First, sources are retrieved from our indexed database. Then, each citation is checked for existence against official bare acts. Finally, the text is verified for accuracy before being presented to you with appropriate confidence scores.",
  },
  {
    question: "What bare acts are covered?",
    answer:
      "HECTOR covers 38+ bare acts including all major criminal and civil laws. This includes the new Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), Bharatiya Sakshya Adhiniyam (BSA), as well as legacy codes like IPC, CrPC, and Evidence Act with full cross-referencing.",
  },
  {
    question: "Can I use HECTOR citations in court?",
    answer:
      "Yes. HECTOR provides verified citations with hyperlinks to source documents. However, we recommend verifying critical citations independently before final submission, as you would with any research tool. Our verification reports can be exported for your records.",
  },
    {
      question: "How do I start using HECTOR?",
      answer:
        "HECTOR is available as a web application. No account or sign-up is required. Simply visit the app and start your legal research. We also offer an API for developers who want to integrate HECTOR into their own tools.",
    },
  {
    question: "How often is the database updated?",
    answer:
      "Our database is updated weekly with new amendments, notifications, and gazette entries. Major legislative changes like the BNS implementation are prioritized and updated within 48 hours of official publication.",
  },
];

export default function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="py-24 lg:py-32 bg-cream">
      <div className="w-full px-6 lg:px-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 bg-slate-custom text-silver text-sm font-medium rounded-full mb-4">
              FAQ
            </span>
            <h2 className="font-serif text-3xl lg:text-5xl font-semibold text-white mb-6">
              Frequently Asked Questions
            </h2>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <div
                key={index}
                className="bg-charcoal rounded-xl border border-white/5 overflow-hidden"
              >
                <button
                  onClick={() =>
                    setOpenIndex(openIndex === index ? null : index)
                  }
                  className="w-full flex items-center justify-between p-6 text-left hover:bg-slate-custom transition-colors"
                >
                  <span className="font-medium text-white pr-4">
                    {faq.question}
                  </span>
                  <span
                    className={cn(
                      "flex-shrink-0 transition-transform duration-300",
                      openIndex === index ? "rotate-180" : ""
                    )}
                  >
                    <Icons.ChevronDown />
                  </span>
                </button>
                <div
                  className={cn(
                    "overflow-hidden transition-all duration-300",
                    openIndex === index ? "max-h-96" : "max-h-0"
                  )}
                >
                  <p className="px-6 pb-6 text-silver leading-relaxed">
                    {faq.answer}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
