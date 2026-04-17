CREATE DATABASE IF NOT EXISTS bilibili_video_analysis
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE bilibili_video_analysis;

CREATE TABLE IF NOT EXISTS video_info (
  video_id INT AUTO_INCREMENT PRIMARY KEY,
  bvid VARCHAR(32) NOT NULL UNIQUE,
  aid BIGINT NOT NULL,
  cid BIGINT NOT NULL,
  title VARCHAR(255) NOT NULL,
  up_name VARCHAR(100),
  up_mid BIGINT,
  duration_seconds INT,
  view_count BIGINT,
  danmaku_count BIGINT,
  reply_count BIGINT,
  favorite_count BIGINT,
  coin_count BIGINT,
  share_count BIGINT,
  like_count BIGINT,
  his_rank INT,
  collect_time DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS danmaku_info (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  bvid VARCHAR(32) NOT NULL,
  cid BIGINT NOT NULL,
  video_time DOUBLE,
  video_minute INT,
  time_bucket_30s INT,
  danmaku_text TEXT,
  clean_text TEXT,
  is_noise_text TINYINT(1) DEFAULT 0,
  is_phone_feedback TINYINT(1) DEFAULT 0,
  phone_feedback_topic VARCHAR(32),
  sentiment_score DOUBLE,
  sentiment_label VARCHAR(20),
  send_time DATETIME NULL,
  mode INT,
  font_size INT,
  color INT,
  collect_time DATETIME,
  INDEX idx_danmaku_bucket (time_bucket_30s),
  INDEX idx_danmaku_sentiment (sentiment_label),
  INDEX idx_danmaku_phone_feedback (is_phone_feedback, phone_feedback_topic)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS comment_info (
  comment_id VARCHAR(64) PRIMARY KEY,
  bvid VARCHAR(32) NOT NULL,
  aid BIGINT NOT NULL,
  comment_text TEXT,
  clean_text TEXT,
  is_noise_text TINYINT(1) DEFAULT 0,
  is_phone_feedback TINYINT(1) DEFAULT 0,
  phone_feedback_topic VARCHAR(32),
  like_count INT,
  reply_count INT,
  comment_time DATETIME NULL,
  sentiment_score DOUBLE,
  sentiment_label VARCHAR(20),
  collect_time DATETIME,
  INDEX idx_comment_sentiment (sentiment_label),
  INDEX idx_comment_like (like_count),
  INDEX idx_comment_phone_feedback (is_phone_feedback, phone_feedback_topic)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS interaction_metrics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  metric_name VARCHAR(64) NOT NULL UNIQUE,
  metric_label VARCHAR(64) NOT NULL,
  metric_value BIGINT,
  metric_rate DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS danmaku_timeline (
  time_bucket_30s INT PRIMARY KEY,
  start_sec INT,
  end_sec INT,
  start_label VARCHAR(16),
  end_label VARCHAR(16),
  time_range VARCHAR(32),
  danmaku_count INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS keyword_metrics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  source_type VARCHAR(32) NOT NULL,
  keyword VARCHAR(80) NOT NULL,
  word_count INT NOT NULL,
  rank_order INT NOT NULL,
  UNIQUE KEY uk_source_keyword (source_type, keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS danmaku_cleaning_summary (
  id INT AUTO_INCREMENT PRIMARY KEY,
  raw_sample_count INT,
  basic_clean_count INT,
  lottery_filtered_count INT,
  content_discussion_count INT,
  filter_ratio DOUBLE,
  retain_ratio DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS danmaku_keyword_compare (
  id INT AUTO_INCREMENT PRIMARY KEY,
  stage VARCHAR(64) NOT NULL,
  keyword VARCHAR(80) NOT NULL,
  word_count INT NOT NULL,
  rank_order INT NOT NULL,
  UNIQUE KEY uk_stage_keyword (stage, keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sentiment_metrics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  source_type VARCHAR(32) NOT NULL,
  sentiment_label VARCHAR(20) NOT NULL,
  sample_count INT NOT NULL,
  ratio DOUBLE,
  avg_score DOUBLE,
  UNIQUE KEY uk_source_sentiment (source_type, sentiment_label)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS phone_feedback_summary (
  id INT AUTO_INCREMENT PRIMARY KEY,
  source_type VARCHAR(32) NOT NULL,
  source_label VARCHAR(32) NOT NULL,
  phone_feedback_topic VARCHAR(32) NOT NULL,
  sample_count INT NOT NULL,
  source_total_count INT NOT NULL,
  feedback_total_count INT NOT NULL,
  source_ratio DOUBLE,
  topic_ratio DOUBLE,
  avg_sentiment_score DOUBLE,
  UNIQUE KEY uk_phone_feedback_summary (source_type, phone_feedback_topic)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS phone_feedback_sentiment (
  id INT AUTO_INCREMENT PRIMARY KEY,
  source_type VARCHAR(32) NOT NULL,
  source_label VARCHAR(32) NOT NULL,
  phone_feedback_topic VARCHAR(32) NOT NULL,
  sentiment_label VARCHAR(20) NOT NULL,
  sample_count INT NOT NULL,
  topic_total_count INT NOT NULL,
  ratio DOUBLE,
  UNIQUE KEY uk_phone_feedback_sentiment (source_type, phone_feedback_topic, sentiment_label)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS phone_feedback_keywords (
  id INT AUTO_INCREMENT PRIMARY KEY,
  source_type VARCHAR(32) NOT NULL,
  source_label VARCHAR(32) NOT NULL,
  phone_feedback_topic VARCHAR(32) NOT NULL,
  keyword VARCHAR(80) NOT NULL,
  word_count INT NOT NULL,
  rank_order INT NOT NULL,
  UNIQUE KEY uk_phone_feedback_keyword (source_type, phone_feedback_topic, keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS phone_feedback_examples (
  id INT AUTO_INCREMENT PRIMARY KEY,
  source_type VARCHAR(32) NOT NULL,
  source_label VARCHAR(32) NOT NULL,
  phone_feedback_topic VARCHAR(32) NOT NULL,
  feedback_text TEXT,
  like_count INT NULL,
  reply_count INT NULL,
  video_time DOUBLE NULL,
  video_time_label VARCHAR(16),
  sentiment_label VARCHAR(20),
  sentiment_score DOUBLE,
  rank_order INT NOT NULL,
  INDEX idx_phone_feedback_example_topic (source_type, phone_feedback_topic)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
