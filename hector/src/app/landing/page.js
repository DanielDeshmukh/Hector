import LandingPage from "@/components/landing/LandingPage";

export const metadata = {
  title: "HECTOR — Bare-Act Retrieval for Indian Law",
  description:
    "How the HECTOR corpus is built: the regex boundary grammar that divides a bare act at its section heads, the cut rules that keep provisos attached, and the validation gates every statute must pass.",
};

export default function Page() {
  return <LandingPage />;
}
