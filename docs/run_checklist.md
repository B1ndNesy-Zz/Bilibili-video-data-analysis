# 运行检查清单

- `python -m compileall config scripts app` 通过。
- `python scripts/run_pipeline.py --max-comments 2000` 可完成公开数据采集、清洗、指标生成和 MySQL 入库。
- MySQL 数据库 `bilibili_video_analysis` 中有 13 张核心表。
- `video_info` 1 行，`danmaku_info` 3523 行，`comment_info` 1947 行。
- 新增 MySQL 表 `danmaku_cleaning_summary` 1 行，`danmaku_keyword_compare` 60 行。
- 手机反馈 MySQL 表已生成：`phone_feedback_summary` 14 行，`phone_feedback_sentiment` 34 行，`phone_feedback_keywords` 413 行，`phone_feedback_examples` 40 行。
- `danmaku_cleaning_summary.csv` 显示基础清洗弹幕 3523 条、过滤抽奖/刷屏/广告噪声弹幕 3098 条、内容讨论弹幕 425 条。
- `danmaku_keyword_compare.csv` 可展示弹幕关键词清洗前后对比。
- `phone_feedback_summary.csv` 显示评论手机反馈 245 条、弹幕手机反馈 41 条，最热主题为影像相机。
- `comments_clean.csv` 和 `danmaku_clean.csv` 均包含 `is_noise_text`、`is_phone_feedback`、`phone_feedback_topic` 字段。
- `data/processed/analysis_insights.txt` 生成真实结论。
- `python app/app.py` 后可访问 `http://127.0.0.1:5001`。
- `/api/health` 返回 `ok=true`。
- 新增 API `/api/phone-feedback-summary`、`/api/phone-feedback-sentiment`、`/api/phone-feedback-keywords`、`/api/phone-feedback-examples` 均可返回数据。
- Playwright 已生成 `docs/screenshots/dashboard_overview.png`。
- `.env` 未纳入 Git 跟踪范围，评论和弹幕明细文件不上传 GitHub；本地文件不包含用户昵称、用户 ID、头像、主页等身份字段。
