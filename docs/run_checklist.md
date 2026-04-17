# 运行检查清单

- `python -m compileall config scripts app` 通过。
- `python scripts/run_pipeline.py --max-comments 2000` 可完成公开数据采集、清洗、指标生成和 MySQL 入库。
- MySQL 数据库 `bilibili_video_analysis` 中有 7 张核心表。
- `video_info` 1 行，`danmaku_info` 3523 行，`comment_info` 1947 行。
- `data/processed/analysis_insights.txt` 生成真实结论。
- `python app/app.py` 后可访问 `http://127.0.0.1:5001`。
- `/api/health` 返回 `ok=true`。
- Playwright 已生成 `docs/screenshots/dashboard_overview.png`。
- `.env` 未纳入 Git 跟踪范围，评论和弹幕明细文件不上传 GitHub；本地文件不包含用户昵称、用户 ID、头像、主页等身份字段。
