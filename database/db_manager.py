"""
Database Manager for the Reddit Sentiment Analysis Pipeline.

Handles SQLite database initialization, connection management, and all
CRUD operations for posts, sentiment scores, and keywords.

All queries use parameterized statements (? placeholders) to prevent
SQL injection attacks.
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and operations."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the DatabaseManager.

        Args:
            db_path: Path to the SQLite database file. If None, uses config default.
        """
        if db_path is None:
            from config import DATABASE_PATH
            db_path = DATABASE_PATH

        self.db_path = db_path

        # Ensure the directory for the DB file exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        logger.info(f"DatabaseManager initialized with path: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """
        Create and return a new database connection.

        Returns:
            sqlite3.Connection with row_factory set to sqlite3.Row for
            dictionary-style access.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")    # Write-Ahead Logging for concurrency
        conn.execute("PRAGMA foreign_keys=ON")      # Enforce foreign key constraints
        return conn

    def init_db(self):
        """
        Initialize the database by executing the schema.sql file.

        Creates all tables and indexes if they don't already exist.
        """
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "sql", "schema.sql"
        )

        try:
            with open(schema_path, "r") as f:
                schema_sql = f.read()

            conn = self._get_connection()
            conn.executescript(schema_sql)
            conn.close()
            logger.info("Database initialized successfully.")
        except FileNotFoundError:
            logger.error(f"Schema file not found at: {schema_path}")
            raise
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def insert_post(self, post_data: dict) -> Optional[int]:
        """
        Insert or ignore a Reddit post into the database.

        Uses INSERT OR IGNORE to handle duplicate reddit_id gracefully.

        Args:
            post_data: Dictionary containing post fields:
                - reddit_id, subreddit, title, selftext, author,
                - score, num_comments, url, permalink, created_utc

        Returns:
            The row ID of the inserted post, or None if it was a duplicate.
        """
        sql = """
            INSERT OR IGNORE INTO posts
                (reddit_id, subreddit, title, selftext, author,
                 score, num_comments, url, permalink, created_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            post_data.get("reddit_id"),
            post_data.get("subreddit"),
            post_data.get("title"),
            post_data.get("selftext", ""),
            post_data.get("author", "[deleted]"),
            post_data.get("score", 0),
            post_data.get("num_comments", 0),
            post_data.get("url", ""),
            post_data.get("permalink", ""),
            post_data.get("created_utc"),
        )

        try:
            conn = self._get_connection()
            cursor = conn.execute(sql, params)
            conn.commit()

            if cursor.rowcount > 0:
                post_id = cursor.lastrowid
                logger.debug(f"Inserted post: {post_data.get('reddit_id')} (id={post_id})")
                conn.close()
                return post_id
            else:
                # Duplicate — fetch existing ID
                cursor = conn.execute(
                    "SELECT id FROM posts WHERE reddit_id = ?",
                    (post_data.get("reddit_id"),)
                )
                row = cursor.fetchone()
                conn.close()
                if row:
                    logger.debug(f"Post already exists: {post_data.get('reddit_id')}")
                    return row["id"]
                return None

        except sqlite3.Error as e:
            logger.error(f"Error inserting post {post_data.get('reddit_id')}: {e}")
            return None

    def insert_sentiment(self, post_id: int, sentiment_data: dict) -> Optional[int]:
        """
        Insert sentiment analysis results for a post.

        Args:
            post_id: The database ID of the post.
            sentiment_data: Dictionary containing:
                - vader_compound, vader_positive, vader_negative, vader_neutral
                - textblob_polarity, textblob_subjectivity
                - combined_score, overall_sentiment

        Returns:
            The row ID of the inserted sentiment record, or None on failure.
        """
        sql = """
            INSERT INTO sentiment_scores
                (post_id, vader_compound, vader_positive, vader_negative, vader_neutral,
                 textblob_polarity, textblob_subjectivity, combined_score, overall_sentiment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            post_id,
            sentiment_data.get("vader_compound", 0.0),
            sentiment_data.get("vader_positive", 0.0),
            sentiment_data.get("vader_negative", 0.0),
            sentiment_data.get("vader_neutral", 0.0),
            sentiment_data.get("textblob_polarity", 0.0),
            sentiment_data.get("textblob_subjectivity", 0.0),
            sentiment_data.get("combined_score", 0.0),
            sentiment_data.get("overall_sentiment", "NEUTRAL"),
        )

        try:
            conn = self._get_connection()
            cursor = conn.execute(sql, params)
            conn.commit()
            record_id = cursor.lastrowid
            conn.close()
            logger.debug(f"Inserted sentiment for post_id={post_id}")
            return record_id
        except sqlite3.Error as e:
            logger.error(f"Error inserting sentiment for post_id={post_id}: {e}")
            return None

    def insert_keywords(self, post_id: int, keywords: list[dict]):
        """
        Insert extracted keywords for a post.

        Args:
            post_id: The database ID of the post.
            keywords: List of dicts with 'keyword' and 'tfidf_score' keys.
        """
        sql = """
            INSERT INTO keywords (post_id, keyword, tfidf_score)
            VALUES (?, ?, ?)
        """
        try:
            conn = self._get_connection()
            for kw in keywords:
                conn.execute(sql, (post_id, kw["keyword"], kw.get("tfidf_score", 0.0)))
            conn.commit()
            conn.close()
            logger.debug(f"Inserted {len(keywords)} keywords for post_id={post_id}")
        except sqlite3.Error as e:
            logger.error(f"Error inserting keywords for post_id={post_id}: {e}")

    def has_sentiment(self, post_id: int) -> bool:
        """Check if sentiment analysis already exists for a given post."""
        sql = "SELECT COUNT(*) as cnt FROM sentiment_scores WHERE post_id = ?"
        try:
            conn = self._get_connection()
            cursor = conn.execute(sql, (post_id,))
            row = cursor.fetchone()
            conn.close()
            return row["cnt"] > 0
        except sqlite3.Error:
            return False

    def execute_query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a read query and return results as a list of dictionaries.

        Args:
            sql: The SQL query to execute.
            params: Query parameters (tuple).

        Returns:
            List of dictionaries with the query results.
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            conn.close()
            return results
        except (sqlite3.Error, Exception) as e:
            logger.error(f"Error executing query: {e}")
            return []

    def get_post_count(self) -> int:
        """Return the total number of posts in the database."""
        results = self.execute_query("SELECT COUNT(*) AS cnt FROM posts")
        return int(results[0]["cnt"]) if results else 0

    def get_sentiment_distribution(self, subreddit: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sentiment distribution, optionally filtered by subreddit."""
        if subreddit and subreddit != "All":
            sql = """
                SELECT s.overall_sentiment, COUNT(*) AS count
                FROM posts p
                JOIN sentiment_scores s ON p.id = s.post_id
                WHERE p.subreddit = ?
                GROUP BY s.overall_sentiment
            """
            return self.execute_query(sql, (subreddit,))
        else:
            sql = """
                SELECT s.overall_sentiment, COUNT(*) AS count
                FROM sentiment_scores s
                GROUP BY s.overall_sentiment
            """
            return self.execute_query(sql)

    def get_sentiment_trend(self, subreddit: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sentiment trend over time, optionally filtered by subreddit."""
        if subreddit and subreddit != "All":
            sql = """
                SELECT
                    strftime('%Y-%m-%d %H:00:00', p.created_utc) AS time_bucket,
                    p.subreddit,
                    AVG(s.vader_compound)    AS avg_vader,
                    AVG(s.textblob_polarity) AS avg_textblob,
                    AVG(s.combined_score)    AS avg_combined,
                    COUNT(*)                 AS post_count
                FROM posts p
                JOIN sentiment_scores s ON p.id = s.post_id
                WHERE p.subreddit = ?
                GROUP BY time_bucket, p.subreddit
                ORDER BY time_bucket
            """
            return self.execute_query(sql, (subreddit,))
        else:
            sql = """
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
                ORDER BY time_bucket
            """
            return self.execute_query(sql)

    def get_top_keywords(self, limit: int = 20, subreddit: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get top keywords by frequency."""
        if subreddit and subreddit != "All":
            sql = """
                SELECT k.keyword, COUNT(*) AS frequency, AVG(k.tfidf_score) AS avg_tfidf
                FROM keywords k
                JOIN posts p ON k.post_id = p.id
                WHERE p.subreddit = ?
                GROUP BY k.keyword
                ORDER BY frequency DESC
                LIMIT ?
            """
            return self.execute_query(sql, (subreddit, limit))
        else:
            sql = """
                SELECT k.keyword, COUNT(*) AS frequency, AVG(k.tfidf_score) AS avg_tfidf
                FROM keywords k
                GROUP BY k.keyword
                ORDER BY frequency DESC
                LIMIT ?
            """
            return self.execute_query(sql, (limit,))

    def get_recent_posts(self, limit: int = 50, subreddit: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent posts with sentiment data."""
        if subreddit and subreddit != "All":
            sql = """
                SELECT
                    p.title, p.subreddit, p.author,
                    p.score AS reddit_score, p.num_comments,
                    s.vader_compound, s.textblob_polarity,
                    s.combined_score, s.overall_sentiment,
                    p.permalink, p.created_utc, s.analyzed_at
                FROM posts p
                JOIN sentiment_scores s ON p.id = s.post_id
                WHERE p.subreddit = ?
                ORDER BY s.analyzed_at DESC
                LIMIT ?
            """
            return self.execute_query(sql, (subreddit, limit))
        else:
            sql = """
                SELECT
                    p.title, p.subreddit, p.author,
                    p.score AS reddit_score, p.num_comments,
                    s.vader_compound, s.textblob_polarity,
                    s.combined_score, s.overall_sentiment,
                    p.permalink, p.created_utc, s.analyzed_at
                FROM posts p
                JOIN sentiment_scores s ON p.id = s.post_id
                ORDER BY s.analyzed_at DESC
                LIMIT ?
            """
            return self.execute_query(sql, (limit,))

    def get_subreddit_comparison(self) -> List[Dict[str, Any]]:
        """Get average sentiment scores per subreddit for comparison."""
        sql = """
            SELECT
                p.subreddit,
                ROUND(AVG(s.vader_compound), 4)    AS avg_vader,
                ROUND(AVG(s.textblob_polarity), 4) AS avg_textblob,
                ROUND(AVG(s.combined_score), 4)     AS avg_combined,
                COUNT(*)                             AS total_posts
            FROM posts p
            JOIN sentiment_scores s ON p.id = s.post_id
            GROUP BY p.subreddit
            ORDER BY avg_combined DESC
        """
        return self.execute_query(sql)

    def get_subreddits(self) -> list[str]:
        """Return a list of all unique subreddits in the database."""
        results = self.execute_query("SELECT DISTINCT subreddit FROM posts ORDER BY subreddit")
        return [row["subreddit"] for row in results] if results else []

    def get_pipeline_stats(self) -> dict:
        """Get overall pipeline statistics."""
        sql = """
            SELECT
                COUNT(*)                                     AS total_posts,
                COUNT(DISTINCT p.subreddit)                  AS subreddits_tracked,
                MIN(p.created_utc)                           AS earliest_post,
                MAX(p.created_utc)                           AS latest_post,
                SUM(CASE WHEN s.overall_sentiment = 'POSITIVE' THEN 1 ELSE 0 END) AS positive_count,
                SUM(CASE WHEN s.overall_sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) AS negative_count,
                SUM(CASE WHEN s.overall_sentiment = 'NEUTRAL'  THEN 1 ELSE 0 END) AS neutral_count
            FROM posts p
            LEFT JOIN sentiment_scores s ON p.id = s.post_id
        """
        results = self.execute_query(sql)
        if not results:
            return {
                "total_posts": 0, "subreddits_tracked": 0,
                "positive_count": 0, "negative_count": 0, "neutral_count": 0,
            }
        row = results[0]
        return {
            "total_posts": int(row.get("total_posts") or 0),
            "subreddits_tracked": int(row.get("subreddits_tracked") or 0),
            "earliest_post": row.get("earliest_post"),
            "latest_post": row.get("latest_post"),
            "positive_count": int(row.get("positive_count") or 0),
            "negative_count": int(row.get("negative_count") or 0),
            "neutral_count": int(row.get("neutral_count") or 0),
        }
