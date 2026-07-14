"""
Sentiment Analysis Engine for the Reddit Sentiment Analysis Pipeline.

Performs dual sentiment analysis using:
- VADER (Valence Aware Dictionary and sEntiment Reasoner) — optimized for
  social media text, handles emojis, slang, capitalization, and punctuation.
- TextBlob — general-purpose sentiment analysis providing polarity and
  subjectivity scores.

Also extracts keywords using TF-IDF vectorization.
"""

import re
import logging
from typing import Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Dual sentiment analyzer combining VADER and TextBlob."""

    def __init__(
        self,
        vader_weight: float = 0.6,
        textblob_weight: float = 0.4,
        positive_threshold: float = 0.05,
        negative_threshold: float = -0.05,
    ):
        """
        Initialize the SentimentAnalyzer.

        Args:
            vader_weight: Weight for VADER compound score in combined calculation.
            textblob_weight: Weight for TextBlob polarity in combined calculation.
            positive_threshold: Threshold above which sentiment is POSITIVE.
            negative_threshold: Threshold below which sentiment is NEGATIVE.
        """
        self.vader = SentimentIntensityAnalyzer()
        self.vader_weight = vader_weight
        self.textblob_weight = textblob_weight
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold

        # TF-IDF vectorizer for keyword extraction
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words="english",
            min_df=1,
            max_df=0.95,
            ngram_range=(1, 2),  # Unigrams and bigrams
        )

        logger.info(
            f"SentimentAnalyzer initialized "
            f"(VADER weight={vader_weight}, TextBlob weight={textblob_weight})"
        )

    @staticmethod
    def preprocess_text(text: str) -> str:
        """
        Clean and preprocess text for sentiment analysis.

        - Removes URLs
        - Removes special characters (preserving emojis for VADER)
        - Strips excess whitespace
        - Converts to lowercase

        Args:
            text: Raw text input.

        Returns:
            Cleaned text string.
        """
        if not text:
            return ""

        # Remove URLs
        text = re.sub(r"http\S+|www\.\S+", "", text)
        # Remove Reddit-specific formatting
        text = re.sub(r"\[.*?\]\(.*?\)", "", text)   # Remove markdown links
        text = re.sub(r"[#*>~`]", "", text)           # Remove markdown formatting chars
        # Remove special characters but keep emojis and basic punctuation
        text = re.sub(r"[^\w\s!?.,;:'\"-]", " ", text)
        # Collapse multiple whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def analyze_vader(self, text: str) -> dict:
        """
        Run VADER sentiment analysis on text.

        VADER is specifically attuned to social media sentiments. It handles:
        - Emoticons and emojis
        - Slang and abbreviations
        - Capitalization emphasis (e.g., "GREAT" vs "great")
        - Punctuation emphasis (e.g., "!!!")
        - Degree modifiers ("extremely", "slightly")
        - Negation ("not good")
        - Conjunctions ("but")

        Args:
            text: Text to analyze.

        Returns:
            Dict with keys: compound, pos, neg, neu (all floats).
        """
        scores = self.vader.polarity_scores(text)
        return {
            "compound": scores["compound"],   # -1 (most negative) to 1 (most positive)
            "pos": scores["pos"],             # Proportion of positive text
            "neg": scores["neg"],             # Proportion of negative text
            "neu": scores["neu"],             # Proportion of neutral text
        }

    def analyze_textblob(self, text: str) -> dict:
        """
        Run TextBlob sentiment analysis on text.

        TextBlob provides:
        - Polarity: -1.0 (negative) to 1.0 (positive)
        - Subjectivity: 0.0 (objective) to 1.0 (subjective)

        Args:
            text: Text to analyze.

        Returns:
            Dict with keys: polarity, subjectivity (both floats).
        """
        blob = TextBlob(text)
        return {
            "polarity": blob.sentiment.polarity,
            "subjectivity": blob.sentiment.subjectivity,
        }

    def classify_sentiment(self, combined_score: float) -> str:
        """
        Classify a combined score into POSITIVE, NEGATIVE, or NEUTRAL.

        Args:
            combined_score: The weighted average of VADER and TextBlob.

        Returns:
            String: "POSITIVE", "NEGATIVE", or "NEUTRAL".
        """
        if combined_score > self.positive_threshold:
            return "POSITIVE"
        elif combined_score < self.negative_threshold:
            return "NEGATIVE"
        else:
            return "NEUTRAL"

    def analyze(self, text: str) -> dict:
        """
        Perform full dual sentiment analysis on a text.

        Combines VADER and TextBlob scores using weighted average:
        combined = (vader_weight * vader_compound) + (textblob_weight * textblob_polarity)

        Args:
            text: Raw text to analyze.

        Returns:
            Dictionary containing all sentiment scores and classification:
            {
                "vader_compound", "vader_positive", "vader_negative", "vader_neutral",
                "textblob_polarity", "textblob_subjectivity",
                "combined_score", "overall_sentiment"
            }
        """
        cleaned = self.preprocess_text(text)

        if not cleaned:
            return {
                "vader_compound": 0.0,
                "vader_positive": 0.0,
                "vader_negative": 0.0,
                "vader_neutral": 1.0,
                "textblob_polarity": 0.0,
                "textblob_subjectivity": 0.0,
                "combined_score": 0.0,
                "overall_sentiment": "NEUTRAL",
            }

        vader_result = self.analyze_vader(cleaned)
        textblob_result = self.analyze_textblob(cleaned)

        # Weighted combined score
        combined = (
            self.vader_weight * vader_result["compound"]
            + self.textblob_weight * textblob_result["polarity"]
        )

        overall = self.classify_sentiment(combined)

        return {
            "vader_compound": round(vader_result["compound"], 4),
            "vader_positive": round(vader_result["pos"], 4),
            "vader_negative": round(vader_result["neg"], 4),
            "vader_neutral": round(vader_result["neu"], 4),
            "textblob_polarity": round(textblob_result["polarity"], 4),
            "textblob_subjectivity": round(textblob_result["subjectivity"], 4),
            "combined_score": round(combined, 4),
            "overall_sentiment": overall,
        }

    def analyze_post(self, post: dict) -> dict:
        """
        Analyze sentiment for a Reddit post by combining title and body text.

        Args:
            post: Dictionary with 'title' and optionally 'selftext' keys.

        Returns:
            Sentiment analysis result dictionary.
        """
        title = post.get("title", "")
        body = post.get("selftext", "")

        # Combine title and body for analysis (title gets more weight via ordering)
        full_text = f"{title}. {body}" if body else title

        return self.analyze(full_text)

    def extract_keywords(
        self, texts: list[str], top_n: int = 20
    ) -> list[dict]:
        """
        Extract top keywords from a collection of texts using TF-IDF.

        Args:
            texts: List of text documents.
            top_n: Number of top keywords to return.

        Returns:
            List of dicts with 'keyword' and 'tfidf_score' keys,
            sorted by score descending.
        """
        if not texts:
            return []

        # Preprocess all texts
        cleaned = [self.preprocess_text(t).lower() for t in texts]
        cleaned = [t for t in cleaned if t]  # Remove empty strings

        if not cleaned:
            return []

        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(cleaned)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()

            # Average TF-IDF score across all documents for each term
            avg_scores = tfidf_matrix.mean(axis=0).A1  # Convert sparse to array

            # Pair feature names with scores and sort
            keyword_scores = [
                {"keyword": name, "tfidf_score": round(float(score), 4)}
                for name, score in zip(feature_names, avg_scores)
                if len(name) >= 3  # Skip very short terms
            ]
            keyword_scores.sort(key=lambda x: x["tfidf_score"], reverse=True)

            return keyword_scores[:top_n]

        except ValueError as e:
            logger.warning(f"TF-IDF extraction failed: {e}")
            return []

    def extract_keywords_for_post(self, post: dict, top_n: int = 10) -> list[dict]:
        """
        Extract keywords for a single post.

        Args:
            post: Dictionary with 'title' and optionally 'selftext' keys.
            top_n: Number of keywords to extract.

        Returns:
            List of keyword dicts.
        """
        title = post.get("title", "")
        body = post.get("selftext", "")
        full_text = f"{title} {body}" if body else title

        if not full_text.strip():
            return []

        return self.extract_keywords([full_text], top_n=top_n)
