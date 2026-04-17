from __future__ import annotations

import json
import hashlib
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

import path_setup  # noqa: F401
from config.settings import (
    BILIBILI_HEADERS,
    COMMENT_PAGE_SIZE,
    COMMENT_TARGET_COUNT,
    PROCESSED_DIR,
    RAW_DIR,
    VIDEO_CONFIG,
    ensure_directories,
)


VIEW_API = "https://api.bilibili.com/x/web-interface/view"
DANMAKU_XML_API = "https://comment.bilibili.com/{cid}.xml"
COMMENT_WBI_MAIN_API = "https://api.bilibili.com/x/v2/reply/wbi/main"
COMMENT_MAIN_API = "https://api.bilibili.com/x/v2/reply/main"
COMMENT_FALLBACK_API = "https://api.bilibili.com/x/v2/reply"
NAV_API = "https://api.bilibili.com/x/web-interface/nav"

MIXIN_KEY_ENC_TAB = [
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
]

_WBI_MIXIN_KEY: str | None = None


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _from_timestamp(value: Any) -> str | None:
    try:
        if value in (None, "", 0, "0"):
            return None
        return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return None


def _get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.get(
        url,
        params=params,
        headers=BILIBILI_HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def _get_wbi_mixin_key() -> str:
    global _WBI_MIXIN_KEY
    if _WBI_MIXIN_KEY:
        return _WBI_MIXIN_KEY

    payload = _get_json(NAV_API)
    wbi_img = (payload.get("data") or {}).get("wbi_img") or {}
    img_key = Path(wbi_img.get("img_url", "")).stem
    sub_key = Path(wbi_img.get("sub_url", "")).stem
    raw_key = img_key + sub_key
    if len(raw_key) < 64:
        raise RuntimeError("Failed to get Bilibili WBI key")
    _WBI_MIXIN_KEY = "".join(raw_key[index] for index in MIXIN_KEY_ENC_TAB)[:32]
    return _WBI_MIXIN_KEY


def _sign_wbi_params(params: dict[str, Any]) -> dict[str, Any]:
    mixin_key = _get_wbi_mixin_key()
    signed = {key: str(value) for key, value in params.items()}
    signed["wts"] = str(int(time.time()))
    signed = {
        key: "".join(char for char in value if char not in "!'()*")
        for key, value in signed.items()
    }
    query = urllib.parse.urlencode(sorted(signed.items()))
    signed["w_rid"] = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
    return signed


def collect_video_info() -> pd.DataFrame:
    params = {"bvid": VIDEO_CONFIG["bvid"]}
    payload = _get_json(VIEW_API, params=params)
    if payload.get("code") != 0:
        raise RuntimeError(f"Video API failed: {payload}")

    data = payload["data"]
    stat = data.get("stat", {})
    owner = data.get("owner", {})
    row = {
        "bvid": data.get("bvid") or VIDEO_CONFIG["bvid"],
        "aid": data.get("aid") or VIDEO_CONFIG["aid"],
        "cid": data.get("cid") or VIDEO_CONFIG["cid"],
        "title": data.get("title", ""),
        "up_name": owner.get("name") or VIDEO_CONFIG["up_name"],
        "up_mid": owner.get("mid") or VIDEO_CONFIG["up_mid"],
        "duration_seconds": data.get("duration", 0),
        "view_count": stat.get("view", 0),
        "danmaku_count": stat.get("danmaku", 0),
        "reply_count": stat.get("reply", 0),
        "favorite_count": stat.get("favorite", 0),
        "coin_count": stat.get("coin", 0),
        "share_count": stat.get("share", 0),
        "like_count": stat.get("like", 0),
        "his_rank": stat.get("his_rank", 0),
        "collect_time": _now_text(),
    }

    raw_payload = {
        "code": payload.get("code"),
        "message": payload.get("message"),
        "data": row,
    }
    (RAW_DIR / "video_info_raw.json").write_text(
        json.dumps(raw_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    frame = pd.DataFrame([row])
    frame.to_csv(PROCESSED_DIR / "video_info.csv", index=False, encoding="utf-8-sig")
    print(f"[collect] video_info: {row['title']} | views={row['view_count']:,}")
    return frame


def collect_danmaku() -> pd.DataFrame:
    cid = VIDEO_CONFIG["cid"]
    response = requests.get(
        DANMAKU_XML_API.format(cid=cid),
        headers={**BILIBILI_HEADERS, "Accept": "application/xml,text/xml,*/*"},
        timeout=30,
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    rows: list[dict[str, Any]] = []
    collect_time = _now_text()
    for index, node in enumerate(root.findall("d"), start=1):
        attrs = (node.attrib.get("p") or "").split(",")
        if len(attrs) < 8:
            continue
        try:
            video_time = float(attrs[0])
        except ValueError:
            continue
        send_time = _from_timestamp(attrs[4])
        row = {
            "sample_id": index,
            "bvid": VIDEO_CONFIG["bvid"],
            "cid": cid,
            "video_time": round(video_time, 3),
            "video_minute": int(video_time // 60),
            "time_bucket_30s": int(video_time // 30) * 30,
            "danmaku_text": (node.text or "").strip(),
            "send_time": send_time,
            "mode": int(float(attrs[1])) if attrs[1] else None,
            "font_size": int(float(attrs[2])) if attrs[2] else None,
            "color": int(float(attrs[3])) if attrs[3] else None,
            "collect_time": collect_time,
        }
        if row["danmaku_text"]:
            rows.append(row)

    frame = pd.DataFrame(rows)
    frame.to_csv(PROCESSED_DIR / "danmaku_raw.csv", index=False, encoding="utf-8-sig")

    raw_path = RAW_DIR / "danmaku_sample_sanitized.jsonl"
    with raw_path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[collect] danmaku sample: {len(frame):,} rows")
    return frame


def _comment_row(reply: dict[str, Any], collect_time: str) -> dict[str, Any] | None:
    content = reply.get("content") or {}
    text = (content.get("message") or "").strip()
    if not text:
        return None
    comment_id = reply.get("rpid_str") or str(reply.get("rpid") or "")
    if not comment_id:
        return None
    return {
        "comment_id": comment_id,
        "bvid": VIDEO_CONFIG["bvid"],
        "aid": VIDEO_CONFIG["aid"],
        "comment_text": text,
        "like_count": int(reply.get("like") or 0),
        "reply_count": int(reply.get("rcount") or reply.get("count") or 0),
        "comment_time": _from_timestamp(reply.get("ctime")),
        "collect_time": collect_time,
    }


def _collect_comments_main(max_comments: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    offset = ""
    collect_time = _now_text()

    for page in range(1, 200):
        params: dict[str, Any] = {
            "type": 1,
            "oid": VIDEO_CONFIG["aid"],
            "mode": 3,
            "plat": 1,
            "ps": COMMENT_PAGE_SIZE,
            "web_location": 1315875,
            "pagination_str": json.dumps(
                {"offset": offset}, ensure_ascii=False, separators=(",", ":")
            ),
        }
        try:
            payload = _get_json(COMMENT_WBI_MAIN_API, params=_sign_wbi_params(params))
        except requests.HTTPError as exc:
            print(f"[collect] comment WBI stopped on page {page}: {exc}")
            break
        if payload.get("code") != 0:
            print(f"[collect] comment main stopped: {payload.get('message')}")
            break

        data = payload.get("data") or {}
        replies = data.get("replies") or []
        for reply in replies:
            row = _comment_row(reply, collect_time)
            if not row or row["comment_id"] in seen:
                continue
            seen.add(row["comment_id"])
            rows.append(row)
            if len(rows) >= max_comments:
                return rows

        cursor = data.get("cursor") or {}
        pagination = cursor.get("pagination_reply") or {}
        next_offset = pagination.get("next_offset") or ""
        if not replies or cursor.get("is_end") or not next_offset or next_offset == offset:
            break
        offset = next_offset
        time.sleep(0.35)

    return rows


def _collect_comments_fallback(max_comments: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    collect_time = _now_text()
    max_pages = max(1, max_comments // COMMENT_PAGE_SIZE + 3)

    for page in range(1, max_pages + 1):
        params = {
            "type": 1,
            "oid": VIDEO_CONFIG["aid"],
            "sort": 2,
            "pn": page,
            "ps": COMMENT_PAGE_SIZE,
        }
        try:
            payload = _get_json(COMMENT_FALLBACK_API, params=params)
        except requests.HTTPError as exc:
            print(f"[collect] comment fallback stopped on page {page}: {exc}")
            break
        if payload.get("code") != 0:
            print(f"[collect] comment fallback stopped: {payload.get('message')}")
            break

        data = payload.get("data") or {}
        replies = data.get("replies") or []
        if not replies:
            break
        for reply in replies:
            row = _comment_row(reply, collect_time)
            if not row or row["comment_id"] in seen:
                continue
            seen.add(row["comment_id"])
            rows.append(row)
            if len(rows) >= max_comments:
                return rows
        time.sleep(0.35)

    return rows


def collect_comments(max_comments: int = COMMENT_TARGET_COUNT) -> pd.DataFrame:
    rows = _collect_comments_main(max_comments=max_comments)
    if len(rows) < min(100, max_comments):
        fallback_rows = _collect_comments_fallback(max_comments=max_comments)
        merged: dict[str, dict[str, Any]] = {row["comment_id"]: row for row in rows}
        for row in fallback_rows:
            merged.setdefault(row["comment_id"], row)
        rows = list(merged.values())[:max_comments]

    frame = pd.DataFrame(rows)
    frame.to_csv(PROCESSED_DIR / "comments_raw.csv", index=False, encoding="utf-8-sig")

    raw_path = RAW_DIR / "comments_public_sanitized.jsonl"
    with raw_path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[collect] comments: {len(frame):,} rows")
    return frame


def collect_all(max_comments: int = COMMENT_TARGET_COUNT) -> None:
    ensure_directories()
    collect_video_info()
    collect_danmaku()
    collect_comments(max_comments=max_comments)


if __name__ == "__main__":
    collect_all()
