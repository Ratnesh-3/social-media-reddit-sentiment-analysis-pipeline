"""
Reddit API Client for the Sentiment Analysis Pipeline.

Wraps PRAW (Python Reddit API Wrapper) to handle:
- OAuth2 authentication with credentials from environment variables
- Rate limit awareness and logging
- JSON response parsing into clean dictionaries
- Hot/new post fetching and real-time streaming
"""

import logging
from datetime import datetime, timezone
from typing import Generator, Optional

import praw
from praw.exceptions import PRAWException
from prawcore.exceptions import (
    ResponseException,
    OAuthException,
    RequestException,
)

logger = logging.getLogger(__name__)


class RedditClient:
    """Client for interacting with the Reddit API via PRAW."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize the Reddit client with API credentials.

        If credentials are not provided, they are loaded from config (env vars).

        Args:
            client_id: Reddit app client ID.
            client_secret: Reddit app client secret.
            username: Reddit username.
            password: Reddit password.
            user_agent: Descriptive user agent string.
        """
        if client_id is None:
            from config import (
                REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
                REDDIT_USERNAME, REDDIT_PASSWORD, REDDIT_USER_AGENT,
            )
            client_id = REDDIT_CLIENT_ID
            client_secret = REDDIT_CLIENT_SECRET
            username = REDDIT_USERNAME
            password = REDDIT_PASSWORD
            user_agent = REDDIT_USER_AGENT

        # Validate that credentials are provided
        if not client_id or not client_secret:
            raise ValueError(
                "Reddit API credentials are missing. "
                "Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in your .env file. "
                "See .env.example for details."
            )

        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                username=username,
                password=password,
                user_agent=user_agent,
            )
            # Verify authentication by accessing read-only attribute
            _ = self.reddit.user.me()
            logger.info(f"Reddit client authenticated as: {username}")
        except OAuthException as e:
            logger.error(f"Reddit OAuth authentication failed: {e}")
            raise
        except Exception as e:
            logger.warning(
                f"Reddit client initialized in read-only mode: {e}. "
                "Some features may be limited."
            )
            # Fall back to read-only mode (no username/password)
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )

    def _parse_submission(self, submission) -> dict:
        """
        Parse a PRAW Submission object into a clean dictionary.

        Extracts and normalizes all relevant fields from the Reddit API
        JSON response.

        Args:
            submission: A praw.models.Submission object.

        Returns:
            Dictionary with parsed post data.
        """
        try:
            author_name = str(submission.author) if submission.author else "[deleted]"
        except Exception:
            author_name = "[deleted]"

        created_utc = datetime.fromtimestamp(
            submission.created_utc, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")

        return {
            "reddit_id": submission.id,
            "subreddit": str(submission.subreddit),
            "title": submission.title,
            "selftext": submission.selftext or "",
            "author": author_name,
            "score": submission.score,
            "num_comments": submission.num_comments,
            "url": submission.url,
            "permalink": f"https://reddit.com{submission.permalink}",
            "created_utc": created_utc,
        }

    def fetch_hot_posts(self, subreddit: str, limit: int = 50) -> list[dict]:
        """
        Fetch hot posts from a subreddit.

        Args:
            subreddit: Name of the subreddit (without r/ prefix).
            limit: Maximum number of posts to fetch.

        Returns:
            List of parsed post dictionaries.
        """
        posts = []
        try:
            logger.info(f"Fetching {limit} hot posts from r/{subreddit}...")
            sub = self.reddit.subreddit(subreddit)

            for submission in sub.hot(limit=limit):
                post = self._parse_submission(submission)
                posts.append(post)

            logger.info(
                f"Fetched {len(posts)} hot posts from r/{subreddit}. "
                f"Rate limit remaining: {self._get_rate_limit_info()}"
            )
        except ResponseException as e:
            logger.error(f"Reddit API response error for r/{subreddit}: {e}")
        except RequestException as e:
            logger.error(f"Reddit API request error for r/{subreddit}: {e}")
        except PRAWException as e:
            logger.error(f"PRAW error fetching from r/{subreddit}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching from r/{subreddit}: {e}")

        return posts

    def fetch_new_posts(self, subreddit: str, limit: int = 50) -> list[dict]:
        """
        Fetch newest posts from a subreddit.

        Args:
            subreddit: Name of the subreddit (without r/ prefix).
            limit: Maximum number of posts to fetch.

        Returns:
            List of parsed post dictionaries.
        """
        posts = []
        try:
            logger.info(f"Fetching {limit} new posts from r/{subreddit}...")
            sub = self.reddit.subreddit(subreddit)

            for submission in sub.new(limit=limit):
                post = self._parse_submission(submission)
                posts.append(post)

            logger.info(
                f"Fetched {len(posts)} new posts from r/{subreddit}. "
                f"Rate limit remaining: {self._get_rate_limit_info()}"
            )
        except ResponseException as e:
            logger.error(f"Reddit API response error for r/{subreddit}: {e}")
        except RequestException as e:
            logger.error(f"Reddit API request error for r/{subreddit}: {e}")
        except PRAWException as e:
            logger.error(f"PRAW error fetching from r/{subreddit}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching from r/{subreddit}: {e}")

        return posts

    def stream_posts(self, subreddit: str) -> Generator[dict, None, None]:
        """
        Stream new submissions from a subreddit in real-time.

        This is a blocking generator that yields new posts as they appear.
        PRAW handles rate limiting automatically during streaming.

        Args:
            subreddit: Name of the subreddit (without r/ prefix).

        Yields:
            Parsed post dictionaries as new submissions appear.
        """
        try:
            logger.info(f"Starting stream for r/{subreddit}...")
            sub = self.reddit.subreddit(subreddit)

            for submission in sub.stream.submissions(skip_existing=True):
                post = self._parse_submission(submission)
                logger.debug(f"Streamed post: {post['reddit_id']} from r/{subreddit}")
                yield post
        except PRAWException as e:
            logger.error(f"PRAW stream error for r/{subreddit}: {e}")
        except Exception as e:
            logger.error(f"Stream error for r/{subreddit}: {e}")

    def _get_rate_limit_info(self) -> str:
        """
        Get current rate limit status from PRAW's internal tracking.

        Returns:
            String with rate limit information.
        """
        try:
            remaining = self.reddit.auth.limits.get("remaining", "unknown")
            reset_timestamp = self.reddit.auth.limits.get("reset_timestamp", None)

            if reset_timestamp:
                reset_time = datetime.fromtimestamp(
                    reset_timestamp, tz=timezone.utc
                ).strftime("%H:%M:%S UTC")
                return f"{remaining} requests remaining (resets at {reset_time})"
            return f"{remaining} requests remaining"
        except Exception:
            return "rate limit info unavailable"

    def test_connection(self) -> bool:
        """
        Test the Reddit API connection.

        Returns:
            True if the connection is working, False otherwise.
        """
        try:
            # Try to fetch a single post from a known subreddit
            sub = self.reddit.subreddit("test")
            for _ in sub.hot(limit=1):
                pass
            logger.info("Reddit API connection test: SUCCESS")
            return True
        except Exception as e:
            logger.error(f"Reddit API connection test FAILED: {e}")
            return False
