from __future__ import annotations

import math
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Iterable

import jieba
import pandas as pd
from snownlp import SnowNLP

import path_setup  # noqa: F401
from config.settings import (
    DANMAKU_BUCKET_SECONDS,
    DOCS_DIR,
    PROCESSED_DIR,
    SCREENSHOT_DIR,
    STOPWORDS,
    TEXT_ANALYSIS_TOP_N,
    ensure_directories,
)


for word in ["影视飓风", "iPhone", "Pro", "Air", "苹果", "评测", "影像", "外观"]:
    jieba.add_word(word)


LOTTERY_KEYWORDS = [
    "抽奖",
    "抽抽",
    "抽到",
    "中奖",
    "求中",
    "必中",
    "想中",
    "蹲奖",
    "参与",
    "来了",
    "冲冲冲",
    "许愿",
    "保佑",
    "欧皇",
    "非酋",
    "中了",
    "抽中",
    "奖品",
    "开奖",
    "送我",
    "给我",
    "选我",
    "中我",
    "我要",
    "想要",
    "一台",
    "中中",
    "中一个",
    "中一次",
    "中吧",
    "可莉",
    "无限",
    "读者",
]

LOTTERY_PATTERN = re.compile("|".join(re.escape(keyword) for keyword in LOTTERY_KEYWORDS))


def format_seconds(seconds: int | float) -> str:
    seconds = max(0, int(seconds))
    minute = seconds // 60
    second = seconds % 60
    return f"{minute:02d}:{second:02d}"


def clean_text(text: object) -> str:
    if pd.isna(text):
        return ""
    value = str(text)
    value = re.sub(r"https?://\S+|www\.\S+", " ", value)
    value = re.sub(r"\[[^\]]+\]", " ", value)
    value = re.sub(r"回复\s*@?\S+\s*:", " ", value)
    value = re.sub(r"@[A-Za-z0-9_\-\u4e00-\u9fa5]+", " ", value)
    value = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def is_lottery_danmaku(text: object) -> bool:
    """Identify lottery participation danmaku that should not drive content-topic analysis."""
    if pd.isna(text):
        return False
    value = str(text).strip()
    if not value:
        return False
    compact = re.sub(r"\s+", "", value.lower())
    if LOTTERY_PATTERN.search(compact):
        return True
    return bool(
        re.search(r"中{2,}", compact)
        or re.search(r"(抽|求|想|蹲|许愿).{0,6}(中|奖)", compact)
        or re.search(r"(中|奖).{0,4}(我|吧|一次|一个|一台)", compact)
    )


def sentiment_score(text: str) -> float:
    if not text:
        return 0.5
    try:
        score = float(SnowNLP(text[:240]).sentiments)
        return round(max(0.0, min(1.0, score)), 4)
    except Exception:
        return 0.5


def sentiment_label(score: float) -> str:
    if score >= 0.6:
        return "正向"
    if score <= 0.4:
        return "负向"
    return "中性"


