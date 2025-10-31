"""
Hybrid Search Service
Combines vector similarity with keyword matching for improved search relevance
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import bm25
from sentence_transformers import CrossEncoder

from .qdrant_client import QdrantClient
from .embeddings import EmbeddingsService

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Combined search result with hybrid score"""

    id: str
    content: str
    file_path: str
    start_line: Optional[int]
    end_line: Optional[int]
    vector_score: float
    keyword_score: float
    hybrid_score: float
    metadata: Dict[str, Any]


class HybridSearchService:
    """Hybrid search combining vector and keyword search"""

    def __init__(
        self, qdrant_client: QdrantClient, embeddings_service: EmbeddingsService
    ):
        self.qdrant_client = qdrant_client
        self.embeddings_service = embeddings_service
        self.cross_encoder = None
        self.bm25_index = None
        self.documents = []
        self._initialize_cross_encoder()

    def _initialize_cross_encoder(self):
        """Initialize cross-encoder for re-ranking"""
        try:
            # Use a lightweight cross-encoder for re-ranking
            model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
            self.cross_encoder = CrossEncoder(model_name)
            logger.info(f"✅ Cross-encoder initialized: {model_name}")
        except Exception as e:
            logger.warning(f"⚠️ Cross-encoder initialization failed: {e}")
            self.cross_encoder = None

    async def build_keyword_index(self, documents: List[Dict[str, Any]]):
        """Build BM25 keyword index from documents"""
        try:
            # Extract text content for BM25
            texts = [doc.get("content", "") for doc in documents]
            self.documents = documents

            # Build BM25 index
            self.bm25_index = bm25.BM25Okapi(texts)
            logger.info(f"✅ BM25 index built with {len(documents)} documents")

        except Exception as e:
            logger.error(f"❌ Failed to build BM25 index: {e}")
            self.bm25_index = None

    async def keyword_search(
        self, query: str, top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """Search using BM25 keyword matching"""
        if not self.bm25_index:
            return []

        try:
            # Tokenize query
            tokenized_query = query.lower().split()

            # Get BM25 scores
            scores = self.bm25_index.get_scores(tokenized_query)

            # Get top-k results
            top_indices = np.argsort(scores)[::-1][:top_k]
            results = [
                (int(idx), float(scores[idx])) for idx in top_indices if scores[idx] > 0
            ]

            return results

        except Exception as e:
            logger.error(f"❌ Keyword search failed: {e}")
            return []

    async def vector_search(
        self, query: str, collection_name: str, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search using vector similarity"""
        try:
            # Generate query embedding
            query_vector = self.embeddings_service.embed_query(query)

            # Search Qdrant
            results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=0.3,  # Lower threshold for hybrid search
            )

            return results

        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return []

    def normalize_scores(
        self, vector_scores: List[float], keyword_scores: List[float]
    ) -> Tuple[List[float], List[float]]:
        """Normalize scores to 0-1 range for combination"""

        def normalize(scores):
            if not scores:
                return []
            min_score, max_score = min(scores), max(scores)
            if max_score == min_score:
                return [1.0] * len(scores)
            return [(s - min_score) / (max_score - min_score) for s in scores]

        return normalize(vector_scores), normalize(keyword_scores)

    async def reciprocal_rank_fusion(
        self,
        vector_results: List[Dict],
        keyword_results: List[Tuple[int, float]],
        k: int = 60,
    ) -> List[Dict]:
        """Combine results using reciprocal rank fusion"""
        # Create document lookup
        doc_lookup = {}
        for doc in self.documents:
            doc_lookup[doc["id"]] = doc

        # Score dictionaries
        fusion_scores = {}

        # Add vector search results
        for rank, result in enumerate(vector_results[:k]):
            doc_id = result["id"]
            fusion_scores[doc_id] = fusion_scores.get(doc_id, 0) + 1.0 / (k + rank + 1)

        # Add keyword search results
        for rank, (doc_idx, score) in enumerate(keyword_results[:k]):
            if doc_idx < len(self.documents):
                doc_id = self.documents[doc_idx]["id"]
                fusion_scores[doc_id] = fusion_scores.get(doc_id, 0) + 1.0 / (
                    k + rank + 1
                )

        # Sort by fusion score
        ranked_docs = sorted(fusion_scores.items(), key=lambda x: x[1], reverse=True)

        # Create result documents
        combined_results = []
        for doc_id, fusion_score in ranked_docs:
            if doc_id in doc_lookup:
                doc = doc_lookup[doc_id].copy()
                doc["hybrid_score"] = fusion_score
                combined_results.append(doc)

        return combined_results

    async def hybrid_search(
        self, query: str, collection_name: str, top_k: int = 10
    ) -> List[SearchResult]:
        """Perform hybrid search combining vector and keyword matching"""
        try:
            logger.info(f"🔍 Performing hybrid search: '{query}'")

            # Step 1: Vector search
            vector_results = await self.vector_search(query, collection_name, top_k * 2)
            logger.info(f"  📊 Vector search: {len(vector_results)} results")

            # Step 2: Keyword search
            keyword_results = await self.keyword_search(query, top_k * 2)
            logger.info(f"  🔤 Keyword search: {len(keyword_results)} results")

            # Step 3: Combine results using reciprocal rank fusion
            combined_results = await self.reciprocal_rank_fusion(
                vector_results, keyword_results
            )
            logger.info(f"  🔄 Combined results: {len(combined_results)}")

            # Step 4: Re-rank with cross-encoder if available
            if self.cross_encoder and len(combined_results) > 1:
                combined_results = await self.rerank_with_cross_encoder(
                    query, combined_results, top_k
                )
                logger.info(f"  🎯 Re-ranked to: {len(combined_results)} results")

            # Step 5: Convert to SearchResult objects
            search_results = []
            for i, result in enumerate(combined_results[:top_k]):
                # Find original scores
                vector_score = 0.0
                keyword_score = 0.0

                for vr in vector_results:
                    if vr["id"] == result["id"]:
                        vector_score = vr["score"]
                        break

                for kr_idx, kr_score in keyword_results:
                    if (
                        kr_idx < len(self.documents)
                        and self.documents[kr_idx]["id"] == result["id"]
                    ):
                        keyword_score = kr_score
                        break

                search_result = SearchResult(
                    id=result["id"],
                    content=result.get("content", ""),
                    file_path=result.get("file_path", ""),
                    start_line=result.get("start_line"),
                    end_line=result.get("end_line"),
                    vector_score=vector_score,
                    keyword_score=keyword_score,
                    hybrid_score=result.get("hybrid_score", 0.0),
                    metadata=result.get("metadata", {}),
                )
                search_results.append(search_result)

            logger.info(
                f"✅ Hybrid search completed: {len(search_results)} final results"
            )
            return search_results

        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            return []

    async def rerank_with_cross_encoder(
        self, query: str, documents: List[Dict], top_k: int
    ) -> List[Dict]:
        """Re-rank documents using cross-encoder"""
        try:
            # Prepare input pairs for cross-encoder
            pairs = [
                [query, doc.get("content", "")] for doc in documents[:50]
            ]  # Limit for performance

            # Get cross-encoder scores
            scores = self.cross_encoder.predict(pairs)

            # Add scores to documents and sort
            for i, doc in enumerate(documents[: len(scores)]):
                doc["cross_encoder_score"] = float(scores[i])

            # Sort by cross-encoder score
            documents.sort(key=lambda x: x.get("cross_encoder_score", 0), reverse=True)

            return documents[:top_k]

        except Exception as e:
            logger.warning(f"⚠️ Cross-encoder re-ranking failed: {e}")
            return documents[:top_k]

    async def expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms"""
        expanded_queries = [query]

        try:
            # Simple expansion rules (can be enhanced with LLM)
            expansions = {
                "function": ["method", "procedure", "func", "def"],
                "class": ["object", "type", "struct"],
                "variable": ["var", "field", "property"],
                "error": ["exception", "issue", "problem", "bug"],
                "test": ["testing", "spec", "validation"],
                "api": ["interface", "endpoint", "service"],
                "database": ["db", "storage", "data store"],
                "config": ["configuration", "settings", "options"],
                "deploy": ["deployment", "release", "publish"],
            }

            # Add expansions for common terms
            words = query.lower().split()
            for word in words:
                if word in expansions:
                    for expansion in expansions[word]:
                        expanded_query = query.replace(word, expansion, 1)
                        expanded_queries.append(expanded_query)

            # Remove duplicates while preserving order
            seen = set()
            unique_expanded = []
            for q in expanded_queries:
                if q not in seen:
                    seen.add(q)
                    unique_expanded.append(q)

            logger.info(f"🔍 Query expansion: {len(unique_expanded)} variants")
            return unique_expanded

        except Exception as e:
            logger.warning(f"⚠️ Query expansion failed: {e}")
            return [query]

    async def search_with_expansion(
        self, query: str, collection_name: str, top_k: int = 10
    ) -> List[SearchResult]:
        """Search with query expansion"""
        try:
            # Get expanded queries
            expanded_queries = await self.expand_query(query)

            all_results = []
            seen_ids = set()

            # Search each query variant
            for expanded_query in expanded_queries:
                results = await self.hybrid_search(
                    expanded_query, collection_name, top_k
                )

                # Add unique results
                for result in results:
                    if result.id not in seen_ids:
                        seen_ids.add(result.id)
                        all_results.append(result)

            # Sort by hybrid score and limit
            all_results.sort(key=lambda x: x.hybrid_score, reverse=True)

            logger.info(
                f"🔍 Expanded search: {len(all_results)} unique results from {len(expanded_queries)} queries"
            )
            return all_results[:top_k]

        except Exception as e:
            logger.error(f"❌ Expanded search failed: {e}")
            return await self.hybrid_search(query, collection_name, top_k)
