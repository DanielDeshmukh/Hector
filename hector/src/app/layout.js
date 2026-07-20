import "./globals.css";

const SITE_URL = "https://hector-legal.vercel.app";

export const metadata = {
  title: {
    default: "HECTOR — Zero-Hallucination Legal Research for Indian Law",
    template: "%s | HECTOR",
  },
  description:
    "Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval. AI-powered legal research engine for Indian Law with 13,479 chunks across 45 bare acts, IPC-to-BNS cross-referencing, and chain-of-verification for zero-hallucination cited responses.",
  keywords: [
    "Indian law",
    "legal research",
    "BNS",
    "IPC",
    "Bharatiya Nyaya Sanhita",
    "Indian Penal Code",
    "legal AI",
    "zero hallucination",
    "case law",
    "bare acts",
    "HECTOR",
    "legal intelligence",
  ],
  authors: [{ name: "Daniel Deshmukh" }],
  creator: "Daniel Deshmukh",
  publisher: "Daniel Deshmukh",
  metadataBase: new URL(SITE_URL),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    locale: "en_IN",
    url: SITE_URL,
    siteName: "HECTOR",
    title: "HECTOR — Zero-Hallucination Legal Research for Indian Law",
    description:
      "AI-powered legal research engine for Indian Law. 45 bare acts, 13,479 chunks, IPC-to-BNS cross-referencing, chain-of-verification.",
    images: [
      {
        url: "/tab-icon.png",
        width: 512,
        height: 512,
        alt: "HECTOR Legal Intelligence System",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "HECTOR — Zero-Hallucination Legal Research for Indian Law",
    description:
      "AI-powered legal research engine for Indian Law. 45 bare acts, 13,479 chunks, IPC-to-BNS cross-referencing.",
    images: ["/tab-icon.png"],
  },
  icons: {
    icon: "/tab-icon.png",
    shortcut: "/tab-icon.png",
    apple: "/tab-icon.png",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/tab-icon.png" sizes="any" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
