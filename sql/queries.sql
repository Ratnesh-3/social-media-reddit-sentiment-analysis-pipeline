-- =============================================================================
-- Reddit Sentiment Analysis Pipeline — Reusable SQL Queries
-- =============================================================================
-- Analytic queries used by the Streamlit dashboard and pipeline reporting.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Sentiment Distribution by Subreddit
-- ---------------------------------------------------------------------------
-- Returns count of POSITIVE, NEGATIVE, NEUTRAL posts per subreddit
SELECT
    p.subreddit,
    s.overall_sentiment,
    COUNT(*) AS post_count
FROM posts p
JOIN sentiment_scores s ON p.id = s.post_id
GROUP BY p.subreddit, s.overall_sentiment
ORDER BY p.subreddit, s.overall_sentiment;

-- ---------------------------------------------------------------------------
-- 2. Sentiment Trend Over Time (Hourly)
-- ---------------------------------------------------------------------------
-- Returns average sentiment scores grouped by hour
SELECT
    strftime('%Y-%m-%d %H:00:00', p.created_utc) AS time_bucket,
    p.subreddit,
    AVG(s.vader_compound)    AS avg_vader,
    AVG(s.textblob_polarity) AS avg_textblob,
    AVG(s.combined_score)    AS avg_combined,
    COUNT(*)                 AS post_count
FROM posts p
JOIN sentiment_scores s ON p.id = s.post_id
GROUP BY time_bucket, p.subreddit
ORDER BY time_bucket DESC;

-- ---------------------------------------------------------------------------
-- 3. Sentiment Trend Over Time (Daily)
-- ---------------------------------------------------------------------------
SELECT
    strftime('%Y-%m-%d', p.created_utc) AS date_bucket,
    p.subreddit,
    AVG(s.vader_compound)    AS avg_vader,
    AVG(s.textblob_polarity) AS avg_textblob,
    AVG(s.combined_score)    AS avg_combined,
    COUNT(*)                 AS post_count
FROM posts p
JOIN sentiment_scores s ON p.id = s.post_id
GROUP BY date_bucket, p.subreddit
ORDER BY date_bucket DESC;

-- ---------------------------------------------------------------------------
-- 4. Top Keywords by Frequency
-- ---------------------------------------------------------------------------
SELECT
    k.keyword,
    COUNT(*)          AS frequency,
    AVG(k.tfidf_score) AS avg_tfidf
FROM keywords k
GROUP BY k.keyword
ORDER BY frequency DESC
LIMIT 20;

-- ---------------------------------------------------------------------------
-- 5. Top Keywords by TF-IDF Score
-- ---------------------------------------------------------------------------
SELECT
    k.keyword,
    MAX(k.tfidf_score) AS max_tfidf,
    AVG(k.tfidf_score) AS avg_tfidf,
    COUNT(*)            AS occurrences
FROM keywords k
GROUP BY k.keyword
ORDER BY avg_tfidf DESC
LIMIT 20;

-- ---------------------------------------------------------------------------
-- 6. Most Positive Posts
-- ---------------------------------------------------------------------------
SELECT
    p.title,
    p.subreddit,
    p.author,
    p.score       AS reddit_score,
    s.vader_compound,
    s.textblob_polarity,
    s.combined_score,
    s.overall_sentiment,
    p.permalink,
    p.created_utc
FROM posts p
JOIN sentiment_scores s ON p.id = s.post_id
ORDER BY s.combined_score DESC
LIMIT 10;

-- ---------------------------------------------------------------------------
-- 7. Most Negative Posts
-- ---------------------------------------------------------------------------
SELECT
    p.title,
    p.subreddit,
    p.author,
    p.score       AS reddit_score,
    s.vader_compound,
    s.textblob_polarity,
    s.combined_score,
    s.overall_sentiment,
    p.permalink,
    p.created_utc
FROM posts p
JOIN sentiment_scores s ON p.id = s.post_id
ORDER BY s.combined_score ASC
LIMIT 10;

-- ---------------------------------------------------------------------------
-- 8. Average Sentiment by Subreddit
-- ---------------------------------------------------------------------------
SELECT
    p.subreddit,
    ROUND(AVG(s.vader_compound), 4)    AS avg_vader,
    ROUND(AVG(s.textblob_polarity), 4) AS avg_textblob,
    ROUND(AVG(s.combined_score), 4)    AS avg_combined,
    COUNT(*)                           AS total_posts
FROM posts p
JOIN sentiment_scores s ON p.id = s.post_id
GROUP BY p.subreddit
ORDER BY avg_combined DESC;

-- ---------------------------------------------------------------------------
-- 9. Recent Posts with Sentiment (Live Feed)
-- ---------------------------------------------------------------------------
SELECT
    p.title,
    p.subreddit,
    p.author,
    p.score           AS reddit_score,
    p.num_comments,
    s.vader_compound,
    s.textblob_polarity,
    s.combined_score,
    s.overall_sentiment,
    p.permalink,
    p.created_utc,
    s.analyzed_at
FROM posts p
JOIN sentiment_scores s ON p.id = s.post_id
ORDER BY s.analyzed_at DESC
LIMIT 50;

-- ---------------------------------------------------------------------------
-- 10. Pipeline Statistics
-- ---------------------------------------------------------------------------
SELECT
    COUNT(*)                                     AS total_posts,
    COUNT(DISTINCT p.subreddit)                  AS subreddits_tracked,
    MIN(p.created_utc)                           AS earliest_post,
    MAX(p.created_utc)                           AS latest_post,
    SUM(CASE WHEN s.overall_sentiment = 'POSITIVE' THEN 1 ELSE 0 END) AS positive_count,
    SUM(CASE WHEN s.overall_sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) AS negative_count,
    SUM(CASE WHEN s.overall_sentiment = 'NEUTRAL'  THEN 1 ELSE 0 END) AS neutral_count
FROM posts p
JOIN sentiment_scores s ON p.id = s.post_id;
