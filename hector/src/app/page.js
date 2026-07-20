"use client";

import dynamic from "next/dynamic";
import { LanguageProvider } from "@/i18n/LanguageContext";

const App = dynamic(() => import("@/components/App"), { ssr: false });

export default function Home() {
  return (
    <LanguageProvider>
      <App />
    </LanguageProvider>
  );
}
