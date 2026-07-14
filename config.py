"""
Centralized configuration for the Reddit Sentiment Analysis Pipeline.

Loads settings from environment variables (.env file) with sensible defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# =============================================================================
# Reddit API Configuration
# =============================================================================
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "")
REDDIT_USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT",
    "sentiment-analysis-pipeline v1.0 by /u/default_user"
)

# =============================================================================
# Database Configuration
# =============================================================================
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/reddit_sentiment.db")

# =============================================================================
# Pipeline Configuration
# =============================================================================
TARGET_SUBREDDITS = os.getenv("TARGET_SUBREDDITS", "technology,programming,news").split(",")
POSTS_PER_SUBREDDIT = int(os.getenv("POSTS_PER_SUBREDDIT", "50"))
PIPELINE_INTERVAL = int(os.getenv("PIPELINE_INTERVAL", "300"))  # seconds

# =============================================================================
# Sentiment Analysis Configuration
# =============================================================================
VADER_WEIGHT = 0.6       # Weight for VADER compound score in combined sentiment
TEXTBLOB_WEIGHT = 0.4    # Weight for TextBlob polarity in combined sentiment
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05

# =============================================================================
# Keyword Extraction Configuration
# =============================================================================
TOP_N_KEYWORDS = 20       # Number of top keywords to extract per batch
MIN_KEYWORD_LENGTH = 3    # Minimum keyword character length
