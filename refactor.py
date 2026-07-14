import sys

with open('dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove pandas import
content = content.replace('import pandas as pd\n', '')

# 2. Fix Tab 1 Donut
content = content.replace('dist_df = db.get_sentiment_distribution(', 'dist_data = db.get_sentiment_distribution(')
content = content.replace('if not dist_df.empty:', 'if dist_data:')
content = content.replace('px.pie(\n                dist_df,', 'px.pie(\n                dist_data,')

# 3. Fix Tab 1 Gauge & Histogram
content = content.replace('recent_df = db.get_recent_posts(', 'recent_data = db.get_recent_posts(')
content = content.replace('if not recent_df.empty:', 'if recent_data:')
content = content.replace('avg_score = recent_df["combined_score"].mean()', 'avg_score = sum(r["combined_score"] for r in recent_data) / len(recent_data)')
content = content.replace('px.histogram(\n                recent_df,', 'px.histogram(\n                recent_data,')

# 4. Fix Tab 1 Trend
content = content.replace('trend_df = db.get_sentiment_trend(', 'trend_data = db.get_sentiment_trend(')
content = content.replace('if not trend_df.empty:', 'if trend_data:')
content = content.replace('trend_df["time_bucket"] = pd.to_datetime(trend_df["time_bucket"])\n\n        fig_trend = px.line(\n            trend_df,', 'fig_trend = px.line(\n            trend_data,')

# 5. Fix Tab 2 Keywords
content = content.replace('kw_df = db.get_top_keywords(', 'kw_data = db.get_top_keywords(')
content = content.replace('if not kw_df.empty:', 'if kw_data:')
content = content.replace('kw_df.head(20),', 'kw_data[:20],')
content = content.replace('word_freq = dict(zip(kw_df["keyword"], kw_df["frequency"]))', 'word_freq = {d["keyword"]: d["frequency"] for d in kw_data}')

# 6. Fix Tab 3 Live Feed
feed_old = """    feed_df = db.get_recent_posts(limit=50, subreddit=selected_subreddit)

    if not feed_df.empty:
        # Format the dataframe for display
        display_df = feed_df.copy()

        # Add sentiment badge HTML
        def sentiment_badge(sentiment):
            colors = {
                "POSITIVE": "🟢",
                "NEGATIVE": "🔴",
                "NEUTRAL": "🟡",
            }
            return f"{colors.get(sentiment, '⚪')} {sentiment}"

        display_df["Sentiment"] = display_df["overall_sentiment"].apply(sentiment_badge)
        display_df["VADER"] = display_df["vader_compound"].apply(lambda x: f"{x:+.3f}")
        display_df["TextBlob"] = display_df["textblob_polarity"].apply(lambda x: f"{x:+.3f}")
        display_df["Combined"] = display_df["combined_score"].apply(lambda x: f"{x:+.3f}")
        display_df["Link"] = display_df["permalink"].apply(
            lambda x: x if pd.notna(x) else ""
        )

        # Select columns for display
        show_cols = [
            "title", "subreddit", "Sentiment", "VADER", "TextBlob",
            "Combined", "reddit_score", "num_comments", "created_utc",
        ]
        display_df = display_df[show_cols].rename(columns={
            "title": "Title",
            "subreddit": "Subreddit",
            "reddit_score": "⬆️ Score",
            "num_comments": "💬 Comments",
            "created_utc": "Created",
        })

        st.dataframe(
            display_df,"""

feed_new = """    feed_data = db.get_recent_posts(limit=50, subreddit=selected_subreddit)

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
            display_data,"""

content = content.replace(feed_old, feed_new)

content = content.replace("{(feed_df['overall_sentiment'] == 'POSITIVE').sum()}", "{sum(1 for r in feed_data if r.get('overall_sentiment') == 'POSITIVE')}")
content = content.replace("{(feed_df['overall_sentiment'] == 'NEUTRAL').sum()}", "{sum(1 for r in feed_data if r.get('overall_sentiment') == 'NEUTRAL')}")
content = content.replace("{(feed_df['overall_sentiment'] == 'NEGATIVE').sum()}", "{sum(1 for r in feed_data if r.get('overall_sentiment') == 'NEGATIVE')}")

# 7. Fix Tab 4 Comparison
comp_old = """    comp_df = db.get_subreddit_comparison()

    if not comp_df.empty:
        # Grouped bar chart
        comp_melted = comp_df.melt(
            id_vars=["subreddit", "total_posts"],
            value_vars=["avg_vader", "avg_textblob", "avg_combined"],
            var_name="Metric",
            value_name="Score",
        )
        metric_labels = {
            "avg_vader": "VADER",
            "avg_textblob": "TextBlob",
            "avg_combined": "Combined",
        }
        comp_melted["Metric"] = comp_melted["Metric"].map(metric_labels)

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
        )"""

comp_new = """    comp_data = db.get_subreddit_comparison()

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
        )"""

content = content.replace(comp_old, comp_new)
content = content.replace("px.bar(\n            comp_df,", "px.bar(\n            comp_data,")

stats_old = """        # Stats table
        st.markdown('<div class="section-header">Detailed Statistics</div>', unsafe_allow_html=True)

        stats_display = comp_df.copy()
        stats_display.columns = ["Subreddit", "Avg VADER", "Avg TextBlob", "Avg Combined", "Total Posts"]
        st.dataframe(stats_display, use_container_width=True, hide_index=True)"""

stats_new = """        # Stats table
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
        st.dataframe(stats_display, use_container_width=True, hide_index=True)"""

content = content.replace(stats_old, stats_new)

with open('dashboard/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
