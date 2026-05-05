# data/hybrid_retriever.py
import os
import json
import numpy as np
from rank_bm25 import BM25Okapi
import chromadb
from chromadb.utils import embedding_functions

class HectorHybridRetriever:
    def __init__(self, collection_name="indian_law_bns"):
        # 1. Semantic Initialization (Vector)
        self.chroma_client = chromadb.PersistentClient(path="./data/hector_db")
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embed_fn
        )
        
        # 2. Keyword Initialization (BM25)
        self.bm25 = None
        self.corpus = []
        self._initialize_bm25()

    def _initialize_bm25(self):
        """Loads all documents from Chroma to build the BM25 index."""
        results = self.collection.get()
        if results['documents']:
            self.corpus = results['documents']
            tokenized_corpus = [doc.lower().split() for doc in self.corpus]
            self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query, top_k=10):
        query_tokens = query.lower().split()
        
        # A. Vector Search (Semantic)
        vector_results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # B. BM25 Search (Exact Keyword)
        if self.bm25:
            bm25_scores = self.bm25.get_scores(query_tokens)
            # Get indices of top scores
            top_bm25_idx = np.argsort(bm25_scores)[-top_k:][::-1]
            bm25_results = [self.corpus[i] for i in top_bm25_idx]
        else:
            bm25_results = []

        # C. Merge and Deduplicate for the Reranker
        # We combine them so the Reranker can sort out the 'truth'
        combined_candidates = list(set(vector_results['documents'][0] + bm25_results))
        
        return combined_candidates

    def refresh_index(self):
        """Call this after ingestion to update the keyword index."""
        self._initialize_bm25()