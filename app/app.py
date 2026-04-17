from __future__ import annotations

from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

app = Flask(__name__)


def read_csv(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    return frame.astype(object).where(pd.notna(frame), None)


def records(filename: str) -> list[dict]:
    return read_csv(filename).to_dict(orient="records")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/video")
def api_video():
    frame = read_csv("video_info.csv")
    if frame.empty:
        return jsonify({})
    video = frame.iloc[0].to_dict()
    video["sample_danmaku_count"] = len(read_csv("danmaku_clean.csv"))
    video["sample_comment_count"] = len(read_csv("comments_clean.csv"))
    return jsonify(video)


@app.route("/api/interaction")
def api_interaction():
    return jsonify(records("interaction_metrics.csv"))


@app.route("/api/danmaku-timeline")
def api_danmaku_timeline():
    return jsonify(records("danmaku_timeline.csv"))


@app.route("/api/danmaku-peaks")
def api_danmaku_peaks():
    limit = int(request.args.get("limit", 10))
    frame = read_csv("danmaku_peaks.csv").head(limit)
    return jsonify(frame.to_dict(orient="records"))


@app.route("/api/keywords")
def api_keywords():
    source = request.args.get("source", "danmaku")
    limit = int(request.args.get("limit", 30))
    if source in {"danmaku_before", "danmaku_after"}:
        stage_map = {
            "danmaku_before": "before_lottery_filter",
            "danmaku_after": "after_lottery_filter",
        }
        frame = read_csv("danmaku_keyword_compare.csv")
        if frame.empty:
            return jsonify([])
        frame = frame[frame["stage"] == stage_map[source]].sort_values("rank_order").head(limit)
        return jsonify(frame.to_dict(orient="records"))

    frame = read_csv("keyword_metrics.csv")
    if frame.empty:
        return jsonify([])
    frame = frame[frame["source_type"] == source].sort_values("rank_order").head(limit)
    return jsonify(frame.to_dict(orient="records"))


@app.route("/api/sentiment")
def api_sentiment():
    source = request.args.get("source")
    frame = read_csv("sentiment_metrics.csv")
    if source and not frame.empty:
        frame = frame[frame["source_type"] == source]
    return jsonify(frame.to_dict(orient="records"))


@app.route("/api/comment-like-sentiment")
def api_comment_like_sentiment():
    return jsonify(records("comment_like_sentiment.csv"))


@app.route("/api/danmaku-cleaning-summary")
def api_danmaku_cleaning_summary():
    frame = read_csv("danmaku_cleaning_summary.csv")
    if frame.empty:
        return jsonify({})
    return jsonify(frame.iloc[0].to_dict())


@app.route("/api/phone-feedback-summary")
def api_phone_feedback_summary():
    return jsonify(records("phone_feedback_summary.csv"))


@app.route("/api/phone-feedback-sentiment")
def api_phone_feedback_sentiment():
    return jsonify(records("phone_feedback_sentiment.csv"))


@app.route("/api/phone-feedback-keywords")
def api_phone_feedback_keywords():
    source = request.args.get("source")
    topic = request.args.get("topic")
    limit = int(request.args.get("limit", 30))
    frame = read_csv("phone_feedback_keywords.csv")
    if frame.empty:
        return jsonify([])
    if source:
        frame = frame[frame["source_type"] == source]
    if topic:
        frame = frame[frame["phone_feedback_topic"] == topic]
    frame = frame.sort_values("rank_order").head(limit)
    return jsonify(frame.to_dict(orient="records"))


@app.route("/api/phone-feedback-examples")
def api_phone_feedback_examples():
    source = request.args.get("source")
    topic = request.args.get("topic")
    frame = read_csv("phone_feedback_examples.csv")
    if frame.empty:
        return jsonify([])
    if source:
        frame = frame[frame["source_type"] == source]
    if topic:
        frame = frame[frame["phone_feedback_topic"] == topic]
    return jsonify(frame.to_dict(orient="records"))


@app.route("/api/insights")
def api_insights():
    path = PROCESSED_DIR / "analysis_insights.txt"
    if not path.exists():
        return jsonify({"insights": []})
    lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return jsonify({"insights": lines})


@app.route("/api/health")
def api_health():
    required = [
        "video_info.csv",
        "danmaku_clean.csv",
        "comments_clean.csv",
        "interaction_metrics.csv",
        "danmaku_timeline.csv",
        "keyword_metrics.csv",
        "danmaku_cleaning_summary.csv",
        "danmaku_keyword_compare.csv",
        "sentiment_metrics.csv",
        "phone_feedback_summary.csv",
        "phone_feedback_sentiment.csv",
        "phone_feedback_keywords.csv",
        "phone_feedback_examples.csv",
    ]
    status = {filename: (PROCESSED_DIR / filename).exists() for filename in required}
    return jsonify({"ok": all(status.values()), "files": status})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
