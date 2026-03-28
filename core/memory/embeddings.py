"""
Simple Embeddings Generator
Creates vector embeddings for semantic similarity search
Uses TF-IDF-like approach (no external ML dependencies)

Production: Replace with OpenAI embeddings or BERT model
"""

import logging
from typing import List, Dict, Any
import math
from collections import Counter
import re


logger = logging.getLogger(__name__)


class SimpleEmbedding:
    """
    Simple embedding generator using TF-IDF-like approach
    Good enough for semantic similarity, lightweight, no dependencies
    
    For production: Replace with:
    - OpenAI embeddings (ada model)
    - Hugging Face transformers
    - BERT sentence embeddings
    """
    
    # Common words to ignore
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "at", "to", "for",
        "of", "with", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "can", "by", "from",
        "up", "about", "into", "through", "during", "before", "after",
        "above", "below", "between", "under", "again", "further", "then",
        "once", "on", "off", "out", "as", "if", "it", "its", "itself",
    }
    
    def __init__(self):
        """Initialize embedding generator"""
        self._vocabulary: Dict[str, int] = {}  # word -> index
        self._word_counts: Counter = Counter()
        self._document_count = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        # to lowercase, split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        # Filter out stopwords and short words
        tokens = [t for t in tokens if t not in self.STOPWORDS and len(t) > 2]
        return tokens
    
    def _build_vocabulary(self, texts: List[str]) -> None:
        """Build vocabulary from texts"""
        all_tokens = set()
        
        for text in texts:
            tokens = self._tokenize(text)
            all_tokens.update(tokens)
            self._word_counts.update(tokens)
        
        self._vocabulary = {word: idx for idx, word in enumerate(sorted(all_tokens))}
        self._document_count = len(texts)
        
        logger.info(f"Built vocabulary with {len(self._vocabulary)} unique words")
    
    def _get_idf(self, word: str, doc_count: int) -> float:
        """Calculate IDF (inverse document frequency)"""
        if word not in self._word_counts:
            return 0.0
        
        # Count documents containing word (approximate)
        df = max(1, self._word_counts[word] // 5)  # Simple approximation
        idf = math.log(doc_count / df) if df > 0 else 0
        return idf
    
    def embed(self, text: str) -> List[float]:
        """
        Create embedding vector for text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats (embedding vector)
        """
        if not self._vocabulary:
            # No vocabulary built yet, return simple hash-based embedding
            return self._simple_embed(text)
        
        tokens = self._tokenize(text)
        
        # TF-IDF vector
        vector = [0.0] * len(self._vocabulary)
        
        for token in tokens:
            if token in self._vocabulary:
                idx = self._vocabulary[token]
                # TF: count of term
                tf = tokens.count(token) / (len(tokens) + 1)
                # IDF
                idf = self._get_idf(token, self._document_count)
                # TF-IDF
                vector[idx] = tf * idf
        
        # Normalize vector
        magnitude = math.sqrt(sum(v**2 for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector
    
    def _simple_embed(self, text: str) -> List[float]:
        """Fallback: simple hash-based embedding"""
        tokens = self._tokenize(text)
        
        # Hash-based features
        vector = [
            len(tokens) / 100.0,  # Document length
            sum(len(t) for t in tokens) / len(tokens) if tokens else 0,  # Avg word len
            hash(text) % 100 / 100.0,  # Simple hash feature
        ]
        
        return vector
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: Vector 1
            vec2: Vector 2
            
        Returns:
            Similarity score (0-1, higher=more similar)
        """
        if not vec1 or not vec2:
            return 0.0
        
        # Ensure same length
        len1, len2 = len(vec1), len(vec2)
        if len1 != len2:
            # Pad shorter vector
            if len1 < len2:
                vec1 = vec1 + [0.0] * (len2 - len1)
            else:
                vec2 = vec2 + [0.0] * (len1 - len2)
        
        # Cosine similarity
        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a**2 for a in vec1))
        mag2 = math.sqrt(sum(b**2 for b in vec2))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        similarity = dot / (mag1 * mag2)
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]


def batch_embed(texts: List[str]) -> List[List[float]]:
    """
    Embed multiple texts at once
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    embedder = SimpleEmbedding()
    
    # Build vocabulary from all texts
    if texts:
        embedder._build_vocabulary(texts)
    
    return [embedder.embed(text) for text in texts]
