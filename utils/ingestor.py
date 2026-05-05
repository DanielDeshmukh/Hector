import os
import chromadb
from chromadb.utils import embedding_functions
import uuid

class HectorMemory:
    def __init__(self):
        # Local storage directory for the vector DB
        self.client = chromadb.PersistentClient(path="./hector_db")
        # Using a reliable local embedding function
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="indian_law_bns",
            embedding_function=self.embedding_fn
        )

    def add_legal_context(self, text, metadata):
        """Adds a chunk of law to the vector database."""
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())]
        )
        print(f"[MEMORY] Ingested: {metadata.get('section', 'Unknown Section')}")

    def semantic_search(self, query, n_results=5):
        """Finds the top N relevant chunks for the reranker to evaluate."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results['documents'][0] # Returns list of text chunks

# Example usage for your first manual ingestion
if __name__ == "__main__":
    memory = HectorMemory()
    # Let's prime it with the theft law you've been testing
    memory.add_legal_context(
        text="Section 303 of BNS: Punishment for theft. Whoever commits theft shall be punished with imprisonment of either description for a term which may extend to three years, or with fine, or with both.",
        metadata={"section": "303", "act": "BNS", "category": "Theft"}
    )