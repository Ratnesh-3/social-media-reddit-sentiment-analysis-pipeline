# 📊 Social Media Reddit Sentiment Analysis Pipeline

A full-stack data engineering pipeline that ingests live Reddit posts via the **PRAW** API, performs dual sentiment analysis using **VADER** and **TextBlob**, stores results in a **SQLite** database, and exposes an interactive **Streamlit** dashboard with real-time sentiment scores and keyword trends.

---

## 🏗️ Architecture

```
Reddit API (PRAW)  →  Ingestion Engine  →  Sentiment Analyzer (VADER + TextBlob)
                                        →  Keyword Extractor (TF-IDF)
                                        →  SQLite Database
                                        →  Streamlit Dashboard (Plotly Charts + WordCloud)
```

---

## 🛠️ Tech Stack

| Component              | Technology                          |
|:----------------------|:------------------------------------|
| **Language**           | Python 3.10+                       |
| **Reddit API**         | PRAW (Python Reddit API Wrapper)   |
| **Sentiment Analysis** | VADER + TextBlob (dual-engine)     |
| **Database**           | SQLite3                            |
| **Dashboard**          | Streamlit + Plotly                  |
| **Keyword Analysis**   | scikit-learn (TF-IDF) + WordCloud  |

---

## 📁 Project Structure

```
social-media-reddit-sentiment-analysis-pipeline/
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── .env.example                      # Template for API credentials
├── .gitignore                        # Files to exclude from git
├── config.py                         # Centralized configuration
├── database/
│   ├── __init__.py
│   └── db_manager.py                 # SQLite connection & CRUD operations
├── ingestion/
│   ├── __init__.py
│   └── reddit_client.py              # PRAW client with auth & rate limiting
├── analysis/
│   ├── __init__.py
│   └── sentiment_analyzer.py         # VADER + TextBlob dual analysis
├── pipeline/
│   ├── __init__.py
│   └── pipeline_runner.py            # Orchestrates the full pipeline
├── dashboard/
│   └── app.py                        # Streamlit interactive dashboard
└── sql/
    ├── schema.sql                    # Database table definitions
    └── queries.sql                   # Reusable analytic queries
```

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10 or higher
- A Reddit account
- Reddit API credentials (see below)

### 2. Reddit API Setup

1. Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Scroll down and click **"create another app..."**
3. Fill in the form:
   - **Name**: `sentiment-analysis-pipeline`
   - **Type**: Select **script**
   - **Redirect URI**: `http://localhost:8080`
4. Click **Create app**
5. Note your **client ID** (under the app name) and **client secret**

### 3. Environment Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd social-media-reddit-sentiment-analysis-pipeline

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download TextBlob corpora (required on first run)
python -m textblob.download_corpora
```

### 4. Configure Credentials

```bash
# Copy the template
cp .env.example .env

# Edit .env with your Reddit API credentials
# Fill in: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD
```

### 5. Run the Pipeline

```bash
# Single batch run (fetches posts once)
python -m pipeline.pipeline_runner

# Continuous mode (fetches posts at regular intervals)
python -m pipeline.pipeline_runner --continuous
```

### 6. Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard will open at `http://localhost:8501` in your browser.

---

## 📊 Dashboard Features

| Feature | Description |
|:--------|:------------|
| **Key Metrics** | Total posts, subreddit count, positive/negative percentages |
| **Sentiment Distribution** | Interactive donut chart showing POSITIVE/NEGATIVE/NEUTRAL split |
| **Sentiment Gauge** | Real-time gauge showing average sentiment score |
| **Trend Analysis** | Time-series chart of sentiment scores by subreddit |
| **Score Distributions** | VADER vs TextBlob histogram comparison |
| **Keyword Cloud** | WordCloud visualization of trending keywords |
| **Keyword Bar Chart** | Top 20 keywords ranked by frequency with TF-IDF coloring |
| **Live Feed** | Scrollable table of recent posts with sentiment labels |
| **Subreddit Comparison** | Grouped bar chart comparing sentiment across communities |
| **Pipeline Trigger** | Run data ingestion directly from the dashboard sidebar |
| **Auto-Refresh** | Toggle automatic dashboard refresh (configurable interval) |
| **Subreddit Filter** | Filter all views by specific subreddit |

---

## 🔧 Configuration

All settings are managed via environment variables (`.env` file):

| Variable | Default | Description |
|:---------|:--------|:------------|
| `REDDIT_CLIENT_ID` | — | Reddit app client ID |
| `REDDIT_CLIENT_SECRET` | — | Reddit app client secret |
| `REDDIT_USERNAME` | — | Your Reddit username |
| `REDDIT_PASSWORD` | — | Your Reddit password |
| `REDDIT_USER_AGENT` | `sentiment-analysis-pipeline v1.0` | User agent string |
| `DATABASE_PATH` | `data/reddit_sentiment.db` | SQLite database file path |
| `TARGET_SUBREDDITS` | `technology,programming,news` | Comma-separated subreddit list |
| `POSTS_PER_SUBREDDIT` | `50` | Posts to fetch per subreddit per run |
| `PIPELINE_INTERVAL` | `300` | Seconds between runs in continuous mode |

---

## 🧠 How Sentiment Analysis Works

This pipeline uses a **dual-engine approach** for more robust sentiment scoring:

### VADER (Valence Aware Dictionary and sEntiment Reasoner)
- Specifically tuned for **social media** text
- Handles emojis, slang, capitalization emphasis ("GREAT"), and punctuation ("!!!")
- Returns compound score (-1 to +1), plus positive/negative/neutral proportions

### TextBlob
- General-purpose sentiment analysis
- Provides polarity (-1 to +1) and subjectivity (0 to 1)
- More stable across diverse text types

### Combined Score
```
combined = (0.6 × VADER compound) + (0.4 × TextBlob polarity)
```
- **POSITIVE**: combined > 0.05
- **NEGATIVE**: combined < -0.05
- **NEUTRAL**: -0.05 ≤ combined ≤ 0.05

---

## 📝 SQL Database Schema

The pipeline uses three main tables:

- **`posts`** — Raw Reddit post data (title, body, author, score, subreddit, timestamps)
- **`sentiment_scores`** — VADER and TextBlob analysis results linked to posts
- **`keywords`** — TF-IDF extracted keywords linked to posts

See [`sql/schema.sql`](sql/schema.sql) for the full DDL and [`sql/queries.sql`](sql/queries.sql) for reusable analytic queries.

---

## 📄 License

This project is for educational and portfolio purposes.
