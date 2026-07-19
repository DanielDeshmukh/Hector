import unittest

from data.hybrid_retriever import HectorHybridRetriever


class HybridRetrieverTests(unittest.TestCase):
    def setUp(self):
        records = [
            {
                "id": "bns-356",
                "document": "Section 356 BNS Defamation and publication of imputations harming reputation.",
                "metadata": {
                    "source": "fixed_Bharatiya_Nyaya_Sanhita.pdf",
                    "page": 220,
                    "page_hash": "hash-bns-356",
                },
            },
            {
                "id": "ipc-499",
                "document": "Section 499 IPC Defamation. Whoever by words spoken or intended to be read harms reputation.",
                "metadata": {
                    "source": "fixed_Indian_Penal_Code.pdf",
                    "page": 310,
                    "page_hash": "hash-ipc-499",
                },
            },
            {
                "id": "bnss-12",
                "document": "Section 12 BNSS concerns magistrates and criminal procedure administration.",
                "metadata": {
                    "source": "fixed_Bharatiya_Nagarik_Suraksha_Sanhita.pdf",
                    "page": 12,
                    "page_hash": "hash-bnss-12",
                },
            },
            {
                "id": "dup-bns-356",
                "document": "Section 356 BNS Defamation and publication of imputations harming reputation.",
                "metadata": {
                    "source": "fixed_Bharatiya_Nyaya_Sanhita.pdf",
                    "page": 220,
                    "page_hash": "hash-bns-356",
                },
            },
        ]
        self.retriever = HectorHybridRetriever.from_records(records)

    def test_parse_query_extracts_section_and_act(self):
        parsed = self.retriever._parse_query("Explain Section 356 BNS on defamation")

        self.assertEqual(parsed["section_numbers"], ["356"])
        self.assertEqual(parsed["acts"], ["BNS"])
        self.assertTrue(parsed["has_legal_citation"])

    def test_search_prefers_exact_bns_citation(self):
        self.retriever._semantic_search = lambda query, top_k: [
            {
                "id": "ipc-499",
                "document": self.retriever.records[1]["document"],
                "metadata": self.retriever.records[1]["metadata"],
                "distance": 0.05,
                "rank": 1,
            },
            {
                "id": "bns-356",
                "document": self.retriever.records[0]["document"],
                "metadata": self.retriever.records[0]["metadata"],
                "distance": 0.08,
                "rank": 2,
            },
        ]

        results = self.retriever.search("Section 356 BNS defamation", top_k=3)

        self.assertEqual(results[0]["id"], "bns-356")
        self.assertIn("citation-match:BNS-356", results[0]["reasons"])

    def test_search_deduplicates_same_page_hash(self):
        self.retriever._semantic_search = lambda query, top_k: [
            {
                "id": "bns-356",
                "document": self.retriever.records[0]["document"],
                "metadata": self.retriever.records[0]["metadata"],
                "distance": 0.04,
                "rank": 1,
            },
            {
                "id": "dup-bns-356",
                "document": self.retriever.records[3]["document"],
                "metadata": self.retriever.records[3]["metadata"],
                "distance": 0.06,
                "rank": 2,
            },
        ]

        results = self.retriever.search("Section 356 BNS defamation", top_k=5)
        ids = [item["id"] for item in results]

        self.assertEqual(ids.count("bns-356") + ids.count("dup-bns-356"), 1)

    def test_jurisdiction_and_recency_boost_uses_metadata(self):
        record = {
            "document": "Example judgment text.",
            "metadata": {
                "jurisdiction": "Supreme Court",
                "decision_date": "2026-01-01",
            },
        }

        boost, reason = self.retriever._jurisdiction_recency_boost(record)

        self.assertGreaterEqual(boost, 0.03)
        self.assertIn("jurisdiction:sc", reason)
        self.assertIn("recency:2026-01-01", reason)


if __name__ == "__main__":
    unittest.main()
