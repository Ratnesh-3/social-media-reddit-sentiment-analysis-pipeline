-- =============================================================================
-- Reddit Sentiment Analysis Pipeline — Database Schema
-- =============================================================================
-- SQLite schema for storing Reddit posts, sentiment scores, and keywords.
-- =============================================================================

-- Posts table: stores raw Reddit post data
CREATE TABLE IF NOT EXISTS posts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    reddit_id       TEXT UNIQUE NOT NULL,          -- Reddit's unique post ID (e.g., "t3_abc123")
    subreddit       TEXT NOT NULL,                 -- Subreddit name (without r/ prefix)
    title           TEXT NOT NULL,                 -- Post title
    selftext        TEXT DEFAULT '',               -- Post body text (empty for link posts)
    author          TEXT DEFAULT '[deleted]',      -- Author username
    score           INTEGER DEFAULT 0,             -- Reddit upvote score
    num_comments    INTEGER DEFAULT 0,             -- Number of comments
    url             TEXT DEFAULT '',               -- Post URL
    permalink       TEXT DEFAULT '',               -- Reddit permalink
    created_utc     TIMESTAMP NOT NULL,            -- Original post creation time (UTC)
    ingested_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- When we ingested this post
);

-- Sentiment scores table: stores analysis results for each post
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id                 INTEGER NOT NULL,              -- FK to posts.id
    vader_compound          REAL DEFAULT 0.0,              -- VADER compound score (-1 to 1)
    vader_positive          REAL DEFAULT 0.0,              -- VADER positive proportion
    vader_negative          REAL DEFAULT 0.0,              -- VADER negative proportion
    vader_neutral           REAL DEFAULT 0.0,              -- VADER neutral proportion
    textblob_polarity       REAL DEFAULT 0.0,              -- TextBlob polarity (-1 to 1)
    textblob_subjectivity   REAL DEFAULT 0.0,              -- TextBlob subjectivity (0 to 1)
    combined_score          REAL DEFAULT 0.0,              -- Weighted combined score
    overall_sentiment       TEXT DEFAULT 'NEUTRAL',        -- POSITIVE, NEGATIVE, or NEUTRAL
    analyzed_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- Keywords table: stores extracted keywords from posts
CREATE TABLE IF NOT EXISTS keywords (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id         INTEGER NOT NULL,              -- FK to posts.id
    keyword         TEXT NOT NULL,                 -- Extracted keyword
    tfidf_score     REAL DEFAULT 0.0,              -- TF-IDF importance score
    extracted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- =============================================================================
-- Indexes for query performance
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit);
CREATE INDEX IF NOT EXISTS idx_posts_created_utc ON posts(created_utc);
CREATE INDEX IF NOT EXISTS idx_posts_reddit_id ON posts(reddit_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_post_id ON sentiment_scores(post_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_overall ON sentiment_scores(overall_sentiment);
CREATE INDEX IF NOT EXISTS idx_sentiment_analyzed_at ON sentiment_scores(analyzed_at);
CREATE INDEX IF NOT EXISTS idx_keywords_post_id ON keywords(post_id);
CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);
