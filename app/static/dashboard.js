const chartPalette = ["#128c7e", "#2f6fed", "#e66145", "#d99a21", "#6d5bd0", "#3a8c4d"];

const charts = [];

function numberText(value) {
  const numeric = Number(value || 0);
  return numeric.toLocaleString("zh-CN");
}

function rateText(value) {
  return `${(Number(value || 0) * 100).toFixed(2)}%`;
}

function shortText(value, maxLength = 86) {
  const text = String(value || "");
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} ${response.status}`);
  }
  return response.json();
}

function mountChart(id) {
  const chart = echarts.init(document.getElementById(id));
  charts.push(chart);
  return chart;
}

function renderSummary(video) {
  document.getElementById("video-title").textContent = video.title || "B站爆款视频弹幕互动与评论情绪分析";
  document.getElementById("video-meta").textContent = `${video.up_name || "影视飓风"} · BV号 ${video.bvid || ""} · 样本弹幕 ${numberText(video.sample_danmaku_count)} · 样本评论 ${numberText(video.sample_comment_count)}`;

  const items = [
    ["播放量", video.view_count],
    ["点赞数", video.like_count],
    ["投币数", video.coin_count],
    ["收藏数", video.favorite_count],
    ["评论数", video.reply_count],
    ["弹幕数", video.danmaku_count],
    ["分享数", video.share_count],
    ["历史最高排名", video.his_rank],
  ];
  document.getElementById("summary-grid").innerHTML = items
    .map(([label, value]) => `
      <article class="stat-card">
        <p class="stat-label">${label}</p>
        <p class="stat-value">${numberText(value)}</p>
      </article>
    `)
    .join("");
}

function renderInteraction(data) {
  const chart = mountChart("interaction-chart");
  const visible = data.filter((item) => item.metric_name !== "overall_interaction_rate");
  chart.setOption({
    color: chartPalette,
    tooltip: {
      trigger: "axis",
      formatter(params) {
        const item = params[0].data;
        return `${item.metric_label}<br/>数量：${numberText(item.metric_value)}<br/>比例：${rateText(item.metric_rate)}`;
      },
    },
    grid: { left: 58, right: 24, top: 20, bottom: 52 },
    xAxis: {
      type: "category",
      data: visible.map((item) => item.metric_label),
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      axisLabel: { formatter: (value) => `${(value * 100).toFixed(0)}%` },
      splitLine: { lineStyle: { color: "#e8edf5" } },
    },
    series: [
      {
        type: "bar",
        data: visible.map((item) => ({ ...item, value: Number(item.metric_rate) })),
        barWidth: 28,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      },
    ],
  });
}

function renderSentiment(data) {
  const chart = mountChart("sentiment-chart");
  const comment = data.filter((item) => item.source_type === "comment");
  chart.setOption({
    color: ["#2f6fed", "#d99a21", "#e66145"],
    tooltip: {
      trigger: "item",
      formatter: "{b}: {d}%",
    },
    legend: { bottom: 0 },
    series: [
      {
        type: "pie",
        radius: ["48%", "72%"],
        center: ["50%", "45%"],
        data: comment.map((item) => ({
          name: item.sentiment_label,
          value: item.sample_count,
        })),
        label: {
          formatter: "{b}\n{d}%",
        },
      },
    ],
  });
}

function renderTimeline(data) {
  const chart = mountChart("timeline-chart");
  chart.setOption({
    color: ["#128c7e"],
    tooltip: {
      trigger: "axis",
      formatter(params) {
        const item = params[0].data;
        return `${item.time_range}<br/>弹幕数：${numberText(item.danmaku_count)}`;
      },
    },
    grid: { left: 58, right: 28, top: 24, bottom: 56 },
    dataZoom: [
      { type: "inside", start: 0, end: 100 },
      { type: "slider", height: 22, bottom: 12 },
    ],
    xAxis: {
      type: "category",
      data: data.map((item) => item.start_label),
      boundaryGap: false,
      axisLabel: { interval: 5 },
    },
    yAxis: {
      type: "value",
      name: "弹幕数",
      splitLine: { lineStyle: { color: "#e8edf5" } },
    },
    series: [
      {
        type: "line",
        smooth: true,
        showSymbol: false,
        areaStyle: { opacity: 0.14 },
        data: data.map((item) => ({ ...item, value: item.danmaku_count })),
      },
    ],
  });
}

function renderPeaks(data) {
  const chart = mountChart("peaks-chart");
  const ordered = [...data].reverse();
  chart.setOption({
    color: ["#e66145"],
    tooltip: { trigger: "axis" },
    grid: { left: 92, right: 24, top: 12, bottom: 26 },
    xAxis: { type: "value", splitLine: { lineStyle: { color: "#e8edf5" } } },
    yAxis: {
      type: "category",
      data: ordered.map((item) => item.time_range),
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: ordered.map((item) => item.danmaku_count),
        itemStyle: { borderRadius: [0, 4, 4, 0] },
      },
    ],
  });
}

function renderCommentLike(data) {
  const chart = mountChart("comment-like-chart");
  chart.setOption({
    color: ["#2f6fed"],
    tooltip: { trigger: "axis" },
    grid: { left: 58, right: 28, top: 20, bottom: 42 },
    xAxis: {
      type: "category",
      data: data.map((item) => item.sentiment_label),
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      name: "平均点赞",
      splitLine: { lineStyle: { color: "#e8edf5" } },
    },
    series: [
      {
        type: "bar",
        data: data.map((item) => Number(item.avg_like_count || 0)),
        barWidth: 34,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      },
    ],
  });
}

function renderCleaningSummary(data) {
  const container = document.getElementById("cleaning-summary");
  const items = [
    ["基础清洗弹幕", numberText(data.basic_clean_count)],
    ["噪声弹幕过滤", numberText(data.lottery_filtered_count)],
    ["过滤比例", rateText(data.filter_ratio)],
    ["内容讨论弹幕", numberText(data.content_discussion_count)],
  ];
  container.innerHTML = items
    .map(([label, value]) => `
      <div class="cleaning-card">
        <p>${label}</p>
        <strong>${value}</strong>
      </div>
    `)
    .join("");
}

function renderPhoneFeedbackSummary(data) {
  const container = document.getElementById("phone-feedback-summary");
  const totals = data.reduce((acc, item) => {
    const source = item.source_label || item.source_type;
    if (!acc[source]) {
      acc[source] = {
        feedback: Number(item.feedback_total_count || 0),
        total: Number(item.source_total_count || 0),
      };
    }
    return acc;
  }, {});
  const topicTotals = data.reduce((acc, item) => {
    acc[item.phone_feedback_topic] = (acc[item.phone_feedback_topic] || 0) + Number(item.sample_count || 0);
    return acc;
  }, {});
  const topTopic = Object.entries(topicTotals).sort((a, b) => b[1] - a[1])[0] || ["暂无", 0];
  const items = [
    ...Object.entries(totals).map(([label, value]) => [
      `${label}反馈`,
      `${numberText(value.feedback)} / ${numberText(value.total)}`,
      rateText(value.total ? value.feedback / value.total : 0),
    ]),
    ["最热主题", topTopic[0], `${numberText(topTopic[1])} 条`],
  ];

  container.innerHTML = items
    .map(([label, value, note]) => `
      <div class="feedback-metric">
        <p>${label}</p>
        <strong>${value}</strong>
        <span>${note}</span>
      </div>
    `)
    .join("");
}

function renderPhoneFeedbackTopics(data) {
  const chart = mountChart("phone-feedback-topic-chart");
  const topicTotals = data.reduce((acc, item) => {
    acc[item.phone_feedback_topic] = (acc[item.phone_feedback_topic] || 0) + Number(item.sample_count || 0);
    return acc;
  }, {});
  const topics = Object.entries(topicTotals)
    .sort((a, b) => a[1] - b[1])
    .map(([topic]) => topic);
  const comments = topics.map((topic) => {
    const row = data.find((item) => item.phone_feedback_topic === topic && item.source_type === "comment");
    return row ? Number(row.sample_count || 0) : 0;
  });
  const danmaku = topics.map((topic) => {
    const row = data.find((item) => item.phone_feedback_topic === topic && item.source_type === "danmaku");
    return row ? Number(row.sample_count || 0) : 0;
  });

  chart.setOption({
    color: ["#2f6fed", "#128c7e"],
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    grid: { left: 82, right: 24, top: 36, bottom: 24 },
    xAxis: { type: "value", splitLine: { lineStyle: { color: "#e8edf5" } } },
    yAxis: {
      type: "category",
      data: topics,
      axisTick: { show: false },
    },
    series: [
      { name: "评论", type: "bar", stack: "total", data: comments },
      { name: "弹幕", type: "bar", stack: "total", data: danmaku },
    ],
  });
}

function renderPhoneFeedbackSentiment(data) {
  const chart = mountChart("phone-feedback-sentiment-chart");
  const grouped = data.reduce((acc, item) => {
    const topic = item.phone_feedback_topic;
    if (!acc[topic]) {
      acc[topic] = { 正向: 0, 中性: 0, 负向: 0, total: 0 };
    }
    acc[topic][item.sentiment_label] += Number(item.sample_count || 0);
    acc[topic].total += Number(item.sample_count || 0);
    return acc;
  }, {});
  const topics = Object.entries(grouped)
    .sort((a, b) => a[1].total - b[1].total)
    .map(([topic]) => topic);
  const labels = ["正向", "中性", "负向"];

  chart.setOption({
    color: ["#2f6fed", "#d99a21", "#e66145"],
    tooltip: {
      trigger: "axis",
      formatter(params) {
        const total = params.reduce((sum, item) => sum + Number(item.value || 0), 0);
        const lines = params.map((item) => `${item.seriesName}: ${numberText(item.value)} (${total ? ((Number(item.value) / total) * 100).toFixed(1) : "0.0"}%)`);
        return `${params[0].axisValue}<br/>${lines.join("<br/>")}`;
      },
    },
    legend: { top: 0 },
    grid: { left: 82, right: 24, top: 36, bottom: 24 },
    xAxis: { type: "value", splitLine: { lineStyle: { color: "#e8edf5" } } },
    yAxis: { type: "category", data: topics, axisTick: { show: false } },
    series: labels.map((label) => ({
      name: label,
      type: "bar",
      stack: "sentiment",
      data: topics.map((topic) => grouped[topic][label] || 0),
    })),
  });
}

function renderPhoneFeedbackKeywords(data) {
  const chart = mountChart("phone-feedback-keyword-chart");
  const all = data
    .filter((item) => item.source_type === "all" && item.phone_feedback_topic === "全部反馈")
    .slice(0, 20)
    .reverse();
  chart.setOption({
    color: ["#6d5bd0"],
    tooltip: { trigger: "axis" },
    grid: { left: 82, right: 24, top: 12, bottom: 24 },
    xAxis: { type: "value", splitLine: { lineStyle: { color: "#e8edf5" } } },
    yAxis: {
      type: "category",
      data: all.map((item) => item.keyword),
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: all.map((item) => item.word_count),
        itemStyle: { borderRadius: [0, 4, 4, 0] },
      },
    ],
  });
}

function renderPhoneFeedbackExamples(data) {
  const container = document.getElementById("phone-feedback-examples");
  const comments = data
    .filter((item) => item.source_type === "comment")
    .sort((a, b) => Number(b.like_count || 0) - Number(a.like_count || 0))
    .slice(0, 4);
  const danmaku = data
    .filter((item) => item.source_type === "danmaku")
    .sort((a, b) => Number(a.video_time || 0) - Number(b.video_time || 0))
    .slice(0, 4);
  const rows = [...comments, ...danmaku];

  container.innerHTML = rows
    .map((item) => {
      const meta = item.source_type === "comment"
        ? `${item.phone_feedback_topic} · ${numberText(item.like_count)}赞 · ${item.sentiment_label}`
        : `${item.phone_feedback_topic} · ${item.video_time_label} · ${item.sentiment_label}`;
      return `
        <div class="feedback-example">
          <p>${shortText(item.feedback_text)}</p>
          <span>${meta}</span>
        </div>
      `;
    })
    .join("");
}

function renderKeywordChart(id, data, color) {
  const chart = mountChart(id);
  const ordered = [...data].slice(0, 20).reverse();
  chart.setOption({
    color: [color],
    tooltip: { trigger: "axis" },
    grid: { left: 82, right: 24, top: 12, bottom: 24 },
    xAxis: { type: "value", splitLine: { lineStyle: { color: "#e8edf5" } } },
    yAxis: {
      type: "category",
      data: ordered.map((item) => item.keyword),
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: ordered.map((item) => item.word_count),
        itemStyle: { borderRadius: [0, 4, 4, 0] },
      },
    ],
  });
}

function renderInsights(data) {
  const list = document.getElementById("insights");
  list.innerHTML = (data.insights || [])
    .map((line) => `<li>${line.replace(/^\d+\.\s*/, "")}</li>`)
    .join("");
}

async function init() {
  const [
    video,
    interaction,
    timeline,
    peaks,
    cleaningSummary,
    danmakuBeforeKeywords,
    danmakuAfterKeywords,
    commentKeywords,
    sentiment,
    commentLike,
    phoneFeedbackSummary,
    phoneFeedbackSentiment,
    phoneFeedbackKeywords,
    phoneFeedbackExamples,
    insights,
  ] = await Promise.all([
    getJson("/api/video"),
    getJson("/api/interaction"),
    getJson("/api/danmaku-timeline"),
    getJson("/api/danmaku-peaks"),
    getJson("/api/danmaku-cleaning-summary"),
    getJson("/api/keywords?source=danmaku_before&limit=30"),
    getJson("/api/keywords?source=danmaku_after&limit=30"),
    getJson("/api/keywords?source=comment&limit=30"),
    getJson("/api/sentiment"),
    getJson("/api/comment-like-sentiment"),
    getJson("/api/phone-feedback-summary"),
    getJson("/api/phone-feedback-sentiment"),
    getJson("/api/phone-feedback-keywords?source=all&limit=30"),
    getJson("/api/phone-feedback-examples"),
    getJson("/api/insights"),
  ]);

  renderSummary(video);
  renderInteraction(interaction);
  renderSentiment(sentiment);
  renderTimeline(timeline);
  renderPeaks(peaks);
  renderCommentLike(commentLike);
  renderCleaningSummary(cleaningSummary);
  renderPhoneFeedbackSummary(phoneFeedbackSummary);
  renderPhoneFeedbackTopics(phoneFeedbackSummary);
  renderPhoneFeedbackSentiment(phoneFeedbackSentiment);
  renderPhoneFeedbackKeywords(phoneFeedbackKeywords);
  renderPhoneFeedbackExamples(phoneFeedbackExamples);
  renderKeywordChart("danmaku-before-keyword-chart", danmakuBeforeKeywords, "#d99a21");
  renderKeywordChart("danmaku-after-keyword-chart", danmakuAfterKeywords, "#128c7e");
  renderKeywordChart("comment-keyword-chart", commentKeywords, "#2f6fed");
  renderInsights(insights);
}

window.addEventListener("resize", () => {
  charts.forEach((chart) => chart.resize());
});

init().catch((error) => {
  console.error(error);
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<div style="padding:12px 20px;background:#fff0f0;color:#9b1c1c;">数据加载失败：${error.message}</div>`,
  );
});
