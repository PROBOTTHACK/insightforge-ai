from dataclasses import dataclass
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class VectorDocument:
    id: str
    title: str
    text: str
    metadata: dict[str, Any]


class InMemoryVectorStore:
    def __init__(self, documents: list[VectorDocument]) -> None:
        self.documents = [document for document in documents if document.text.strip()]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform([document.text for document in self.documents]) if self.documents else None

    def search(self, query: str, limit: int = 8) -> list[VectorDocument]:
        if not self.documents or self.matrix is None:
            return []
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).flatten()
        ranked_indexes = scores.argsort()[::-1][:limit]
        return [self.documents[index] for index in ranked_indexes if scores[index] > 0]
