"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/landing/cn";
import { SectionShell } from "./ui";
import { FAQ } from "@/lib/landing/samples";

export function FaqSection() {
  const [open, setOpen] = useState(0);
  return (
    <SectionShell
      id="faq"
      no="09"
      kicker="Questions of construction"
      title={
        <>
          Read it
          <span className="block italic text-gold-light">as a set of clauses.</span>
        </>
      }
      lede={
        <>
          The objections we hear most often, answered without a marketing register. Where the answer is
          &ldquo;it depends on the text&rdquo;, we say so and point at the text.
        </>
      }
    >
      <ol className="border-t border-hair">
        {FAQ.map((f, i) => {
          const on = open === i;
          return (
            <li key={f.q} className="border-b border-hair">
              <button
                onClick={() => setOpen(on ? -1 : i)}
                aria-expanded={on}
                className="group flex w-full items-start gap-4 py-4 text-left transition-colors duration-200 hover:bg-panel/40"
              >
                <span className={cn("mt-1 font-mono text-[10.5px]", on ? "text-gold" : "text-muted")}>
                  {`(${String.fromCharCode(97 + i)})`}
                </span>
                <span
                  className={cn(
                    "flex-1 font-display text-[clamp(1.1rem,2.1vw,1.5rem)] leading-snug tracking-tight transition-colors duration-200",
                    on ? "text-gold-light" : "text-paper group-hover:text-paper",
                  )}
                >
                  {f.q}
                </span>
                <span className={cn("mt-1 transition-transform duration-300", on ? "rotate-180 text-gold" : "text-muted")}>
                  <ChevronDown className="h-4 w-4" strokeWidth={1.6} />
                </span>
              </button>
              <div
                className="grid transition-[grid-template-rows] duration-500 ease-out"
                style={{ gridTemplateRows: on ? "1fr" : "0fr" }}
              >
                <div className="overflow-hidden">
                  <p className="max-w-[74ch] pb-5 pl-[46px] pr-8 text-[13.5px] leading-[1.75] text-silver">{f.a}</p>
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </SectionShell>
  );
}
