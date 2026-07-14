"""
Streamlit Dashboard for the Reddit Sentiment Analysis Pipeline.

An interactive web dashboard that exposes:
- Live sentiment scores and distributions
- Sentiment trends over time
- Keyword clouds and frequency charts
- Subreddit comparison analytics
- Real-time post feed with sentiment labels

Launch with: streamlit run dashboard/app.py
"""

import sys
import os

# Ensure project root is on the path so imports work when
# Streamlit is launched from the dashboard/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io

from database.db_manager import DatabaseManager

# =============================================================================
# Page Configuration
# =============================================================================
st.set_page_config(
    page_title="Reddit Sentiment Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# Custom CSS for Premium Look
# =============================================================================
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #FF4500 0%, #FF6B35 50%, #FF8C42 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(255, 69, 0, 0.25);
    }
    .main-header h1 {
        color: white;
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: rgba(255,255,255,0.85);
        font-size: 1rem;
        margin: 0.3rem 0 0 0;
        font-weight: 400;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.25);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF4500, #FF8C42);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }
    .metric-label {
        color: #8892b0;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.3rem;
    }

    /* Sentiment badges */
    .sentiment-positive {
        background: linear-gradient(135deg, #00c853, #69f0ae);
        color: #1b5e20;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .sentiment-negative {
        background: linear-gradient(135deg, #ff1744, #ff8a80);
        color: #b71c1c;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .sentiment-neutral {
        background: linear-gradient(135deg, #ffd600, #fff59d);
        color: #f57f17;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }

    /* Section headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #e0e0e0;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(255, 69, 0, 0.3);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    }
    [data-testid="stSidebar"] .stMarkdown h2 {
        color: #FF4500;
        font-weight: 700;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Data table styling */
    .dataframe {
        font-size: 0.85rem !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Initialize Database Connection
# =============================================================================
@st.cache_resource
def get_db():
    """Get a cached DatabaseManager instance."""
    db = DatabaseManager()
    db.init_db()
    return db

db = get_db()


# =============================================================================
# Sidebar
# =============================================================================
with st.sidebar:
    st.markdown("## 🔧 Controls")
    st.markdown("---")

    # Subreddit filter
    subreddits = db.get_subreddits()
    subreddit_options = ["All"] + subreddits
    selected_subreddit = st.selectbox(
        "📌 Filter by Subreddit",
        subreddit_options,
        index=0,
    )

    st.markdown("---")

    # Pipeline trigger
    st.markdown("## 🚀 Pipeline")
    if st.button("▶️ Run Pipeline Now", use_container_width=True, type="primary"):
        with st.spinner("Running pipeline..."):
            try:
                from pipeline.pipeline_runner import PipelineRunner
                runner = PipelineRunner()
                runner.run_once()
                st.success("✅ Pipeline completed!")
                st.cache_data.clear()
                st.rerun()
            except ValueError as e:
                st.error(f"❌ Configuration Error: {e}")
            except Exception as e:
                st.error(f"❌ Pipeline error: {e}")

    st.markdown("---")

    # Auto-refresh
    auto_refresh = st.toggle("🔄 Auto-Refresh", value=False)
    if auto_refresh:
        refresh_interval = st.slider("Refresh interval (sec)", 10, 300, 60)
        st.info(f"Dashboard refreshes every {refresh_interval}s")
        import time as _time
        _time.sleep(0.1)  # Small delay to prevent instant rerun
        st.rerun()

    st.markdown("---")
    st.markdown("## 📊 About")
    st.markdown(
        "**Reddit Sentiment Analysis Pipeline**\n\n"
        "Powered by PRAW, VADER, TextBlob, and Streamlit.\n\n"
        "Analyzes Reddit posts for sentiment using dual NLP engines "
        "and visualizes trends in real-time."
    )


# =============================================================================
# Main Dashboard
# =============================================================================

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>📊 Reddit Sentiment Analysis Dashboard</h1>
    <p>Real-time sentiment tracking across Reddit communities · Powered by VADER & TextBlob</p>
</div>
""", unsafe_allow_html=True)


# --- Key Metrics ---
stats = db.get_pipeline_stats()
total_posts = stats["total_posts"]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_posts:,}</div>
        <div class="metric-label">Total Posts Analyzed</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{stats['subreddits_tracked']}</div>
        <div class="metric-label">Subreddits Tracked</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    positive = stats.get("positive_count", 0)
    pct = f"{(positive/total_posts*100):.1f}%" if total_posts > 0 else "N/A"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="background: linear-gradient(135deg, #00c853, #69f0ae); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{pct}</div>
        <div class="metric-label">Positive Sentiment</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    negative = stats.get("negative_count", 0)
    neg_pct = f"{(negative/total_posts*100):.1f}%" if total_posts > 0 else "N/A"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="background: linear-gradient(135deg, #ff1744, #ff8a80); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{neg_pct}</div>
        <div class="metric-label">Negative Sentiment</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# --- Guard: Check if data exists ---
if total_posts == 0:
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border-radius: 16px; border: 1px dashed rgba(255,69,0,0.4); margin: 2rem 0;">
        <h2 style="color: #FF4500;">🚀 No Data Yet</h2>
        <p style="color: #8892b0; font-size: 1.1rem;">
            Run the pipeline to start analyzing Reddit posts.<br>
            Click <strong>"▶️ Run Pipeline Now"</strong> in the sidebar, or run from the terminal:
        </p>
        <code style="color: #FF8C42; font-size: 1rem;">python -m pipeline.pipeline_runner</code>
        <p style="color: #8892b0; margin-top: 1rem; font-size: 0.9rem;">
            Make sure your Reddit API credentials are set in the <strong>.env</strong> file first.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# =============================================================================
# Dashboard Tabs
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Sentiment Overview",
    "🔑 Keyword Trends",
    "📋 Live Feed",
    "🏆 Subreddit Comparison",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: Sentiment Overview
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">Sentiment Distribution</div>', unsafe_allow_html=True)

    col_dist, col_gauge = st.columns([1, 1])

    with col_dist:
        # Donut chart: sentiment distribution
        dist_data = db.get_sentiment_distribution(
            selected_subreddit if selected_subreddit != "All" else None
        )
        if dist_data:
            color_map = {
                "POSITIVE": "#00c853",
                "NEGATIVE": "#ff1744",
                "NEUTRAL": "#ffd600",
            }
            fig_donut = px.pie(
                dist_data,
                values="count",
                names="overall_sentiment",
                color="overall_sentiment",
                color_discrete_map=color_map,
                hole=0.55,
            )
            fig_donut.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#e0e0e0"),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, x=0.5, xanchor="center"),
                margin=dict(t=30, b=30, l=20, r=20),
                height=380,
            )
            fig_donut.update_traces(
                textinfo="percent+label",
                textfont_size=13,
                marker=dict(line=dict(color="#0d1117", width=2)),
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No sentiment data available yet.")

    with col_gauge:
        # Gauge: average combined sentiment
        recent_data = db.get_recent_posts(limit=100, subreddit=selected_subreddit)
        if recent_data:
            avg_score = sum(r["combined_score"] for r in recent_data) / len(recent_data)

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=avg_score,
                number=dict(font=dict(size=42, color="#FF4500"), valueformat=".3f"),
                title=dict(text="Average Sentiment Score", font=dict(size=16, color="#8892b0")),
                gauge=dict(
                    axis=dict(range=[-1, 1], tickwidth=1, tickcolor="#444"),
                    bar=dict(color="#FF4500"),
                    bgcolor="rgba(0,0,0,0)",
                    borderwidth=0,
                    steps=[
                        dict(range=[-1, -0.05], color="rgba(255,23,68,0.2)"),
                        dict(range=[-0.05, 0.05], color="rgba(255,214,0,0.2)"),
                        dict(range=[0.05, 1], color="rgba(0,200,83,0.2)"),
                    ],
                    threshold=dict(
                        line=dict(color="white", width=3),
                        thickness=0.8,
                        value=avg_score,
                    ),
                ),
            ))
            fig_gauge.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter"),
                height=380,
                margin=dict(t=60, b=30, l=40, r=40),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
        else:
            st.info("No recent posts available.")

    # Sentiment Trend Over Time
    st.markdown('<div class="section-header">Sentiment Trend Over Time</div>', unsafe_allow_html=True)

    trend_data = db.get_sentiment_trend(
        selected_subreddit if selected_subreddit != "All" else None
    )
    if trend_data:
        fig_trend = px.line(
            trend_data,
            x="time_bucket",
            y="avg_combined",
            color="subreddit",
            markers=True,
            labels={
                "time_bucket": "Time",
                "avg_combined": "Avg Combined Sentiment",
                "subreddit": "Subreddit",
            },
        )
        fig_trend.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#e0e0e0"),
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)"),
            height=400,
            margin=dict(t=20, b=40, l=40, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
            hovermode="x unified",
        )
        fig_trend.update_traces(line=dict(width=2.5))
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Not enough data for trend analysis yet.")

    # VADER vs TextBlob Score Distribution
    st.markdown('<div class="section-header">VADER vs TextBlob Score Distribution</div>', unsafe_allow_html=True)

    if recent_data:
        col_v, col_t = st.columns(2)
        with col_v:
            fig_hist_vader = px.histogram(
                recent_data,
                x="vader_compound",
                nbins=30,
                color_discrete_sequence=["#FF4500"],
                labels={"vader_compound": "VADER Compound Score"},
            )
            fig_hist_vader.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#e0e0e0"),
                title=dict(text="VADER Compound Distribution", font=dict(size=14)),
                height=300,
                margin=dict(t=40, b=40, l=40, r=20),
                bargap=0.05,
            )
            st.plotly_chart(fig_hist_vader, use_container_width=True)

        with col_t:
            fig_hist_tb = px.histogram(
                recent_data,
                x="textblob_polarity",
                nbins=30,
                color_discrete_sequence=["#00bcd4"],
                labels={"textblob_polarity": "TextBlob Polarity"},
            )
            fig_hist_tb.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#e0e0e0"),
                title=dict(text="TextBlob Polarity Distribution", font=dict(size=14)),
                height=300,
                margin=dict(t=40, b=40, l=40, r=20),
                bargap=0.05,
            )
            st.plotly_chart(fig_hist_tb, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: Keyword Trends
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">Top Keywords by Frequency</div>', unsafe_allow_html=True)

    kw_data = db.get_top_keywords(limit=25, subreddit=selected_subreddit)

    if kw_data:
        col_bar, col_cloud = st.columns([1, 1])

        with col_bar:
            fig_kw = px.bar(
                kw_data[:20],
                x="frequency",
                y="keyword",
                orientation="h",
                color="avg_tfidf",
                color_continuous_scale=["#1a1a2e", "#FF4500", "#FF8C42"],
                labels={"frequency": "Frequency", "keyword": "Keyword", "avg_tfidf": "TF-IDF"},
            )
            fig_kw.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#e0e0e0"),
                yaxis=dict(autorange="reversed", categoryorder="total ascending"),
                height=550,
                margin=dict(t=20, b=40, l=20, r=20),
                coloraxis_colorbar=dict(title="TF-IDF", thickness=15),
            )
            st.plotly_chart(fig_kw, use_container_width=True)

        with col_cloud:
            # Word Cloud
            word_freq = {d["keyword"]: d["frequency"] for d in kw_data}
            if word_freq:
                wc = WordCloud(
                    width=800,
                    height=500,
                    background_color="#0d1117",
                    colormap="Oranges",
                    max_words=50,
                    min_font_size=12,
                    max_font_size=100,
                    prefer_horizontal=0.7,
                    contour_width=0,
                    margin=10,
                ).generate_from_frequencies(word_freq)

                fig_wc, ax = plt.subplots(figsize=(10, 6))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                fig_wc.patch.set_facecolor("#0d1117")
                plt.tight_layout(pad=0)
                st.pyplot(fig_wc)
                plt.close()
    else:
        st.info("No keyword data available. Run the pipeline to extract keywords.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: Live Feed
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">Recent Posts with Sentiment Scores</div>', unsafe_allow_html=True)

    feed_data = db.get_recent_posts(limit=50, subreddit=selected_subreddit)

    if feed_data:
        def sentiment_badge(sentiment):
            colors = {
                "POSITIVE": "🟢",
                "NEGATIVE": "🔴",
                "NEUTRAL": "🟡",
            }
            return f"{colors.get(sentiment, '⚪')} {sentiment}"

        display_data = []
        for row in feed_data:
            display_data.append({
                "Title": row.get("title", ""),
                "Subreddit": row.get("subreddit", ""),
                "Sentiment": sentiment_badge(row.get("overall_sentiment", "")),
                "VADER": f"{row.get('vader_compound', 0.0):+.3f}",
                "TextBlob": f"{row.get('textblob_polarity', 0.0):+.3f}",
                "Combined": f"{row.get('combined_score', 0.0):+.3f}",
                "⬆️ Score": row.get("reddit_score", 0),
                "💬 Comments": row.get("num_comments", 0),
                "Created": row.get("created_utc", ""),
            })

        st.dataframe(
            display_data,
            use_container_width=True,
            height=600,
            column_config={
                "Title": st.column_config.TextColumn("Title", width="large"),
                "Subreddit": st.column_config.TextColumn("Subreddit", width="small"),
                "Sentiment": st.column_config.TextColumn("Sentiment", width="small"),
                "VADER": st.column_config.TextColumn("VADER", width="small"),
                "TextBlob": st.column_config.TextColumn("TextBlob", width="small"),
                "Combined": st.column_config.TextColumn("Combined", width="small"),
                "⬆️ Score": st.column_config.NumberColumn("⬆️ Score", width="small"),
                "💬 Comments": st.column_config.NumberColumn("💬 Comments", width="small"),
                "Created": st.column_config.TextColumn("Created", width="medium"),
            },
        )

        # Summary below the table
        st.markdown(f"""
        <div style="display: flex; gap: 1.5rem; margin-top: 1rem; justify-content: center;">
            <div style="color: #00c853; font-weight: 600;">
                🟢 Positive: {sum(1 for r in feed_data if r.get('overall_sentiment') == 'POSITIVE')}
            </div>
            <div style="color: #ffd600; font-weight: 600;">
                🟡 Neutral: {sum(1 for r in feed_data if r.get('overall_sentiment') == 'NEUTRAL')}
            </div>
            <div style="color: #ff1744; font-weight: 600;">
                🔴 Negative: {sum(1 for r in feed_data if r.get('overall_sentiment') == 'NEGATIVE')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No posts available. Run the pipeline to start ingesting data.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: Subreddit Comparison
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">Subreddit Sentiment Comparison</div>', unsafe_allow_html=True)

    comp_data = db.get_subreddit_comparison()

    if comp_data:
        # Grouped bar chart
        comp_melted = []
        metric_labels = {
            "avg_vader": "VADER",
            "avg_textblob": "TextBlob",
            "avg_combined": "Combined",
        }
        for row in comp_data:
            for val_var in ["avg_vader", "avg_textblob", "avg_combined"]:
                comp_melted.append({
                    "subreddit": row["subreddit"],
                    "total_posts": row["total_posts"],
                    "Metric": metric_labels[val_var],
                    "Score": row[val_var]
                })

        fig_comp = px.bar(
            comp_melted,
            x="subreddit",
            y="Score",
            color="Metric",
            barmode="group",
            color_discrete_map={
                "VADER": "#FF4500",
                "TextBlob": "#00bcd4",
                "Combined": "#ffd600",
            },
            labels={"subreddit": "Subreddit", "Score": "Average Sentiment Score"},
        )
        fig_comp.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#e0e0e0"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="rgba(255,255,255,0.3)"),
            height=450,
            margin=dict(t=20, b=40, l=40, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # Post count per subreddit
        st.markdown('<div class="section-header">Posts Per Subreddit</div>', unsafe_allow_html=True)

        fig_posts = px.bar(
            comp_data,
            x="subreddit",
            y="total_posts",
            color="avg_combined",
            color_continuous_scale=["#ff1744", "#ffd600", "#00c853"],
            color_continuous_midpoint=0,
            labels={"subreddit": "Subreddit", "total_posts": "Total Posts", "avg_combined": "Avg Sentiment"},
        )
        fig_posts.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#e0e0e0"),
            height=350,
            margin=dict(t=20, b=40, l=40, r=20),
        )
        st.plotly_chart(fig_posts, use_container_width=True)

        # Stats table
        st.markdown('<div class="section-header">Detailed Statistics</div>', unsafe_allow_html=True)

        stats_display = [
            {
                "Subreddit": row["subreddit"],
                "Avg VADER": row["avg_vader"],
                "Avg TextBlob": row["avg_textblob"],
                "Avg Combined": row["avg_combined"],
                "Total Posts": row["total_posts"],
            }
            for row in comp_data
        ]
        st.dataframe(stats_display, use_container_width=True, hide_index=True)
    else:
        st.info("No subreddit comparison data available yet.")


# =============================================================================
# Footer
# =============================================================================
st.markdown("---")
st.markdown(
    f"""
    <div style="text-align: center; color: #555; font-size: 0.8rem; padding: 1rem 0;">
        Reddit Sentiment Analysis Pipeline · Built with Python, PRAW, VADER, TextBlob, SQLite & Streamlit
        <br>Dashboard last loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """,
    unsafe_allow_html=True,
)
