"""
Re-ranking Service
Advanced re-ranking algorithms for improved search relevance
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from sentence_transformers import CrossEncoder, SentenceTransformer
import torch

from .hybrid_search import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class ReRankedResult:
    """Re-ranked search result with confidence scores"""

    original_result: SearchResult
    rerank_score: float
    confidence: float
    relevance_features: Dict[str, float]


class ReRankingService:
    """Advanced re-ranking service for search results"""

    def __init__(self):
        self.cross_encoder = None
        self.sentence_model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialize_models()

    def _initialize_models(self):
        """Initialize re-ranking models"""
        try:
            # Initialize cross-encoder for relevance scoring
            self.cross_encoder = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2", device=self.device
            )
            logger.info(f"✅ Cross-encoder initialized on {self.device}")

            # Initialize sentence transformer for semantic similarity
            self.sentence_model = SentenceTransformer(
                "all-MiniLM-L6-v2", device=self.device
            )
            logger.info(f"✅ Sentence transformer initialized on {self.device}")

        except Exception as e:
            logger.error(f"❌ Model initialization failed: {e}")
            self.cross_encoder = None
            self.sentence_model = None

    async def rerank_results(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 10,
        method: str = "hybrid",
    ) -> List[ReRankedResult]:
        """Re-rank search results using specified method"""
        if not results:
            return []

        logger.info(f"🎯 Re-ranking {len(results)} results using {method} method")

        try:
            if method == "cross_encoder" and self.cross_encoder:
                return await self._rerank_with_cross_encoder(query, results, top_k)
            elif method == "semantic_similarity" and self.sentence_model:
                return await self._rerank_with_semantic_similarity(
                    query, results, top_k
                )
            elif method == "feature_based":
                return await self._rerank_with_features(query, results, top_k)
            elif method == "hybrid":
                return await self._hybrid_rerank(query, results, top_k)
            else:
                logger.warning(f"⚠️ Unknown reranking method: {method}")
                return await self._basic_rerank(results, top_k)

        except Exception as e:
            logger.error(f"❌ Re-ranking failed: {e}")
            return await self._basic_rerank(results, top_k)

    async def _rerank_with_cross_encoder(
        self, query: str, results: List[SearchResult], top_k: int
    ) -> List[ReRankedResult]:
        """Re-rank using cross-encoder relevance scoring"""
        if not self.cross_encoder or len(results) < 2:
            return await self._basic_rerank(results, top_k)

        try:
            # Prepare query-document pairs
            pairs = [[query, result.content] for result in results]

            # Get relevance scores
            scores = self.cross_encoder.predict(pairs)

            # Create re-ranked results
            re_ranked = []
            for i, (result, score) in enumerate(zip(results, scores)):
                confidence = self._calculate_confidence(float(score), len(results))

                re_ranked_result = ReRankedResult(
                    original_result=result,
                    rerank_score=float(score),
                    confidence=confidence,
                    relevance_features={"cross_encoder_score": float(score)},
                )
                re_ranked.append(re_ranked_result)

            # Sort by re-rank score
            re_ranked.sort(key=lambda x: x.rerank_score, reverse=True)

            logger.info("✅ Cross-encoder re-ranking completed")
            return re_ranked[:top_k]

        except Exception as e:
            logger.error(f"❌ Cross-encoder re-ranking failed: {e}")
            return await self._basic_rerank(results, top_k)

    async def _rerank_with_semantic_similarity(
        self, query: str, results: List[SearchResult], top_k: int
    ) -> List[ReRankedResult]:
        """Re-rank using semantic similarity"""
        if not self.sentence_model or len(results) < 2:
            return await self._basic_rerank(results, top_k)

        try:
            # Encode query and documents
            query_embedding = self.sentence_model.encode([query])
            doc_embeddings = self.sentence_model.encode([r.content for r in results])

            # Calculate cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity

            similarities = cosine_similarity(query_embedding, doc_embeddings)[0]

            # Create re-ranked results
            re_ranked = []
            for result, similarity in zip(results, similarities):
                confidence = self._calculate_confidence(float(similarity), len(results))

                re_ranked_result = ReRankedResult(
                    original_result=result,
                    rerank_score=float(similarity),
                    confidence=confidence,
                    relevance_features={"semantic_similarity": float(similarity)},
                )
                re_ranked.append(re_ranked_result)

            # Sort by similarity
            re_ranked.sort(key=lambda x: x.rerank_score, reverse=True)

            logger.info("✅ Semantic similarity re-ranking completed")
            return re_ranked[:top_k]

        except Exception as e:
            logger.error(f"❌ Semantic similarity re-ranking failed: {e}")
            return await self._basic_rerank(results, top_k)

    async def _rerank_with_features(
        self, query: str, results: List[SearchResult], top_k: int
    ) -> List[ReRankedResult]:
        """Re-rank using multiple features"""
        try:
            re_ranked = []

            for result in results:
                # Extract multiple relevance features
                features = await self._extract_relevance_features(query, result)

                # Calculate weighted score
                weights = {
                    "exact_match": 0.3,
                    "keyword_density": 0.2,
                    "position_bonus": 0.15,
                    "length_bonus": 0.1,
                    "file_type_bonus": 0.15,
                    "vector_score": 0.1,
                }

                weighted_score = sum(
                    features.get(feature, 0) * weight
                    for feature, weight in weights.items()
                )

                confidence = self._calculate_confidence(weighted_score, len(results))

                re_ranked_result = ReRankedResult(
                    original_result=result,
                    rerank_score=weighted_score,
                    confidence=confidence,
                    relevance_features=features,
                )
                re_ranked.append(re_ranked_result)

            # Sort by weighted score
            re_ranked.sort(key=lambda x: x.rerank_score, reverse=True)

            logger.info("✅ Feature-based re-ranking completed")
            return re_ranked[:top_k]

        except Exception as e:
            logger.error(f"❌ Feature-based re-ranking failed: {e}")
            return await self._basic_rerank(results, top_k)

    async def _extract_relevance_features(
        self, query: str, result: SearchResult
    ) -> Dict[str, float]:
        """Extract relevance features for a result"""
        features = {}
        query_lower = query.lower()
        content_lower = result.content.lower()

        # Exact match feature
        if query_lower in content_lower:
            features["exact_match"] = 1.0
        else:
            features["exact_match"] = 0.0

        # Keyword density
        query_words = query_lower.split()
        content_words = content_lower.split()
        if content_words:
            matches = sum(1 for word in query_words if word in content_words)
            features["keyword_density"] = matches / len(query_words)
        else:
            features["keyword_density"] = 0.0

        # Position bonus (earlier results get bonus)
        features["position_bonus"] = max(0, 1.0 - (result.start_line / 1000))

        # Length bonus (prefer optimal chunk length)
        optimal_length = 200  # characters
        content_length = len(result.content)
        if content_length <= optimal_length:
            features["length_bonus"] = content_length / optimal_length
        else:
            features["length_bonus"] = optimal_length / content_length

        # File type bonus
        file_ext = result.file_path.lower().split(".")[-1]
        code_extensions = {"py", "js", "ts", "java", "cpp", "c", "go", "rs"}
        if file_ext in code_extensions:
            features["file_type_bonus"] = 1.0
        else:
            features["file_type_bonus"] = 0.8

        # Vector score
        features["vector_score"] = result.vector_score

        return features

    async def _hybrid_rerank(
        self, query: str, results: List[SearchResult], top_k: int
    ) -> List[ReRankedResult]:
        """Hybrid re-ranking combining multiple methods"""
        try:
            # Get scores from different methods
            cross_encoder_scores = []
            semantic_scores = []
            feature_scores = []

            if self.cross_encoder and len(results) > 1:
                cross_encoder_results = await self._rerank_with_cross_encoder(
                    query, results, len(results)
                )
                cross_encoder_scores = [r.rerank_score for r in cross_encoder_results]

            if self.sentence_model and len(results) > 1:
                semantic_results = await self._rerank_with_semantic_similarity(
                    query, results, len(results)
                )
                semantic_scores = [r.rerank_score for r in semantic_results]

            feature_results = await self._rerank_with_features(
                query, results, len(results)
            )
            feature_scores = [r.rerank_score for r in feature_results]

            # Combine scores using weighted average
            re_ranked = []
            for i, result in enumerate(results):
                scores = []
                weights = []

                if cross_encoder_scores:
                    scores.append(cross_encoder_scores[i])
                    weights.append(0.4)  # Cross-encoder has highest weight

                if semantic_scores:
                    scores.append(semantic_scores[i])
                    weights.append(0.3)  # Semantic similarity

                if feature_scores:
                    scores.append(feature_scores[i])
                    weights.append(0.3)  # Feature-based

                # Calculate weighted average
                if scores:
                    weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(
                        weights
                    )
                else:
                    weighted_score = result.hybrid_score

                confidence = self._calculate_confidence(weighted_score, len(results))

                # Combine all features
                all_features = {"hybrid_score": weighted_score}
                if cross_encoder_scores:
                    all_features["cross_encoder_score"] = cross_encoder_scores[i]
                if semantic_scores:
                    all_features["semantic_similarity"] = semantic_scores[i]
                if feature_scores:
                    all_features.update(feature_results[i].relevance_features)

                re_ranked_result = ReRankedResult(
                    original_result=result,
                    rerank_score=weighted_score,
                    confidence=confidence,
                    relevance_features=all_features,
                )
                re_ranked.append(re_ranked_result)

            # Sort by hybrid score
            re_ranked.sort(key=lambda x: x.rerank_score, reverse=True)

            logger.info("✅ Hybrid re-ranking completed")
            return re_ranked[:top_k]

        except Exception as e:
            logger.error(f"❌ Hybrid re-ranking failed: {e}")
            return await self._basic_rerank(results, top_k)

    async def _basic_rerank(
        self, results: List[SearchResult], top_k: int
    ) -> List[ReRankedResult]:
        """Basic re-ranking using existing scores"""
        re_ranked = []

        for result in results:
            # Use existing hybrid score as rerank score
            confidence = self._calculate_confidence(result.hybrid_score, len(results))

            re_ranked_result = ReRankedResult(
                original_result=result,
                rerank_score=result.hybrid_score,
                confidence=confidence,
                relevance_features={
                    "vector_score": result.vector_score,
                    "keyword_score": result.keyword_score,
                    "hybrid_score": result.hybrid_score,
                },
            )
            re_ranked.append(re_ranked_result)

        # Sort by existing hybrid score
        re_ranked.sort(key=lambda x: x.rerank_score, reverse=True)

        return re_ranked[:top_k]

    def _calculate_confidence(self, score: float, total_results: int) -> float:
        """Calculate confidence score based on score and result count"""
        # Normalize score to 0-1 range
        normalized_score = max(0, min(1, score))

        # Adjust confidence based on result count (more results = lower confidence per result)
        result_factor = 1.0 - (total_results / 100.0)  # Penalize large result sets

        # Combine factors
        confidence = normalized_score * (0.7 + 0.3 * result_factor)

        return max(0.1, min(1.0, confidence))  # Ensure reasonable bounds

    async def diversify_results(
        self,
        results: List[ReRankedResult],
        diversity_threshold: float = 0.7,
        max_results: int = 10,
    ) -> List[ReRankedResult]:
        """Diversify results to avoid redundancy"""
        if len(results) <= 1:
            return results

        try:
            diversified = [results[0]]  # Always keep top result

            for result in results[1:]:
                if len(diversified) >= max_results:
                    break

                # Check similarity with already selected results
                is_similar = False

                for selected in diversified:
                    similarity = await self._calculate_content_similarity(
                        result.original_result.content, selected.original_result.content
                    )

                    if similarity > diversity_threshold:
                        is_similar = True
                        break

                if not is_similar:
                    diversified.append(result)

            logger.info(f"✅ Diversified {len(results)} results to {len(diversified)}")
            return diversified

        except Exception as e:
            logger.error(f"❌ Result diversification failed: {e}")
            return results[:max_results]

    async def _calculate_content_similarity(
        self, content1: str, content2: str
    ) -> float:
        """Calculate semantic similarity between two contents"""
        if not self.sentence_model:
            # Fallback to simple overlap
            words1 = set(content1.lower().split())
            words2 = set(content2.lower().split())
            if not words1 or not words2:
                return 0.0

            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union) if union else 0.0

        try:
            # Use sentence transformer for semantic similarity
            embeddings = self.sentence_model.encode([content1, content2])

            # Calculate cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity

            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

            return float(similarity)

        except Exception:
            # Fallback to word overlap
            words1 = set(content1.lower().split())
            words2 = set(content2.lower().split())
            if not words1 or not words2:
                return 0.0

            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union) if union else 0.0

    async def explain_ranking(self, result: ReRankedResult) -> Dict[str, Any]:
        """Explain why a result was ranked this way"""
        explanation = {
            "final_score": result.rerank_score,
            "confidence": result.confidence,
            "reasoning": [],
        }

        # Analyze each feature
        for feature, value in result.relevance_features.items():
            if feature == "exact_match" and value > 0.5:
                explanation["reasoning"].append("Contains exact query match")
            elif feature == "keyword_density" and value > 0.7:
                explanation["reasoning"].append("High keyword density")
            elif feature == "semantic_similarity" and value > 0.8:
                explanation["reasoning"].append("High semantic similarity")
            elif feature == "cross_encoder_score" and value > 0.7:
                explanation["reasoning"].append("High relevance according to ML model")
            elif feature == "vector_score" and value > 0.7:
                explanation["reasoning"].append("High vector similarity")
            elif feature == "position_bonus" and value > 0.8:
                explanation["reasoning"].append("Found early in document")
            elif feature == "file_type_bonus" and value > 0.9:
                explanation["reasoning"].append("Preferred file type (code)")

        return explanation
