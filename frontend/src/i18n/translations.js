const translations = {
  en: {
    // Sidebar
    "sidebar.brand": "Legal Intelligence",
    "sidebar.newQuery": "New Query",
    "sidebar.history": "History",
    "sidebar.saved": "Saved",
    "sidebar.historyEmpty": "Your live HECTOR searches will appear here.",
    "sidebar.bookmarksEmpty": "Bookmark sources from search results to save them here.",
    "sidebar.documentsIndexed": "documents indexed",
    "sidebar.online": "Online",
    "sidebar.checking": "Checking...",

    // Header
    "header.ready": "Ready for queries",
    "header.processing": "Processing...",
    "header.resolved": "Query Resolved",
    "header.compareMode": "Search Mode",
    "header.searchMode": "Compare IPC/BNS",

    // Query Input
    "query.placeholder": 'Enter your legal query - e.g., "What is the BNS equivalent of IPC Section 302?"',
    "query.toSubmit": "to submit",

    // Welcome Screen
    "welcome.title": "HECTOR",
    "welcome.subtitle": "Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval",
    "welcome.intentRouting": "Intent Routing",
    "welcome.intentRoutingDesc": "Queries classified by legal domain - Criminal, Civil, or Procedural - to prevent data bleeding.",
    "welcome.hybridRetrieval": "Hybrid Retrieval",
    "welcome.hybridRetrievalDesc": "Dual-search combining semantic understanding with keyword precision across legal texts.",
    "welcome.hierarchicalContext": "Hierarchical Context",
    "welcome.hierarchicalContextDesc": "Sub-clauses automatically pull parent Section, Chapter, and Act titles for complete context.",
    "welcome.citationGrounding": "Citation Grounding",
    "welcome.citationGroundingDesc": "Every response verified against source material. Unverified claims are refused, not guessed.",
    "welcome.disclaimer": "HECTOR retrieves information exclusively from its curated library of legal commentaries and Bare Acts. Responses are not legal advice. Always verify with authorised legal counsel.",

    // Processing
    "processing.query": "Your Query",

    // Comparison
    "compare.title": "IPC \u2194 BNS Comparison",
    "compare.subtitle": "Enter a section number to compare across acts",
    "compare.results": "Results",
    "compare.noResults": "No results found",
    "compare.loading": "Comparing sections...",

    // Response
    "response.query": "Query",
    "response.response": "Response",
    "response.confidence": "Confidence",
    "response.sources": "Source Documents",
    "response.citationGrounding": "Citation Grounding",
    "response.note": "Note: This is for informational purposes only and does not constitute legal advice.",

    // Features
    "features.criminal": "Criminal",
    "features.civil": "Civil",
    "features.procedural": "Procedural",
  },
  hi: {
    // Sidebar
    "sidebar.brand": "\u0915\u093e\u0928\u0942\u0928\u0940 \u092c\u0941\u0926\u094d\u0927\u093f",
    "sidebar.newQuery": "\u0928\u0908 \u0915\u094d\u0935\u0947\u0937\u094d\u0939",
    "sidebar.history": "\u0907\u0924\u093f\u0939\u093e\u0938",
    "sidebar.saved": "\u0938\u0939\u0947\u0928\u0947 \u0915\u0940 \u0917\u092f\u0947",
    "sidebar.historyEmpty": "\u0906\u092a\u0915\u0947 HECTOR \u0916\u094b\u091c\u0947\u0928 \u092f\u0939\u093e\u0901 \u0926\u093f\u0916\u093e\u090f\u0902\u0917\u0947\u0964",
    "sidebar.bookmarksEmpty": "\u0938\u094d\u0930\u094b\u0924 \u092a\u0930\u093f\u0923\u093e\u092e\u094b\u0902 \u0938\u0947 \u092c\u0941\u0915\u092e\u093e\u0930\u094d\u0915 \u0932\u0932\u093e\u0915\u0930 \u092f\u0939\u093e\u0901\u0964",
    "sidebar.documentsIndexed": "\u0926\u0938\u094d\u0924\u093e\u0935\u0947\u091c\u093c \u0907\u0902\u0921\u0947\u0915\u094d\u0938",
    "sidebar.online": "\u0911\u0928\u0932\u093e\u0907\u0928",
    "sidebar.checking": "\u091c\u093e\u0901\u091a \u0939\u094b \u0930\u0939\u093e \u0939\u0948...",

    // Header
    "header.ready": "\u0915\u094d\u0935\u0947\u0936\u093e\u0913\u0902 \u0915\u0947 \u0932\u093f\u090f \u0924\u092f\u093e\u0930",
    "header.processing": "\u092a\u094d\u0930\u0915\u0930\u093f\u092f\u093e \u0939\u094b \u0930\u0939\u093e \u0939\u0948...",
    "header.resolved": "\u0915\u094d\u0935\u0947\u0936 \u0939\u0932 \u0939\u094b \u0917\u092f\u093e",
    "header.compareMode": "\u0916\u094b\u091c \u092e\u094b\u0921",
    "header.searchMode": "IPC/BNS \u0924\u0941\u0932\u0928\u093e",

    // Query Input
    "query.placeholder": '\u0905\u092a\u0928\u0940 \u0915\u093e\u0928\u0942\u0928\u0940 \u092a\u094d\u0930\u0936\u094d\u0928 \u0926\u0930\u094d\u091c \u0915\u0930\u0947\u0902 - \u091c\u0948\u0938\u0947, "IPC \u0927\u093e\u0930\u093e 302 \u0915\u093e BNS \u0938\u092e\u0915\u094d\u0937 \u0915\u094d\u092f\u093e \u0939\u0948?"',
    "query.toSubmit": "\u0915\u094d\u0935\u0947\u0936 \u0915\u0930\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f",

    // Welcome Screen
    "welcome.title": "HECTOR",
    "welcome.subtitle": "\u0938\u093f\u0935\u093f\u0932 \u092a\u094d\u0930\u0915\u093e\u0930 \u092a\u094d\u0930\u0923\u093e\u0932\u0940 \u0915\u093e \u092a\u094d\u0930\u0924\u094d\u0937\u093e\u0935\u0932\u094b\u0915\u094d\u0937\u0928 \u0914\u0930 \u092a\u094d\u0930\u093e\u092a\u094d\u0924",
    "welcome.intentRouting": "\u0907\u0902\u091f\u0947\u0928\u094d\u091f \u0930\u0942\u091f\u093f\u0902\u0917",
    "welcome.intentRoutingDesc": "\u0915\u093e\u0928\u0942\u0928\u094b\u0902 \u0915\u093e\u0935\u0948\u0907\u0902\u091f\u0940 \u0921\u094b\u092e\u0947\u0928 \u0926\u094d\u0935\u093e\u0930\u093e \u0935\u0930\u094d\u0917\u0940\u0915\u0930\u0923 \u0915\u093f\u092f\u093e \u091c\u093e\u0924\u093e \u0939\u0948 - \u0906\u092a\u0930\u093e\u0927, \u0926\u0940\u0935\u092f\u0940\u092f \u092f\u093e \u092a\u094d\u0930\u0915\u093f\u0930\u093f\u092f \u092f\u093e \u092a\u094d\u0930\u0915\u094d\u0937\u0947\u0924\u0928 \u0930\u094b\u0915\u093e \u092e\u0947\u0902\u0964",
    "welcome.hybridRetrieval": "\u0939\u093e\u0907\u092c\u094d\u0930\u093f\u0921 \u092a\u094d\u0930\u093e\u092a\u094d\u0924",
    "welcome.hybridRetrievalDesc": "\u0938\u0947\u092e\u093e\u0902\u091f\u093f\u0915 \u0938\u092e\u091d \u0914\u0930 \u0936\u092C\u094d\u0926 \u0938\u0939\u0940 \u092e\u0947\u0902 \u0926\u094d\u0935\u093f\u0927 \u0915\u093e\u0928\u0942\u0928\u094b\u0902 \u092e\u0947\u0902\u0964",
    "welcome.hierarchicalContext": "\u0935\u0947\u0928\u094d\u0924\u093f\u0915\u0943\u0924 \u0938\u0902\u0926\u0930\u094d\u092d",
    "welcome.hierarchicalContextDesc": "\u0909\u092a-0927\u093e\u0930\u093e\u090f\u0901 \u0938\u094d\u0935\u092f\u093e\u092e\u093e\u0928\u094d\u0935\u093f\u0924 \u0930\u0942\u092a \u0935\u093f\u0937\u092f, \u0905\u0927\u094d\u092f\u093e\u092f \u0914\u0930 \u0905\u0927\u093f\u0928\u093f\u092f\u092e \u0936\u0940\u0930\u094d\u0937\u0915 \u0915\u094d0938\u093e\u0925 \u092a\u094d\u0930\u093e\u092a\u094d\u0924 \u0915\u0930\u0924\u0947 \u0939\u0948\u0902\u0964",
    "welcome.citationGrounding": "\u0939\u0935\u093e\u0932\u093e \u092a\u094d\u0930\u0924\u093e\u092a\u093e\u0926\u0928",
    "welcome.citationGroundingDesc": "\u0939\u0930 \u091c\u0935\u093e\u092c \u0938\u094d\u0930\u094b\u0924 \u0938\u093e\u092e\u0917\u094d\u0930\u093f\u092f\u094b\u0902 \u0938\u0947 \u091c\u093e0901\u091a\u093f\u0924 \u0915\u093f\u092f\u093e \u091c\u093e\u0924\u093e \u0939\u0948\u0964 \u0905\u092a\u094d\u0930\u092e\u093e\u0923\u093f\u0924 \u0926\u093e\u0935\u0947\u0914\u0902 \u0915\u094b \u0920\u0941\u0939\u0930\u093e \u091c\u093e\u0924\u093e \u0939\u0948, \u0905\u0928\u0941\u092e\u093e\u0928\u093f\u0924 \u0928\u0939\u0940\u0902\u0964",
    "welcome.disclaimer": "HECTOR \u0915\u0947\u0935\u0932 \u0915\u093e\u0928\u0942\u0928\u0940 \u092a\u094d\u0930\u0924\u093e\u092a\u093e\u0926\u0928 \u0915\u0947\u0935\u0932 \u0915\u093e\u0928\u0942\u0928\u0940 \u092a\u0941\u0938\u094d\u0924\u093e\u0915\u0924\u093e \u0938\u0947 \u0939\u0940 \u091c\u093e\u0928\u0915\u093e\u0930\u0940 \u0915\u0930\u0924\u093e \u0939\u0948\u0964 \u091c\u0935\u093e\u092c \u0915\u093e\u0928\u0942\u0928\u0940 \u0938\u0932\u093e\u0939 \u0928\u0939\u0940\u0902 \u0939\u0948\u0902\u0964 \u0939\u092e\u0947\u0936\u093e \u0905\u0927\u093f\u0915\u093e\u0930 \u0935\u0915\u0940\u0932 \u0938\u0947 \u0938\u092e\u094d\u0921\u093c \u0932\u0947\u0902\u0964",

    // Processing
    "processing.query": "\u0906\u092a\u0915\u0940 \u0915\u094d\u0935\u0947\u0936",

    // Comparison
    "compare.title": "IPC \u2194 BNS \u0924\u0941\u0932\u0928\u093e",
    "compare.subtitle": "\u0905\u0927\u093f\u0928\u093f\u092f\u094b\u0902 \u092e\u0947\u0902 \u0924\u0941\u0932\u0928\u093e \u0915\u0930\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u092f\u0939\u093e\u0901 \u0928\u0902\u092c\u0930 \u0926\u0930\u094d\u091c \u0915\u0930\u0947\u0902",
    "compare.results": "\u092a\u0930\u093f\u0923\u093e\u092e",
    "compare.noResults": "\u0915\u094b\u0908 \u092a\u0930\u093f\u0923\u093e\u092e \u0928\u0939\u0940\u0902 \u092e\u093f\u0932\u093e",
    "compare.loading": "\u0924\u0941\u0932\u0928\u093e \u0939\u094b \u0930\u0939\u093e \u0939\u0948...",

    // Response
    "response.query": "\u0915\u094d\u0935\u0947\u0936",
    "response.response": "\u091c\u0935\u093e\u092c",
    "response.confidence": "\u0935\u093f\u0936\u094d\u0935\u093e\u0938",
    "response.sources": "\u0938\u094d\u0930\u094b\u0924 \u0926\u0938\u094d\u0924\u093e\u0935\u0947\u091c\u093c",
    "response.citationGrounding": "\u0939\u0935\u093e\u0932\u093e \u092a\u094d\u0930\u0924\u093e\u092a\u093e\u0926\u0928",
    "response.note": "\u0928\u094b\u091f: \u092f\u0939 \u0915\u0947\u0935\u0932 \u091c\u093e\u0928\u0915\u093e\u0930\u0940 \u0909\u0926\u094d\u0926\u0947\u0936 \u0915\u0947 \u0932\u093f\u090f \u0939\u0948 \u0914\u0930 \u0915\u093e\u0928\u0942\u0928\u0940 \u0938\u0932\u093e\u0939 \u0928\u0939\u0940\u0902 \u0939\u0948\u0964",

    // Features
    "features.criminal": "\u0906\u092a\u0930\u093e\u0927",
    "features.civil": "\u0926\u0940\u0935\u092f\u0940\u092f",
    "features.procedural": "\u092a\u094d\u0930\u0915\u093f\u0930\u093f\u092f",
  },
};

export default translations;
