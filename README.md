# B站爆款视频弹幕互动与评论情绪分析

本项目围绕影视飓风单条爆款视频《外观变了，值得买吗？iPhone 17 Pro&Air评测》做公开视频数据分析，覆盖数据采集、清洗、文本分析、MySQL 入库和 Flask + Echarts 可视化看板。

## 项目成果预览

点开仓库即可先看到完整看板效果：

![B站视频数据分析看板](docs/screenshots/dashboard_overview.png)

弹幕词云清洗前后对比：

| 弹幕词云：清洗前 | 弹幕词云：清洗后 |
| --- | --- |
| ![清洗前](docs/screenshots/danmaku_wordcloud_before.png) | ![清洗后](docs/screenshots/danmaku_wordcloud_after.png) |

评论词云：

![评论词云](docs/screenshots/comment_wordcloud.png)

## 项目背景

短视频和中长视频平台的用户反馈通常分散在播放量、点赞、投币、收藏、评论和弹幕中。单看播放量只能判断传播规模，不能解释用户讨论集中在哪些片段、评论关注什么主题、整体情绪偏向如何。

本项目选择一条播放量较高的 B 站公开视频，构建一套可复现的数据分析流程，用于展示 Python 爬虫、pandas 清洗、中文文本分析、MySQL 建模和 Web 可视化能力。

## 分析对象

| 字段 | 内容 |
| --- | --- |
| 视频 | 外观变了，值得买吗？iPhone 17 Pro&Air评测 |
| BV号 | BV1Enpxz5Ef3 |
| UP主 | 影视飓风 |
| aid | 115218420078806 |
| cid | 33272367686 |
| 视频时长 | 1815 秒，约 30 分 15 秒 |
| 采集日期 | 2026-04-17 |

公开视频统计数据会随时间变化，README 中的结论以本次运行生成的 CSV 和 MySQL 数据为准。

## 技术栈

- Python：requests、pandas、jieba、SnowNLP、wordcloud
- 数据库：MySQL 8
- 后端：Flask
- 前端：Echarts、HTML、CSS、JavaScript
- 数据文件：CSV、JSONL

## 数据来源与隐私处理

数据来源均为公开视频公开接口：

- 视频基础信息：`https://api.bilibili.com/x/web-interface/view`
- 弹幕样本：`https://comment.bilibili.com/{cid}.xml`
- 评论样本：B 站公开视频评论 WBI 接口

隐私处理策略：

- 不保存用户昵称、用户 ID、头像、主页等身份字段。
- 评论只保存文本、点赞数、回复数、评论时间等分析字段。
- 弹幕只保存文本、视频时间、发送时间、样式字段等分析字段。
- `.env`、Cookie 和本地数据库密码不会提交到 GitHub。
- GitHub 仓库不上传评论/弹幕明细和 raw 文件，只保留代码、文档、截图和聚合指标；明细数据可通过脚本在本地重新生成。

## 为什么要做弹幕与手机反馈二次清洗

该视频存在抽奖活动，公开弹幕和评论中有较多“抽奖、中奖、参与、求中、抽中”等参与型文本，也存在“中、抽我、1111、oi”等刷屏弹幕。这类文本反映活动参与行为，但不代表用户对手机产品本身的反馈。

如果直接基于弹幕和评论做词云和关键词统计，抽奖相关词、复制段子和广告会淹没真实内容反馈。因此项目新增可解释规则：先整条过滤抽奖、刷屏、广告等噪声，再从剩余文本中筛选“手机真实反馈”，并按外观设计、影像相机、性能散热、屏幕手感、续航充电、系统功能、价格购买、竞品对比 8 个主题做聚合分析。该规则是可复现的数据分析口径，不是语义分类模型。

## 核心指标

互动率指标：

```text
点赞率 = 点赞数 / 播放量
投币率 = 投币数 / 播放量
收藏率 = 收藏数 / 播放量
分享率 = 分享数 / 播放量
评论率 = 评论数 / 播放量
弹幕率 = 弹幕数 / 播放量
综合互动率 = (点赞 + 投币 + 收藏 + 分享 + 评论 + 弹幕) / 播放量
```

文本分析指标：

- 弹幕时间轴：按 30 秒聚合弹幕数量。
- 弹幕高峰片段：弹幕数量最高的 TOP 10 时间段。
- 高频关键词：对弹幕和评论分别进行 jieba 分词、停用词过滤和词频统计。
- 弹幕二次清洗：识别抽奖、刷屏、广告弹幕并整条过滤，用清洗前后对比体现活动噪声对文本分析的干扰。
- 手机反馈主题：从弹幕和评论中筛选手机相关反馈，并按 8 个产品主题聚合样本量、情绪和代表文本。
- 评论情绪：使用 SnowNLP 生成情绪分数，并划分为正向、中性、负向。

## 本次运行结果

| 数据项 | 数值 |
| --- | ---: |
| 播放量 | 15,366,018 |
| 点赞数 | 961,581 |
| 投币数 | 863,150 |
| 收藏数 | 306,020 |
| 分享数 | 272,268 |
| 评论数 | 184,449 |
| 弹幕数 | 685,279 |
| 公开弹幕样本 | 3,523 |
| 公开评论样本 | 1,947 |
| 噪声弹幕过滤数 | 3,098 |
| 内容讨论弹幕数 | 425 |
| 手机反馈评论 | 245 |
| 手机反馈弹幕 | 41 |

