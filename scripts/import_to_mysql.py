from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pymysql

import path_setup  # noqa: F401
from config.settings import MYSQL_CONFIG, PROCESSED_DIR, SQL_DIR


TABLE_FILES = {
    "video_info": "video_info.csv",
    "danmaku_info": "danmaku_clean.csv",
    "comment_info": "comments_clean.csv",
    "interaction_metrics": "interaction_metrics.csv",
    "danmaku_timeline": "danmaku_timeline.csv",
    "keyword_metrics": "keyword_metrics.csv",
    "danmaku_cleaning_summary": "danmaku_cleaning_summary.csv",
    "danmaku_keyword_compare": "danmaku_keyword_compare.csv",
    "sentiment_metrics": "sentiment_metrics.csv",
    "phone_feedback_summary": "phone_feedback_summary.csv",
    "phone_feedback_sentiment": "phone_feedback_sentiment.csv",
    "phone_feedback_keywords": "phone_feedback_keywords.csv",
    "phone_feedback_examples": "phone_feedback_examples.csv",
}

TABLE_COLUMNS = {
    "video_info": [
        "bvid",
        "aid",
        "cid",
        "title",
        "up_name",
        "up_mid",
        "duration_seconds",
        "view_count",
        "danmaku_count",
        "reply_count",
        "favorite_count",
        "coin_count",
        "share_count",
        "like_count",
        "his_rank",
        "collect_time",
    ],
    "danmaku_info": [
        "bvid",
        "cid",
        "video_time",
        "video_minute",
        "time_bucket_30s",
        "danmaku_text",
        "clean_text",
        "is_noise_text",
        "is_phone_feedback",
        "phone_feedback_topic",
        "sentiment_score",
        "sentiment_label",
        "send_time",
        "mode",
        "font_size",
        "color",
        "collect_time",
    ],
    "comment_info": [
        "comment_id",
        "bvid",
        "aid",
        "comment_text",
        "clean_text",
        "is_noise_text",
        "is_phone_feedback",
        "phone_feedback_topic",
        "like_count",
        "reply_count",
        "comment_time",
        "sentiment_score",
        "sentiment_label",
        "collect_time",
    ],
    "interaction_metrics": [
        "metric_name",
        "metric_label",
        "metric_value",
        "metric_rate",
    ],
    "danmaku_timeline": [
        "time_bucket_30s",
        "start_sec",
        "end_sec",
        "start_label",
        "end_label",
        "time_range",
        "danmaku_count",
    ],
    "keyword_metrics": ["source_type", "keyword", "word_count", "rank_order"],
    "danmaku_cleaning_summary": [
        "raw_sample_count",
        "basic_clean_count",
        "lottery_filtered_count",
        "content_discussion_count",
        "filter_ratio",
        "retain_ratio",
    ],
    "danmaku_keyword_compare": ["stage", "keyword", "word_count", "rank_order"],
    "sentiment_metrics": [
        "source_type",
        "sentiment_label",
        "sample_count",
        "ratio",
        "avg_score",
    ],
    "phone_feedback_summary": [
        "source_type",
        "source_label",
        "phone_feedback_topic",
        "sample_count",
        "source_total_count",
        "feedback_total_count",
        "source_ratio",
        "topic_ratio",
        "avg_sentiment_score",
    ],
    "phone_feedback_sentiment": [
        "source_type",
        "source_label",
        "phone_feedback_topic",
        "sentiment_label",
        "sample_count",
        "topic_total_count",
        "ratio",
    ],
    "phone_feedback_keywords": [
        "source_type",
        "source_label",
        "phone_feedback_topic",
        "keyword",
        "word_count",
        "rank_order",
    ],
    "phone_feedback_examples": [
        "source_type",
        "source_label",
        "phone_feedback_topic",
        "feedback_text",
        "like_count",
        "reply_count",
        "video_time",
        "video_time_label",
        "sentiment_label",
        "sentiment_score",
        "rank_order",
    ],
}

SCHEMA_COMPAT_COLUMNS = {
    "danmaku_info": {
        "is_noise_text": "TINYINT(1) DEFAULT 0",
        "is_phone_feedback": "TINYINT(1) DEFAULT 0",
        "phone_feedback_topic": "VARCHAR(32)",
    },
    "comment_info": {
        "is_noise_text": "TINYINT(1) DEFAULT 0",
        "is_phone_feedback": "TINYINT(1) DEFAULT 0",
        "phone_feedback_topic": "VARCHAR(32)",
    },
}


def _connect(with_database: bool = True):
    config = MYSQL_CONFIG.copy()
    if not with_database:
        config.pop("database", None)
    return pymysql.connect(**config)


def _split_sql_statements(sql_text: str) -> list[str]:
    statements = []
    for part in sql_text.split(";"):
        statement = part.strip()
        if statement:
            statements.append(statement)
    return statements


def init_schema() -> None:
    schema_path = SQL_DIR / "schema.sql"
    sql_text = schema_path.read_text(encoding="utf-8")
    with _connect(with_database=False) as connection:
        with connection.cursor() as cursor:
            for statement in _split_sql_statements(sql_text):
                cursor.execute(statement)
        connection.commit()
    print("[mysql] schema initialized")


def ensure_schema_compatibility(connection) -> None:
    with connection.cursor() as cursor:
        for table_name, columns in SCHEMA_COMPAT_COLUMNS.items():
            for column_name, column_sql in columns.items():
                cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE %s", (column_name,))
                if cursor.fetchone():
                    continue
                cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_sql}")
                print(f"[mysql] added column {table_name}.{column_name}")
    connection.commit()


def _prepare_frame(path: Path, columns: list[str]) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{path.name} missing columns: {missing}")
    frame = frame[columns].copy()
    frame = frame.astype(object).where(pd.notna(frame), None)
    return frame


def _insert_frame(cursor: Any, table_name: str, frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    columns = list(frame.columns)
    column_sql = ", ".join(f"`{column}`" for column in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO `{table_name}` ({column_sql}) VALUES ({placeholders})"
    values = [tuple(row) for row in frame.itertuples(index=False, name=None)]
    cursor.executemany(sql, values)
    return len(values)


def import_all() -> None:
    init_schema()
    with _connect(with_database=True) as connection:
        ensure_schema_compatibility(connection)
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS=0")
            for table_name in TABLE_FILES:
                cursor.execute(f"TRUNCATE TABLE `{table_name}`")
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")

            for table_name, filename in TABLE_FILES.items():
                path = PROCESSED_DIR / filename
                frame = _prepare_frame(path, TABLE_COLUMNS[table_name])
                inserted = _insert_frame(cursor, table_name, frame)
                print(f"[mysql] {table_name}: {inserted:,} rows")
        connection.commit()


if __name__ == "__main__":
    import_all()
