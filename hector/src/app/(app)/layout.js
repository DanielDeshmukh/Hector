"use client";

import dynamic from "next/dynamic";

const AppShell = dynamic(() => import("@/components/AppShell"), { ssr: false });

export default function AppLayout({ children }) {
  return <AppShell>{children}</AppShell>;
}
