from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"
SCREENSHOT_DIR = DOCS_DIR / "screenshots"
SQL_DIR = PROJECT_ROOT / "sql"

load_dotenv(PROJECT_ROOT / ".env")

VIDEO_CONFIG = {
    "bvid": "BV1Enpxz5Ef3",
    "aid": 115218420078806,
    "cid": 33272367686,
    "video_url": "https://www.bilibili.com/video/BV1Enpxz5Ef3/",
    "up_name": "影视飓风",
    "up_mid": 946974,
}

BILIBILI_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": VIDEO_CONFIG["video_url"],
    "Accept": "application/json, text/plain, */*",
}

BILI_COOKIE = os.getenv("BILI_COOKIE", "").strip()
if BILI_COOKIE:
    BILIBILI_HEADERS["Cookie"] = BILI_COOKIE

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "bilibili_video_analysis"),
    "charset": "utf8mb4",
}

STOPWORDS = {
    "一个",
    "一些",
    "一下",
    "一样",
    "不是",
    "不能",
    "不要",
    "他们",
    "你们",
    "我们",
    "这个",
    "那个",
    "这里",
    "就是",
    "还是",
    "可以",
    "已经",
    "真的",
    "感觉",
    "因为",
    "所以",
    "但是",
    "然后",
    "如果",
    "没有",
    "什么",
    "怎么",
    "这么",
    "那么",
    "直接",
    "现在",
    "看到",
    "视频",
    "弹幕",
    "评论",
    "哈哈",
    "哈哈哈",
    "啊啊",
    "啊啊啊",
    "doge",
    "b站",
    "bilibili",
    "up",
    "up主",
}

TEXT_ANALYSIS_TOP_N = 30
COMMENT_TARGET_COUNT = 2500
COMMENT_PAGE_SIZE = 20
DANMAKU_BUCKET_SECONDS = 30


def ensure_directories() -> None:
    for path in [RAW_DIR, PROCESSED_DIR, DOCS_DIR, SCREENSHOT_DIR, SQL_DIR]:
        path.mkdir(parents=True, exist_ok=True)
