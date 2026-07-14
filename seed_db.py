import os
import random
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager

def seed():
    print("Initializing Database...")
    db = DatabaseManager()
    db.init_db()

    subreddits = ["technology", "python", "dataengineering", "learnprogramming"]
    
    # Mock data
    for i in range(1, 101):
        created_dt = datetime.utcnow() - timedelta(hours=random.randint(0, 100))
        post_id = db.insert_post({
            "reddit_id": f"mock{i}",
            "subreddit": random.choice(subreddits),
            "title": f"Mock post title {i}",
            "selftext": f"This is some mock content for post {i}",
            "author": f"user{i}",
            "score": random.randint(0, 1000),
            "num_comments": random.randint(0, 100),
            "url": f"https://reddit.com/r/mock/mock{i}",
            "permalink": f"/r/mock/mock{i}",
            "created_utc": created_dt.isoformat()
        })

        if post_id:
            vader = random.uniform(-1, 1)
            tb = random.uniform(-1, 1)
            combined = (vader + tb) / 2
            
            if combined > 0.05:
                sentiment = "POSITIVE"
            elif combined < -0.05:
                sentiment = "NEGATIVE"
            else:
                sentiment = "NEUTRAL"
                
            db.insert_sentiment(post_id, {
                "vader_compound": vader,
                "vader_positive": max(0, vader),
                "vader_negative": abs(min(0, vader)),
                "vader_neutral": 1 - abs(vader),
                "textblob_polarity": tb,
                "textblob_subjectivity": random.uniform(0, 1),
                "combined_score": combined,
                "overall_sentiment": sentiment,
            })
            
            # Keywords
            for j in range(random.randint(1, 5)):
                db.insert_keywords(post_id, [{
                    "keyword": random.choice(["python", "code", "ai", "data", "cloud", "api", "tech", "web", "app", "dev"]),
                    "tfidf_score": random.uniform(0.1, 0.9)
                }])
                
    print("Database seeded with 100 mock posts.")

if __name__ == "__main__":
    seed()
