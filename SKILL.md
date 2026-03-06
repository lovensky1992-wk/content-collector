---
name: content-collector
description: >
  个人内容收藏与知识管理系统。收藏、整理、检索、二创。
  Use when: (1) 用户分享链接/文字/截图并要求保存或收藏,
  (2) 用户说"收藏这个"/"存一下"/"记录下来"/"save this",
  (3) 用户要求按关键词/标签搜索之前收藏的内容,
  (4) 用户要求基于收藏内容生成小红书/社交媒体文案,
  (5) 用户发送 URL 并要求提取/总结内容。
  已支持来源：博客、X/Twitter、网页、B站视频。
  计划支持：微信公众号、视频号、抖音。
  内容类型：文字、长视频（B站可自动转录）、短视频。
---

# Content Collector — 个人内容收藏系统

收藏好内容 → 结构化整理 → 关键词检索 → 二次创作

## 数据位置

`~/.openclaw/workspace/collections/`

```
collections/
├── articles/       # 文章、博客、长文
├── tweets/         # X/Twitter 推文、短内容
├── videos/         # 视频内容（转录+笔记）
├── wechat/         # 微信公众号文章
├── ideas/          # 零散想法、灵感
├── index.md        # 全局索引（自动维护）
└── tags.md         # 标签索引（自动维护）
```

## 收藏工作流

### Supadata API（优先方案）
对于大部分 URL，优先使用 Supadata API 解析：
- 脚本：`SUPADATA_API_KEY=<key> python3 scripts/supadata_fetch.py <command> <url>`
- 环境变量：`SUPADATA_API_KEY` 存放在 TOOLS.md

| 内容类型 | 命令 | 说明 |
|---------|------|------|
| 网页/博客 | `web <url>` | 返回 Markdown 正文，1 credit |
| 视频转录 | `transcript <url> --text [--lang zh]` | YouTube/TikTok/X/Instagram/Facebook，1-2 credits |
| 社交媒体元数据 | `metadata <url>` | 标题、作者、互动数据，1 credit |

Supadata 不可用时的降级方案：
- 网页 → `web_fetch`
- B站 → 本地 bilibili 脚本（见下方）
- 需登录/内网 → Chrome Relay

### URL 内容（文章/博客/网页）
1. **优先** `supadata_fetch.py web <url>` 抓取正文
2. **降级** `web_fetch` 抓取正文
3. 提取标题、作者、发布日期、正文摘要、关键词
4. 生成 `collections/articles/YYYY-MM-DD-slug.md`

### 视频内容（YouTube/TikTok/X/Instagram/Facebook）
1. **元数据**: `supadata_fetch.py metadata <url>`
2. **转录**: `supadata_fetch.py transcript <url> --text --lang zh`
3. **内容提取**：基于转录文本提取核心观点、金句、要点
4. 生成 `collections/videos/YYYY-MM-DD-slug.md`

### 纯文本/截图
1. 截图用 `image` 工具提取文字
2. 整理成结构化格式，来源可选补充

### B站视频（本地流程，Supadata 不支持 B站）
1. **元数据**：`python3 scripts/bilibili_extract.py <bvid_or_url>` → 标题、作者、时长、标签、数据指标
2. **评论区**：
   - 无登录（API）：3条热门
   - 已登录（浏览器 shadow DOM）：20+条，见 `references/bilibili-comments.md`
3. **视频转录**：`bash scripts/bilibili_transcribe.sh <bvid_or_url> [model]`
   - 依赖：yt-dlp、faster-whisper（uv）、opencc
   - 需浏览器已登录B站（yt-dlp 读取 cookie）
   - 模型：tiny/base(默认)/small/medium，base 约10-15分钟转录46分钟视频
   - 输出：`/tmp/bilibili_audio/<BVID>_transcript.json` + `.txt`
   - 注意：ASR 有识别错误，专有名词需人工校验
4. **内容提取**：基于转录文本提取核心观点、金句、要点
5. 生成 `collections/videos/YYYY-MM-DD-slug.md`

## 关联项目（自动匹配）

每次收藏内容后，自动将内容与当前活跃项目关联：

