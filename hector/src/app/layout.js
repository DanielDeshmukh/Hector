import "./globals.css";

const SITE_URL = "https://hector-nine.vercel.app";

export const metadata = {
  title: {
    default: "HECTOR — Zero-Hallucination Legal Research for Indian Law",
    template: "%s | HECTOR",
  },
  description:
    "Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval. AI-powered legal research engine for Indian Law with IPC-to-BNS cross-referencing and chain-of-verification for cited responses.",
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
  openGraph: {
    type: "website",
    locale: "en_IN",
    siteName: "HECTOR",
    title: "HECTOR — Zero-Hallucination Legal Research for Indian Law",
    description:
      "AI-powered legal research engine for Indian Law. 38 bare acts, 13,479 chunks, IPC-to-BNS cross-referencing, chain-of-verification.",
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
      "AI-powered legal research engine for Indian Law. 38 bare acts, 13,479 chunks, IPC-to-BNS cross-referencing.",
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
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/tab-icon.png" sizes="any" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..900;1,6..96,400..900&family=IBM+Plex+Mono:ital,wght@0,300;0,400;0,500;0,600;1,400&family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
