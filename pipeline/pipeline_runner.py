"""
Pipeline Runner for the Reddit Sentiment Analysis Pipeline.

Orchestrates the full data pipeline:
1. Initialize database tables
2. Fetch posts from configured subreddits via RedditClient
3. Run sentiment analysis via SentimentAnalyzer
4. Store results in SQLite via DatabaseManager
5. Extract and store keywords

Supports single batch runs and continuous mode with configurable intervals.
"""

import sys
import time
import logging
from datetime import datetime

from database.db_manager import DatabaseManager
from ingestion.reddit_client import RedditClient
from analysis.sentiment_analyzer import SentimentAnalyzer
from config import TARGET_SUBREDDITS, POSTS_PER_SUBREDDIT, PIPELINE_INTERVAL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class PipelineRunner:
    """Orchestrates the Reddit sentiment analysis pipeline."""

    def __init__(self):
        """Initialize all pipeline components."""
        logger.info("=" * 60)
        logger.info("Initializing Reddit Sentiment Analysis Pipeline")
        logger.info("=" * 60)

        # Initialize database
        self.db = DatabaseManager()
        self.db.init_db()
        logger.info("✓ Database initialized")

        # Initialize Reddit client
        self.reddit_client = RedditClient()
        logger.info("✓ Reddit client connected")

        # Initialize sentiment analyzer
        self.analyzer = SentimentAnalyzer()
        logger.info("✓ Sentiment analyzer ready")

        logger.info(f"Target subreddits: {TARGET_SUBREDDITS}")
        logger.info(f"Posts per subreddit: {POSTS_PER_SUBREDDIT}")
        logger.info("=" * 60)

    def process_post(self, post: dict) -> bool:
        """
        Process a single post through the pipeline.

        1. Insert post into database
        2. Run sentiment analysis (if not already analyzed)
        3. Extract and store keywords

        Args:
            post: Parsed Reddit post dictionary.

        Returns:
            True if the post was successfully processed, False otherwise.
        """
        try:
            # Step 1: Insert post into database
            post_id = self.db.insert_post(post)
            if post_id is None:
                logger.warning(f"Failed to insert post: {post.get('reddit_id')}")
                return False

            # Step 2: Check if already analyzed
            if self.db.has_sentiment(post_id):
                logger.debug(f"Post {post.get('reddit_id')} already analyzed, skipping.")
                return True

            # Step 3: Run sentiment analysis
            sentiment = self.analyzer.analyze_post(post)
            self.db.insert_sentiment(post_id, sentiment)

            # Step 4: Extract and store keywords
            keywords = self.analyzer.extract_keywords_for_post(post, top_n=10)
            if keywords:
                self.db.insert_keywords(post_id, keywords)

            logger.debug(
                f"Processed: {post.get('reddit_id')} | "
                f"r/{post.get('subreddit')} | "
                f"Sentiment: {sentiment['overall_sentiment']} "
                f"(combined={sentiment['combined_score']:.4f})"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error processing post {post.get('reddit_id', 'unknown')}: {e}"
            )
            return False

    def run_once(self):
        """
        Execute a single batch run of the pipeline.

        Fetches hot posts from all configured subreddits, analyzes them,
        and stores results in the database.
        """
        start_time = time.time()
        total_processed = 0
        total_failed = 0

        logger.info("Starting pipeline batch run...")

        for subreddit in TARGET_SUBREDDITS:
            subreddit = subreddit.strip()
            logger.info(f"--- Processing r/{subreddit} ---")

            # Fetch posts
            posts = self.reddit_client.fetch_hot_posts(
                subreddit, limit=POSTS_PER_SUBREDDIT
            )

            if not posts:
                logger.warning(f"No posts fetched from r/{subreddit}")
                continue

            # Process each post
            for post in posts:
                success = self.process_post(post)
                if success:
                    total_processed += 1
                else:
                    total_failed += 1

        elapsed = time.time() - start_time
        stats = self.db.get_pipeline_stats()

        logger.info("=" * 60)
        logger.info("Pipeline Batch Run Complete")
        logger.info(f"  Posts processed this run: {total_processed}")
        logger.info(f"  Posts failed this run:    {total_failed}")
        logger.info(f"  Total posts in database:  {stats['total_posts']}")
        logger.info(f"  Subreddits tracked:       {stats['subreddits_tracked']}")
        logger.info(f"  Elapsed time:             {elapsed:.2f}s")
        logger.info("=" * 60)

    def run_continuous(self, interval: int = None):
        """
        Run the pipeline in continuous mode, executing batches at regular intervals.

        Args:
            interval: Seconds between batch runs. Defaults to PIPELINE_INTERVAL from config.
        """
        if interval is None:
            interval = PIPELINE_INTERVAL

        logger.info(f"Starting continuous pipeline (interval={interval}s)")
        logger.info("Press Ctrl+C to stop.")

        run_count = 0
        try:
            while True:
                run_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Pipeline Run #{run_count} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")

                self.run_once()

                logger.info(f"Next run in {interval} seconds...")
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("\nPipeline stopped by user. Graceful shutdown complete.")


def main():
    """Entry point for running the pipeline from the command line."""
    runner = PipelineRunner()

    if "--continuous" in sys.argv or "-c" in sys.argv:
        runner.run_continuous()
    else:
        runner.run_once()


if __name__ == "__main__":
    main()