1. 读取 `~/.openclaw/workspace/memory/topics/projects.md` 获取活跃项目列表
2. 将收藏内容的标题、摘要、标签与每个项目的关键词匹配
3. 匹配到的项目写入收藏文件的 YAML frontmatter：
   ```yaml
   related_projects: ["wemp-ops", "xiaohongshu-ops"]
   project_notes: "这个案例可以用于公众号选题：AI调度人力的真实案例"
   ```
4. 同时在 `index.md` 中标注关联项目，方便按项目筛选素材

### 项目关键词（自动从 projects.md 提取）
- **wemp-ops**：公众号、写作、文章、排版、内容运营
- **xiaohongshu-ops**：小红书、笔记、种草、配图、短内容
- **content-collector**：收藏、知识管理、素材库

### 使用场景
- 写公众号文章前：`搜索关联 wemp-ops 的收藏` → 快速找到素材
- 写小红书前：`搜索关联 xiaohongshu-ops 的收藏` → 找到适合拆解的内容
- 选题会议：按项目汇总最近收藏 → 发现选题方向

## 存储格式

文件命名：`YYYY-MM-DD-slug.md`

```yaml
---
title: "标题"
source: "来源平台"
url: "原始链接"
author: "作者"
date_published: "发布日期"
date_collected: "收藏日期"
tags: [tag1, tag2, tag3]
category: "articles|tweets|videos|wechat|ideas"
language: "zh|en"
summary: "一句话摘要"
# 视频专属（可选）
duration: "时长"
platform: "bilibili|youtube"
bvid: "BV号"
stats: { views: 0, likes: 0, comments: 0 }
---
```

### 内容结构

- **核心观点** — 3-7个要点
- **要点摘录** — 原文金句（blockquote）
- **热门评论精选**（视频类）— 含点赞数
- **评论区观点摘要**（视频类）— 总结争议点
- **我的笔记** — 用户个人批注，后续补充
- **原文摘要** — 200-500字概要

## 索引

每次收藏后更新：
- **index.md** — 按月份倒序，含标签和来源
- **tags.md** — 按标签聚合所有收藏

## 检索

1. 标签匹配：`tags.md` 中查找
2. 全文搜索：`grep -ril "keyword" collections/`
3. 返回匹配列表 + 摘要

## 二创 — 小红书内容生成

1. 按选题/标签从收藏库筛选素材
2. 参考 `references/xiaohongshu-style.md` 写作风格
3. 生成：emoji标题 + 口语化正文(300-800字) + 话题标签(5-10个)
4. 发布配合 `xiaohongshu-ops` 技能

## 联动 — 公众号写作供料

收藏库是 `wemp-ops` 公众号写作的素材来源之一。wemp-ops 选题时会自动检索收藏库：
- 标签匹配：`tags.md` 按关键词查找相关收藏
- 全文搜索：`grep -ril` 搜索 collections/ 目录
- 收藏文件中的"核心观点"、"要点摘录"、"我的笔记"可直接用于文章引用

**收藏时的写作友好建议**：
- `summary` 写清楚，便于快速判断是否相关
- `tags` 覆盖主题关键词，提高检索命中率
- "我的笔记"多写自己的思考和联想，这些是文章的独特视角

## 分类规则

| 来源 | 目录 | 备注 |
|------|------|------|
| 博客/网页 | `articles/` | 默认归类 |
| X/Twitter | `tweets/` | 短内容/thread |
| 微信公众号 | `wechat/` | 中文长文 |
| B站/YouTube/抖音 | `videos/` | B站可自动转录 |
| 零散想法 | `ideas/` | 非外部来源 |

## 标签规范

- 中文为主，英文专有名词保持英文
- 每条 3-8 个标签
- 常用：`AI`、`产品设计`、`电商`、`运营`、`技术`、`商业`、`创业`、`效率工具`、`思维模型`、`管理`

## 命令速查

| 用户说 | 动作 |
|--------|------|
| "收藏这个 [URL/文字]" | 抓取→整理→存储→更新索引 |
| "搜索 [关键词]" | 搜索收藏库 |
| "最近收藏了什么" | 读 index.md |
| "关于 [标签] 的收藏" | 从 tags.md 筛选 |
| "用 [选题] 写篇小红书" | 二创生成 |
| "给这篇加个笔记" | 更新"我的笔记"部分 |
| "删除这条收藏" | 移除并更新索引 |
