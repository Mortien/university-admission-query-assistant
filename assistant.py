"""Admission question matching using Sentence Transformers when available."""
from __future__ import annotations

import re
from typing import Any

try:
    import nltk
    from nltk.tokenize import wordpunct_tokenize
except ImportError:  # Keep the app usable if the local NLTK/regex install is damaged.
    nltk = None
    wordpunct_tokenize = None

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # A lexical fallback keeps the demo runnable without model packages.
    SentenceTransformer = None
    cosine_similarity = None


def _tokens(text: str) -> set[str]:
    try:
        words = wordpunct_tokenize(text.lower()) if wordpunct_tokenize else re.findall(r"[a-z0-9]+", text.lower())
    except (LookupError, ImportError):
        words = re.findall(r"[a-z0-9]+", text.lower())
    try:
        stopwords = set(nltk.corpus.stopwords.words("english")) if nltk else set()
    except (LookupError, ImportError, AttributeError):
        stopwords = {"a", "an", "the", "is", "are", "do", "does", "i", "how", "what", "when", "for", "to", "of", "in", "and", "can", "my"}
    return {word for word in words if word.isalnum() and word not in stopwords}


class AdmissionAssistant:
    def __init__(self, repository: Any) -> None:
        self.repository = repository
        self.model = None
        self.entries: list[dict[str, Any]] = []
        self.entry_embeddings = None
        self.refresh()

    def refresh(self) -> None:
        self.entries = self.repository.all_faqs()
        if SentenceTransformer and self.entries:
            try:
                model_name = __import__("os").getenv("SENTENCE_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
                self.model = SentenceTransformer(model_name)
                texts = [f"{entry['question']} {entry.get('keywords', '')}" for entry in self.entries]
                self.entry_embeddings = self.model.encode(texts, normalize_embeddings=True)
            except Exception:
                # The model is downloaded on first use; lexical matching works offline.
                self.model = self.entry_embeddings = None

    def answer(self, question: str) -> dict[str, Any]:
        courses = self.repository.all_courses()
        normalized_question = re.sub(r"[^a-z0-9]+", " ", question.lower()).strip()
        matched_course = next((course for course in courses if re.sub(r"[^a-z0-9]+", " ", course["name"].lower()).strip() in normalized_question), None)
        if matched_course:
            course = matched_course
            answer = (f"{course['name']} is a {course['degree_level'].lower()} programme lasting {course['duration']}. "
                      f"The sample annual tuition fee is {course['currency']} {float(course['annual_fee']):,.0f}. "
                      "Check the official fee schedule for the current amount and any additional charges.")
            return {"answer": answer, "category": "Courses and Fees", "confidence": 1.0, "matched": True, "source_question": course["name"]}
        if any(term in normalized_question.split() for term in ("courses", "course", "programmes", "programs")):
            listing = "; ".join(f"{course['name']} ({course['currency']} {float(course['annual_fee']):,.0f}/year)" for course in courses)
            if listing:
                return {"answer": "Available demo courses and sample annual fees: " + listing + ". Replace these sample amounts with the university's official fees.", "category": "Courses and Fees", "confidence": 1.0, "matched": True, "source_question": "Course catalog"}
        if not self.entries:
            return {"answer": "Admission information is not available yet.", "category": None, "confidence": 0.0, "matched": False}
        scores: list[float]
        if self.model is not None and self.entry_embeddings is not None:
            query_embedding = self.model.encode([question], normalize_embeddings=True)
            scores = cosine_similarity(query_embedding, self.entry_embeddings)[0].tolist()
        else:
            query = _tokens(question)
            scores = []
            for item in self.entries:
                candidate = _tokens(f"{item['question']} {item.get('keywords', '')}")
                scores.append(len(query & candidate) / max(1, len(query | candidate)))
        best_index = max(range(len(scores)), key=scores.__getitem__)
        best = self.entries[best_index]
        confidence = float(scores[best_index])
        threshold = float(__import__("os").getenv("MATCH_THRESHOLD", "0.28"))
        matched = confidence >= threshold
        return {
            "answer": best["answer"] if matched else "I couldn't find a confident match. Try asking about eligibility, courses, fees, dates, documents, or the application process.",
            "category": best["category"] if matched else None,
            "confidence": round(confidence, 3),
            "matched": matched,
            "source_question": best["question"] if matched else None,
        }
