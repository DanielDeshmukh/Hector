import ExactLanding from "@/components/landing/exact/src/App.jsx";

export const metadata = {
  title: "HECTOR — Bare-Act Retrieval for Indian Law",
  description:
    "Explore HECTOR's section-boundary grammar, chunking behavior, and live index-backed search and comparison.",
  alternates: { canonical: "/" },
};

export default function Page() {
  return <ExactLanding />;
}