主要结论：

1. 综合互动率约为 21.30%，其中点赞率约为 6.26%，投币率约为 5.62%。
2. 弹幕密度最高的时间段为 00:00-00:30、12:00-12:30、28:30-29:00，说明开头、核心评测段和结尾互动较集中。
3. 视频抽奖活动会显著影响弹幕词云，清洗前高频词中包含大量抽奖参与词；本次过滤 3,098 条抽奖、刷屏和广告噪声弹幕后，关键词更接近内容讨论。
4. 本次筛选出手机真实反馈评论 245 条、弹幕 41 条；反馈最集中的主题为影像相机、竞品对比和价格购买。
5. 评论样本中正向情绪占比约 58.4%，负向约 24.8%；弹幕样本中正向约 45.8%，负向约 32.6%。
6. 情绪识别、噪声过滤和手机反馈分类均为轻量级探索性分析，适合求职作品展示，不代表严格舆情模型结论。

## 项目结构

```text
bilibili_video_analysis/
  app/
    app.py
    static/
    templates/
  config/
    settings.py
  data/
    raw/
    processed/
  docs/
    screenshots/
    interview_script.md
    resume_project.md
  scripts/
    collect_bilibili.py
    process_data.py
    import_to_mysql.py
    run_pipeline.py
  sql/
    schema.sql
  README.md
  requirements.txt
  .env.example
```

## 运行步骤

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 复制并配置环境变量：

```bash
copy .env.example .env
```

填写本地 MySQL 配置：

```text
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=bilibili_video_analysis
```

3. 运行完整管道：

```bash
python scripts/run_pipeline.py --max-comments 2000
```

4. 启动看板：

```bash
python app/app.py
```

浏览器打开：

```text
http://127.0.0.1:5001
```

## 输出文件

核心输出：

- `data/processed/video_info.csv`
- `data/processed/interaction_metrics.csv`
- `data/processed/danmaku_timeline.csv`
- `data/processed/danmaku_cleaning_summary.csv`
- `data/processed/danmaku_keyword_compare.csv`
- `data/processed/keyword_metrics.csv`
- `data/processed/phone_feedback_summary.csv`
- `data/processed/phone_feedback_sentiment.csv`
- `data/processed/phone_feedback_keywords.csv`
- `data/processed/phone_feedback_examples.csv`
- `data/processed/sentiment_metrics.csv`
- `data/processed/analysis_insights.txt`

本地运行后还会生成 `comments_clean.csv`、`danmaku_clean.csv` 和 `data/raw/` 下的采集样本。清洗明细中包含 `is_noise_text`、`is_phone_feedback`、`phone_feedback_topic` 字段，便于复核手机反馈筛选口径。为了避免在公开仓库中长期保存评论/弹幕明细文本，这些文件默认被 `.gitignore` 排除。

MySQL 入库表：

- `video_info`：视频基础信息。
- `danmaku_info`：本地弹幕明细表，不上传 GitHub。
- `comment_info`：本地评论明细表，不上传 GitHub。
- `interaction_metrics`：互动率指标。
- `danmaku_timeline`：弹幕时间轴。
- `keyword_metrics`：清洗后关键词指标。
- `danmaku_cleaning_summary`：弹幕抽奖噪声清洗摘要。
- `danmaku_keyword_compare`：弹幕关键词清洗前后对比。
- `sentiment_metrics`：情绪分布指标。
- `phone_feedback_summary`：手机反馈主题样本量和占比。
- `phone_feedback_sentiment`：手机反馈主题情绪分布。
- `phone_feedback_keywords`：手机反馈口径下的关键词。
- `phone_feedback_examples`：手机反馈代表性评论和弹幕。

展示材料：

- `docs/screenshots/dashboard_overview.png`
- `docs/screenshots/danmaku_wordcloud_before.png`
- `docs/screenshots/danmaku_wordcloud_after.png`
- `docs/screenshots/comment_wordcloud.png`
- `docs/interview_script.md`
- `docs/resume_project.md`

## 可视化看板

看板包含：

- 视频概览指标卡
- 互动率结构柱状图
- 评论情绪环形图
- 弹幕 30 秒时间轴
- 弹幕高峰片段 TOP 10
- 弹幕抽奖与刷屏噪声清洗摘要
- 手机真实反馈主题分布
- 手机反馈主题情绪
- 手机反馈关键词
- 代表性反馈样本
- 弹幕关键词清洗前后对比
- 评论情绪与平均点赞
- 评论关键词原始口径 TOP 30
- 自动生成分析结论

## 项目不足与后续优化

- 第一版只使用公开接口，不使用 Cookie，因此评论不是全量评论，只是公开分页样本。
- SnowNLP 情绪分类适合快速探索，但对 B 站语境、反讽、梗文化识别有限。
- 可以继续加入视频章节识别，把弹幕高峰与具体内容片段关联起来。
- 可以扩展到同 UP 主多条视频，对比不同选题的互动表现和评论情绪。
- 可以将 Tableau 作为补充展示，将 CSV 导入后制作更细的交互式分析页。
