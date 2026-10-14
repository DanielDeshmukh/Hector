import SearchClient from "../SearchClient";

export const metadata = {
  title: "Search",
  description: "Search the HECTOR legal index.",
  alternates: { canonical: "/search" },
};

export default function Page() {
  return <SearchClient />;
}