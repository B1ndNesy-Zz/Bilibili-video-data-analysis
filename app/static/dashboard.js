const chartPalette = ["#128c7e", "#2f6fed", "#e66145", "#d99a21", "#6d5bd0", "#3a8c4d"];

const charts = [];

function numberText(value) {
  const numeric = Number(value || 0);
  return numeric.toLocaleString("zh-CN");
}

function rateText(value) {
  return `${(Number(value || 0) * 100).toFixed(2)}%`;
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
    danmakuKeywords,
    commentKeywords,
    sentiment,
    commentLike,
    insights,
  ] = await Promise.all([
    getJson("/api/video"),
    getJson("/api/interaction"),
    getJson("/api/danmaku-timeline"),
    getJson("/api/danmaku-peaks"),
    getJson("/api/keywords?source=danmaku&limit=30"),
    getJson("/api/keywords?source=comment&limit=30"),
    getJson("/api/sentiment"),
    getJson("/api/comment-like-sentiment"),
    getJson("/api/insights"),
  ]);

  renderSummary(video);
  renderInteraction(interaction);
  renderSentiment(sentiment);
  renderTimeline(timeline);
  renderPeaks(peaks);
  renderCommentLike(commentLike);
  renderKeywordChart("danmaku-keyword-chart", danmakuKeywords, "#128c7e");
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
