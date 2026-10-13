"use client";

import ComparisonView from "@/components/ComparisonView";
import { useApp } from "@/components/appContext";

export default function CompareClient() {
  const { handleCompare, compareData, compareLoading, compareError } = useApp();

  return (
    <ComparisonView
      onCompare={handleCompare}
      compareData={compareData}
      compareLoading={compareLoading}
      compareError={compareError}
    />
  );
}
