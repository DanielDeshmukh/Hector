import CompareClient from "./CompareClient";

export const metadata = {
  title: "IPC / BNS Comparison",
  alternates: { canonical: "/compare" },
};

export default function Page() {
  return <CompareClient />;
}