def tokenize_texts(texts: Iterable[str]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for text in texts:
        if not isinstance(text, str) or not text:
            continue
        for token in jieba.lcut(text):
            token = token.strip()
            if not token:
                continue
            token_lower = token.lower()
            if token_lower in STOPWORDS or token in STOPWORDS:
                continue
            if len(token) < 2 and not re.match(r"[A-Za-z0-9]{2,}", token):
                continue
            if token.isdigit():
                continue
            if re.fullmatch(r"[A-Za-z0-9]+", token):
                token = token_lower
            counter[token] += 1
    return counter


def build_keyword_frame(source_type: str, texts: Iterable[str], top_n: int) -> pd.DataFrame:
    counter = tokenize_texts(texts)
    rows = [
        {
            "source_type": source_type,
            "keyword": keyword,
            "word_count": count,
            "rank_order": rank,
        }
        for rank, (keyword, count) in enumerate(counter.most_common(top_n), start=1)
    ]
    return pd.DataFrame(rows)


def build_sentiment_metrics(source_type: str, frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=["source_type", "sentiment_label", "sample_count", "ratio", "avg_score"]
        )

    total = len(frame)
    grouped = (
        frame.groupby("sentiment_label")
        .agg(sample_count=("sentiment_label", "size"), avg_score=("sentiment_score", "mean"))
        .reset_index()
    )
    grouped["source_type"] = source_type
    grouped["ratio"] = grouped["sample_count"] / total
    grouped["avg_score"] = grouped["avg_score"].round(4)
    grouped["ratio"] = grouped["ratio"].round(4)

    order_map = {"正向": 1, "中性": 2, "负向": 3}
    grouped["sort_order"] = grouped["sentiment_label"].map(order_map).fillna(9)
    grouped = grouped.sort_values("sort_order")
    return grouped[["source_type", "sentiment_label", "sample_count", "ratio", "avg_score"]]


def build_interaction_metrics(video: pd.Series) -> pd.DataFrame:
    views = max(int(video.get("view_count", 0) or 0), 1)
    metric_specs = [
        ("like_count", "点赞率", "like_rate"),
        ("coin_count", "投币率", "coin_rate"),
        ("favorite_count", "收藏率", "favorite_rate"),
        ("share_count", "分享率", "share_rate"),
        ("reply_count", "评论率", "reply_rate"),
        ("danmaku_count", "弹幕率", "danmaku_rate"),
    ]
    rows = []
    total_interactions = 0
    for value_field, label, metric_name in metric_specs:
        value = int(video.get(value_field, 0) or 0)
        total_interactions += value
        rows.append(
            {
                "metric_name": metric_name,
                "metric_label": label,
                "metric_value": value,
                "metric_rate": round(value / views, 6),
            }
        )

    rows.append(
        {
            "metric_name": "overall_interaction_rate",
            "metric_label": "综合互动率",
            "metric_value": total_interactions,
            "metric_rate": round(total_interactions / views, 6),
        }
    )
    return pd.DataFrame(rows)


def build_danmaku_timeline(danmaku: pd.DataFrame, duration_seconds: int) -> pd.DataFrame:
    if danmaku.empty:
        return pd.DataFrame(
            columns=[
                "time_bucket_30s",
                "start_sec",
                "end_sec",
                "start_label",
                "end_label",
                "time_range",
                "danmaku_count",
            ]
        )

    max_seconds = max(duration_seconds, int(danmaku["video_time"].max()) + 1)
    bucket_count = int(math.ceil(max_seconds / DANMAKU_BUCKET_SECONDS))
    buckets = pd.DataFrame(
        {"time_bucket_30s": [i * DANMAKU_BUCKET_SECONDS for i in range(bucket_count + 1)]}
    )
    grouped = (
        danmaku.groupby("time_bucket_30s")
        .size()
        .reset_index(name="danmaku_count")
        .sort_values("time_bucket_30s")
    )
    timeline = buckets.merge(grouped, on="time_bucket_30s", how="left")
    timeline["danmaku_count"] = timeline["danmaku_count"].fillna(0).astype(int)
    timeline["start_sec"] = timeline["time_bucket_30s"].astype(int)
    timeline["end_sec"] = timeline["start_sec"] + DANMAKU_BUCKET_SECONDS
    timeline["start_label"] = timeline["start_sec"].map(format_seconds)
    timeline["end_label"] = timeline["end_sec"].map(format_seconds)
    timeline["time_range"] = timeline["start_label"] + "-" + timeline["end_label"]
    return timeline[
        [
            "time_bucket_30s",
            "start_sec",
            "end_sec",
            "start_label",
            "end_label",
            "time_range",
            "danmaku_count",
        ]
    ]


def build_danmaku_cleaning_summary(
    raw_count: int,
    basic_clean_count: int,
    lottery_count: int,
    content_count: int,
) -> pd.DataFrame:
    filter_ratio = lottery_count / basic_clean_count if basic_clean_count else 0
    retain_ratio = content_count / basic_clean_count if basic_clean_count else 0
    return pd.DataFrame(
        [
            {
                "raw_sample_count": raw_count,
                "basic_clean_count": basic_clean_count,
                "lottery_filtered_count": lottery_count,
                "content_discussion_count": content_count,
                "filter_ratio": round(filter_ratio, 4),
                "retain_ratio": round(retain_ratio, 4),
            }
        ]
    )


def build_comment_like_sentiment(comments: pd.DataFrame) -> pd.DataFrame:
    if comments.empty:
        return pd.DataFrame(
            columns=["sentiment_label", "sample_count", "avg_like_count", "median_like_count"]
        )
    grouped = (
        comments.groupby("sentiment_label")
        .agg(
            sample_count=("comment_id", "size"),
            avg_like_count=("like_count", "mean"),
            median_like_count=("like_count", "median"),
        )
        .reset_index()
    )
    grouped["avg_like_count"] = grouped["avg_like_count"].round(2)
    grouped["median_like_count"] = grouped["median_like_count"].round(2)
    return grouped


def _format_number(value: int | float) -> str:
    return f"{int(value):,}"


def build_insights(
    video: pd.Series,
    interaction_metrics: pd.DataFrame,
    timeline: pd.DataFrame,
    keyword_metrics: pd.DataFrame,
    danmaku_keyword_compare: pd.DataFrame,
    danmaku_cleaning_summary: pd.DataFrame,
    sentiment_metrics: pd.DataFrame,
    comment_like_sentiment: pd.DataFrame,
) -> str:
    top_peaks = timeline.sort_values("danmaku_count", ascending=False).head(3)
    peak_text = "、".join(
        f"{row.time_range}({int(row.danmaku_count)}条)"
        for row in top_peaks.itertuples(index=False)
    )
    danmaku_before_keywords = (
        danmaku_keyword_compare[
            danmaku_keyword_compare["stage"] == "before_lottery_filter"
        ]
        .head(8)["keyword"]
        .tolist()
    )
    danmaku_after_keywords = (
        danmaku_keyword_compare[
            danmaku_keyword_compare["stage"] == "after_lottery_filter"
        ]
        .head(8)["keyword"]
        .tolist()
    )
    comment_keywords = (
        keyword_metrics[keyword_metrics["source_type"] == "comment"]
        .head(8)["keyword"]
        .tolist()
    )
    overall_rate = interaction_metrics.loc[
        interaction_metrics["metric_name"] == "overall_interaction_rate", "metric_rate"
    ]
    overall_rate_value = float(overall_rate.iloc[0]) if not overall_rate.empty else 0
    best_metric = interaction_metrics[
        interaction_metrics["metric_name"] != "overall_interaction_rate"
    ].sort_values("metric_rate", ascending=False)
    best_metric_text = "暂无"
    if not best_metric.empty:
        row = best_metric.iloc[0]
        best_metric_text = f"{row['metric_label']}最高，约为 {row['metric_rate']:.2%}"

    sentiment_lines = []
    for source_type, source_label in [("danmaku", "弹幕"), ("comment", "评论")]:
        source_metrics = sentiment_metrics[sentiment_metrics["source_type"] == source_type]
        if source_metrics.empty:
            continue
        parts = [
            f"{row.sentiment_label}{row.ratio:.1%}"
            for row in source_metrics.itertuples(index=False)
        ]
        sentiment_lines.append(f"{source_label}情绪分布为" + "、".join(parts))

    like_line = ""
    if not comment_like_sentiment.empty:
        top_like_group = comment_like_sentiment.sort_values(
            "avg_like_count", ascending=False
        ).iloc[0]
        like_line = (
            f"按评论点赞均值看，{top_like_group['sentiment_label']}评论的平均点赞数最高，"
            f"约 {top_like_group['avg_like_count']}。"
        )

    lottery_line = "抽奖弹幕过滤样本不足。"
    if not danmaku_cleaning_summary.empty:
        summary = danmaku_cleaning_summary.iloc[0]
        lottery_line = (
            f"弹幕二次清洗识别并过滤抽奖参与弹幕 {int(summary['lottery_filtered_count']):,} 条，"
            f"过滤比例约 {float(summary['filter_ratio']):.1%}；清洗后保留内容讨论弹幕 "
            f"{int(summary['content_discussion_count']):,} 条。"
        )

    lines = [
        f"1. 本项目分析视频《{video.get('title', '')}》，公开视频播放量为 {_format_number(video.get('view_count', 0))}，评论数为 {_format_number(video.get('reply_count', 0))}，弹幕数为 {_format_number(video.get('danmaku_count', 0))}。",
        f"2. 样本数据包含公开弹幕 {int(timeline['danmaku_count'].sum()) if not timeline.empty else 0:,} 条、公开评论样本 {int(comment_like_sentiment['sample_count'].sum()) if not comment_like_sentiment.empty else 0:,} 条；综合互动率约为 {overall_rate_value:.2%}，{best_metric_text}。",
        f"3. 弹幕密度最高的时间段集中在：{peak_text or '暂无'}，可作为定位视频高讨论片段的依据。",
        f"4. 抽奖活动对弹幕关键词造成明显干扰，清洗前高频词包括：{'、'.join(danmaku_before_keywords) or '暂无'}；清洗后更接近内容讨论，高频词包括：{'、'.join(danmaku_after_keywords) or '暂无'}。",
        f"5. {lottery_line}",
        f"6. 评论高频词包括：{'、'.join(comment_keywords) or '暂无'}。{'；'.join(sentiment_lines) or '情绪样本不足'}。{like_line}",
        "7. 弹幕抽奖识别使用可解释的业务规则；情绪识别基于 SnowNLP 的轻量级中文情感模型，结果适合做作品展示和探索性分析，不代表严格的舆情模型结论。",
    ]
    return "\n".join(lines)


def _write_wordcloud(frequencies: dict[str, int], filename: str, font_path: Path) -> None:
    if not frequencies:
        return
    from wordcloud import WordCloud

    cloud = WordCloud(
        font_path=str(font_path),
        width=1200,
        height=720,
        background_color="white",
        colormap="viridis",
        max_words=80,
    ).generate_from_frequencies(frequencies)
    cloud.to_file(str(SCREENSHOT_DIR / filename))


def generate_wordcloud(
    keyword_metrics: pd.DataFrame,
    danmaku_keyword_compare: pd.DataFrame,
) -> None:
    try:
        from wordcloud import WordCloud  # noqa: F401
    except Exception:
        return

    font_candidates = [
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    ]
    font_path = next((path for path in font_candidates if path.exists()), None)
    if not font_path:
        return

    before = danmaku_keyword_compare[
        danmaku_keyword_compare["stage"] == "before_lottery_filter"
    ]
    after = danmaku_keyword_compare[
        danmaku_keyword_compare["stage"] == "after_lottery_filter"
    ]
    _write_wordcloud(
        dict(zip(before["keyword"], before["word_count"])),
        "danmaku_wordcloud_before.png",
        font_path,
    )
    _write_wordcloud(
        dict(zip(after["keyword"], after["word_count"])),
        "danmaku_wordcloud_after.png",
        font_path,
    )

    after_path = SCREENSHOT_DIR / "danmaku_wordcloud_after.png"
    legacy_path = SCREENSHOT_DIR / "danmaku_wordcloud.png"
    if after_path.exists():
        shutil.copyfile(after_path, legacy_path)

    comment = keyword_metrics[keyword_metrics["source_type"] == "comment"]
    _write_wordcloud(
        dict(zip(comment["keyword"], comment["word_count"])),
        "comment_wordcloud.png",
        font_path,
    )


def process_all() -> None:
    ensure_directories()
    video_frame = pd.read_csv(PROCESSED_DIR / "video_info.csv")
    video = video_frame.iloc[0]
    duration_seconds = int(video.get("duration_seconds", 0) or 0)

    danmaku = pd.read_csv(PROCESSED_DIR / "danmaku_raw.csv")
    raw_danmaku_count = len(danmaku)
    if not danmaku.empty:
        danmaku = danmaku[danmaku["video_time"].between(0, max(duration_seconds, 1))].copy()
        danmaku["clean_text"] = danmaku["danmaku_text"].map(clean_text)
        danmaku = danmaku[danmaku["clean_text"] != ""].copy()
        danmaku["is_lottery_danmaku"] = danmaku["clean_text"].map(is_lottery_danmaku)
        danmaku["content_clean_text"] = danmaku["clean_text"].where(
            ~danmaku["is_lottery_danmaku"], ""
        )
        danmaku["sentiment_score"] = danmaku["clean_text"].map(sentiment_score)
        danmaku["sentiment_label"] = danmaku["sentiment_score"].map(sentiment_label)
    else:
        danmaku["is_lottery_danmaku"] = []
        danmaku["content_clean_text"] = []
    danmaku.to_csv(PROCESSED_DIR / "danmaku_clean.csv", index=False, encoding="utf-8-sig")

    content_danmaku = danmaku[danmaku["content_clean_text"] != ""].copy()
    lottery_filtered_count = int(danmaku["is_lottery_danmaku"].sum()) if not danmaku.empty else 0
    danmaku_cleaning_summary = build_danmaku_cleaning_summary(
        raw_count=raw_danmaku_count,
        basic_clean_count=len(danmaku),
        lottery_count=lottery_filtered_count,
        content_count=len(content_danmaku),
    )
    danmaku_cleaning_summary.to_csv(
        PROCESSED_DIR / "danmaku_cleaning_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    comments = pd.read_csv(PROCESSED_DIR / "comments_raw.csv")
    if not comments.empty:
        comments["clean_text"] = comments["comment_text"].map(clean_text)
        comments = comments[comments["clean_text"] != ""].copy()
        comments["sentiment_score"] = comments["clean_text"].map(sentiment_score)
        comments["sentiment_label"] = comments["sentiment_score"].map(sentiment_label)
    comments.to_csv(PROCESSED_DIR / "comments_clean.csv", index=False, encoding="utf-8-sig")

    interaction_metrics = build_interaction_metrics(video)
    interaction_metrics.to_csv(
        PROCESSED_DIR / "interaction_metrics.csv", index=False, encoding="utf-8-sig"
    )

    timeline = build_danmaku_timeline(danmaku, duration_seconds)
    timeline.to_csv(PROCESSED_DIR / "danmaku_timeline.csv", index=False, encoding="utf-8-sig")
    timeline.sort_values("danmaku_count", ascending=False).head(10).to_csv(
        PROCESSED_DIR / "danmaku_peaks.csv", index=False, encoding="utf-8-sig"
    )

    danmaku_keyword_before = build_keyword_frame(
        "before_lottery_filter", danmaku["clean_text"], TEXT_ANALYSIS_TOP_N
    ).rename(columns={"source_type": "stage"})
    danmaku_keyword_after = build_keyword_frame(
        "after_lottery_filter", content_danmaku["content_clean_text"], TEXT_ANALYSIS_TOP_N
    ).rename(columns={"source_type": "stage"})
    danmaku_keyword_compare = pd.concat(
        [danmaku_keyword_before, danmaku_keyword_after],
        ignore_index=True,
    )
    danmaku_keyword_compare.to_csv(
        PROCESSED_DIR / "danmaku_keyword_compare.csv",
        index=False,
        encoding="utf-8-sig",
    )

    keyword_metrics = pd.concat(
        [
            build_keyword_frame(
                "danmaku", content_danmaku["content_clean_text"], TEXT_ANALYSIS_TOP_N
            ),
            build_keyword_frame("comment", comments["clean_text"], TEXT_ANALYSIS_TOP_N),
        ],
        ignore_index=True,
    )
    keyword_metrics.to_csv(
        PROCESSED_DIR / "keyword_metrics.csv", index=False, encoding="utf-8-sig"
    )
    keyword_metrics.to_csv(
        PROCESSED_DIR / "tableau_text_keywords.csv", index=False, encoding="utf-8-sig"
    )

    sentiment_metrics = pd.concat(
        [
            build_sentiment_metrics("danmaku", danmaku),
            build_sentiment_metrics("comment", comments),
        ],
        ignore_index=True,
    )
    sentiment_metrics.to_csv(
        PROCESSED_DIR / "sentiment_metrics.csv", index=False, encoding="utf-8-sig"
    )

    comment_like_sentiment = build_comment_like_sentiment(comments)
    comment_like_sentiment.to_csv(
        PROCESSED_DIR / "comment_like_sentiment.csv", index=False, encoding="utf-8-sig"
    )

    tableau_timeline = timeline.copy()
    tableau_timeline["bvid"] = video.get("bvid", "")
    tableau_timeline["title"] = video.get("title", "")
    tableau_timeline.to_csv(
        PROCESSED_DIR / "tableau_danmaku_timeline.csv", index=False, encoding="utf-8-sig"
    )

    insights = build_insights(
        video=video,
        interaction_metrics=interaction_metrics,
        timeline=timeline,
        keyword_metrics=keyword_metrics,
        danmaku_keyword_compare=danmaku_keyword_compare,
        danmaku_cleaning_summary=danmaku_cleaning_summary,
        sentiment_metrics=sentiment_metrics,
        comment_like_sentiment=comment_like_sentiment,
    )
    (PROCESSED_DIR / "analysis_insights.txt").write_text(insights, encoding="utf-8")
    generate_wordcloud(keyword_metrics, danmaku_keyword_compare)

    print(f"[process] danmaku_clean: {len(danmaku):,} rows")
    print(f"[process] danmaku_lottery_filtered: {lottery_filtered_count:,} rows")
    print(f"[process] danmaku_content_discussion: {len(content_danmaku):,} rows")
    print(f"[process] comments_clean: {len(comments):,} rows")
    print("[process] metrics and insights generated")


if __name__ == "__main__":
    process_all()
