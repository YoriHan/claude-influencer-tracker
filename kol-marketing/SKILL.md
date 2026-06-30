---
name: kol-marketing
description: "KOL marketing all-in-one for Notion-tracked influencers — one skill, four modes routed by the first argument: 入库/add (paste Twitter/YouTube/LinkedIn links or @handles, auto-detect platform, scrape, write to Notion), 刷新/refresh (re-scrape tracked KOLs, update only auto-scraped fields), 评估/eval (score 0-100 on CPM/engagement/authenticity/pricing, output verdict 合作/小单测试/压价/不合作, write back to Notion — needs the kol-eval Python tool), 计划/plan (collaboration plan with funnel math + budget across outreach/launch tracks). Empty arg lists the modes. Trigger: 'kol', 'kol-marketing', 'KOL Marketing', '加 KOL', '入库 KOL', '把这些达人加进 Notion', '导入 LinkedIn KOL', '批量导入 LinkedIn KOL', '刷新 KOL 数据', '更新达人数据', '评估 KOL', 'KOL 价值评估', '该不该合作', 'KOL 合作计划', 'KOL 投放计划', '拆分预算', '生成投放方案', or pasting KOL links to track."
---

> **Helio 运行说明**：本 skill 由你的自然语言请求触发（不是 Claude Code 的 `/命令`）。下文中出现的 `$ARGUMENTS` 指你在请求里给出的参数——链接 / @handle / 模式词 / 关键词等；没给参数时，按各模式里的「留空」分支处理。

# KOL Marketing

KOL 营销全流程一体化技能：入库 → 刷新 → 评估 → 投放计划，全部围绕 Notion 跟踪库。一个技能、四个模式，按 `$ARGUMENTS` 第一个词分发。

## 模式路由（每次先执行）

读取 `$ARGUMENTS` 的第一个词，决定进入哪个模式；其余参数原样传给该模式：

| 第一个词 | 进入模式 | 干什么 |
|---|---|---|
| `入库` / `add` / 直接粘 KOL 链接或 @handle | **模式一·入库** | 自动识别平台（推特/YouTube/LinkedIn）→ 抓数据 → 写 Notion |
| `刷新` / `refresh` | **模式二·刷新** | 重爬已跟踪 KOL，只更新自动抓取字段 |
| `评估` / `eval` | **模式三·评估** | 0-100 打分 + 合作结论，写回 Notion |
| `计划` / `plan` | **模式四·计划** | 投放计划 + 预算 + 漏斗测算 |
| （留空） | — | 列出以上四个模式，问用户要做哪个 |

判别规则：
- 第一个词命中上表关键词 → 进对应模式（关键词本身不算业务参数，从输入里剥掉）。
- 没有模式词、但输入里有链接或 @handle → 默认进 **入库**。
- 完全留空 → 输出模式清单让用户选，不要瞎猜。

---

# 模式一 · 入库（add）

输入：一个或多个 Twitter/X、YouTube 或 LinkedIn 链接 / @handle（空格或换行分隔）。

**平台自动识别**：逐个判断每条输入属于哪个平台，再走对应抓取流程——
- `twitter.com` / `x.com` / 裸 @handle → 走下面【Twitter / YouTube 入库流程】里的 Twitter 分支
- `youtube.com` / `youtu.be` / `@频道名` → 走【Twitter / YouTube 入库流程】里的 YouTube 分支
- `linkedin.com/in/...` → 走【LinkedIn 入库流程】
- 混合输入：按平台分组，分别处理，最后合并汇总。

## Twitter / YouTube 入库流程

输入：$ARGUMENTS（一个或多个 Twitter/X 或 YouTube 链接或 @handle，空格或换行分隔）

### 用途

粘贴 KOL 链接或 handle → 自动爬取全量数据 → 写入 Notion 数据库。
首次运行自动完成所有配置（建数据库、建视图、存配置），后续零配置直接用。

支持：Twitter/X、YouTube
支持格式：完整 URL 或 `@handle`（Twitter）/ 频道名（YouTube）

---

### 第零步：环境与配置检查（每次都执行）

#### 检查 1：gstack browse 是否安装

```bash
B=$(find "$HOME" -maxdepth 6 -path "*/gstack/browse/dist/browse" 2>/dev/null | head -1)
[ -n "$B" ] && echo "FOUND: $B" || echo "NOT_FOUND"
```

**NOT_FOUND** → 停止，提示：
> "需要先安装 gstack（用于爬取数据）。
> 请运行：`npm install -g @gstack/cli && gstack install`
> 完成后重新运行 `/kol-add`。"

**FOUND** → 将路径记为 `$B`，继续。

---

#### 检查 2：Notion MCP 是否可用

检查当前会话是否有 `notion-create-database`、`notion-create-pages`、`notion-update-page` 等工具。

**不可用** → 停止，提示：
> "需要先配置 Notion MCP。
> 参考：https://github.com/makenotion/notion-mcp-server
> 安装后重新运行 `/kol-add`。"

---

#### 检查 3：读取本地配置

```bash
CONFIG="$HOME/.claude/kol-tracker/config.json"
[ -f "$CONFIG" ] && cat "$CONFIG" || echo "NOT_FOUND"
```

**NOT_FOUND** → 进入「首次配置向导」（Step A）。
**找到配置** → 检查 `twitter_db_id`、`youtube_db_id`、`setup_complete` 是否都有值，缺任意一项则重新走对应步骤。

---

#### Step A：首次配置向导（仅第一次运行）

**A1：确认父页面**

> "首次运行，需要在你的 Notion 里创建 KOL 数据库。
> 请在 Notion 中打开你想放 KOL 数据库的页面，复制页面链接粘贴给我。"

提取 page_id（URL 中去掉连字符的 32 位字符串）。

---

**A2：创建 Twitter KOL 数据库**

调用 notion-create-database，数据库标题 `Twitter KOL`，字段：

| 字段名 | 类型 | 选项/说明 |
|--------|------|-----------|
| Handle | title | @handle |
| 账号链接 | url | |
| 粉丝 | rich_text | 如 "147.4K" |
| 层级 | select | nano / micro / mid / macro |
| DM状态 | rich_text | 开放DM / 未开放DM |
| 区域 | select | en / cn / jp / other |
| 账号标签 | multi_select | AI / Vibe Coding / No Code / Productivity / Builder / Indie Dev |
| 近5均浏览 | number | 近5条推文平均浏览量 |
| 近5均赞 | number | 近5条推文平均点赞数 |
| 最后发帖 | date | 最近一条推文日期 |
| 活跃状态 | select | 活跃 / 不活跃（>30天无更新） |
| YouTube链接 | url | 跨平台关联 |
| 回复状态 | select | reach out / 待回复 / 推进中 / 未报价 / 确认合作 / 暂停推进 |
| 推进状态 | select | 砍价中 / 内容发布 / 已付款 |
| 合作方式 | rich_text | |
| 报价 | rich_text | |
| imp_24h | number | |
| imp_72h | number | |
| engagement | number | |
| CPM | rich_text | |
| 发布日期 | date | |
| post链接 | url | |
| 合作备注 | rich_text | |

记录返回的 `database_id` 为 `TWITTER_DB_ID`。

---

**A3：创建 YouTube KOL 数据库**

调用 notion-create-database，数据库标题 `YouTube KOL`，字段：

| 字段名 | 类型 | 选项/说明 |
|--------|------|-----------|
| Handle | title | 频道名 |
| 账号链接 | url | |
| 粉丝 | rich_text | 如 "92.2K" |
| 层级 | select | nano / micro / mid / macro |
| Email | email | |
| 区域 | select | 英文 / 中文 / 印度 / 日本 / 其他 |
| 账号标签 | multi_select | AI / Vibe Coding / No Code / Productivity / Dev |
| 近十均播K | number | 近10视频平均播放量（千） |
| 最后发布 | date | 最近一条视频日期 |
| 活跃状态 | select | 活跃 / 不活跃（>30天无更新） |
| Twitter链接 | url | 跨平台关联 |
| 回复状态 | select | reach out / 待回复 / 推进中 / 未报价 / 确认合作 / 暂停推进 |
| 达人报价 | rich_text | |
| CPM | rich_text | |
| Engagement Rate | rich_text | |
| 受众地区 | rich_text | |
| 合作方式 | rich_text | |
| 备注 | rich_text | |

记录返回的 `database_id` 为 `YOUTUBE_DB_ID`。

---

**A4：为两个数据库各创建视图**

对 Twitter 和 YouTube 两个数据库，各调用 notion-create-view 创建：

| 视图名 | filter 条件 |
|--------|------------|
| 推进中-视图 | 回复状态 = 推进中 |
| 确认合作-视图 | 回复状态 = 确认合作 |
| reach out-视图 | 回复状态 = reach out |
| 待回复-视图 | 回复状态 = 待回复 |
| 未报价-视图 | 回复状态 = 未报价 |
| 暂停推进-视图 | 回复状态 = 暂停推进 |

---

**A5：保存配置**

```bash
mkdir -p "$HOME/.claude/kol-tracker"
```

用 Write 工具写入 `~/.claude/kol-tracker/config.json`：

```json
{
  "twitter_db_id": "<TWITTER_DB_ID>",
  "youtube_db_id": "<YOUTUBE_DB_ID>",
  "twitter_cookie_file": "",
  "setup_complete": true
}
```

打印：
```
✓ Twitter KOL 数据库已创建（含新字段：层级/互动数据/活跃状态/跨平台链接）
✓ YouTube KOL 数据库已创建
✓ 视图已创建（6个视图 × 2个数据库）
✓ 配置已保存 → ~/.claude/kol-tracker/config.json
```

---

### 第一步：解析输入

从 $ARGUMENTS 解析所有输入，支持混合格式：

**格式识别规则：**

| 输入格式 | 判断逻辑 | 处理方式 |
|----------|---------|---------|
| `https://x.com/handle` | 含 x.com/ 或 twitter.com/ | Twitter，提取 handle |
| `https://youtube.com/@Channel` | 含 youtube.com/ | YouTube，提取频道名 |
| `@handle` | 以 @ 开头，不含 youtube | 默认 Twitter，补全为 `https://x.com/handle` |
| `ChannelName_` | 不含 @、不含 http、含下划线或大写 | 尝试 YouTube，补全为 `https://youtube.com/@ChannelName_` |

如果同一输入无法判断平台，询问用户：
> "`[输入]` 是 Twitter 还是 YouTube？"

**重复检查**：用 notion-search 检查 handle 是否已存在。已存在的标注「已存在，跳过」。

**如果 $ARGUMENTS 为空，提示：**
> "请粘贴 KOL 链接或 handle，支持混合格式，例如：
> @rohanpaul_ai https://youtube.com/@Chase-H-AI @swyx"

---

### 第二步：Twitter 登录检查

（无 Twitter KOL 时跳过）

如果用户提供 `tweetclaw-export=<path>` 或明确说明已有 TweetClaw/OpenClaw
导出的公开 X/Twitter 数据，先生成可审查的种子行：

```bash
python3 scripts/tweetclaw_to_kol_rows.py "<path>" > /tmp/kol-seed.json
```

读取 `/tmp/kol-seed.json`，展示 handle、样本推文数、平均浏览和平均点赞。
只有用户确认后，才把这些种子行写入 Notion。需要补齐 DM 状态、跨平台链接或
最新曝光时，再继续下面的浏览器抓取流程。

```bash
$B goto https://x.com 2>/dev/null && sleep 1
$B text 2>/dev/null | grep -qE "Sign in|Log in|登录" && echo "NOT_LOGGED_IN" || echo "LOGGED_IN"
```

**LOGGED_IN** → 继续。

**NOT_LOGGED_IN** → 检查 config 中 `twitter_cookie_file`：

- **已配置且文件存在**：运行格式修复脚本并导入：
  ```bash
  python3 << 'PYEOF'
  import json
  with open('<cookie_file_path>') as f:
      cookies = json.load(f)
  sameSite_map = {'no_restriction': 'None', 'lax': 'Lax', 'strict': 'Strict'}
  for c in cookies:
      c['sameSite'] = sameSite_map.get(c.get('sameSite', ''), 'None')
      c.pop('storeId', None); c.pop('hostOnly', None)
  with open('/tmp/kol_twitter_cookies.json', 'w') as f:
      json.dump(cookies, f)
  PYEOF
  $B goto https://x.com && $B cookie-import /tmp/kol_twitter_cookies.json
  $B goto https://x.com/home && $B text | grep -qE "Home|For you|首页" && echo "LOGIN_OK"
  ```

- **未配置** → 提示：
  > "需要 Twitter 登录 cookie 才能抓取数据。
  > 步骤：① Chrome 安装 Cookie-Editor 插件 → ② 打开 x.com 并登录 → ③ 点插件 Export → Export as JSON → ④ 把文件路径粘贴给我"

  收到路径后，运行格式修复脚本导入，成功后将路径写入 config.json 的 `twitter_cookie_file`。

---

### 第三步：批量抓取数据

依次处理每个 KOL（Twitter sleep 1.5s，YouTube sleep 0.8s）。

---

#### Twitter 抓取流程

```bash
$B goto "https://x.com/<handle>" 2>/dev/null && sleep 1.5
$B text 2>/dev/null > /tmp/kol_tw_raw.txt
```

```python
import re
from datetime import datetime, timedelta

with open('/tmp/kol_tw_raw.txt') as f:
    raw = f.read()

# ── 粉丝数 ──
m = re.search(r'([\d,.]+[KMkm]?)\s*(?:Followers|关注者)', raw)
followers_str = m.group(1) if m else ''

# ── 层级计算 ──
def parse_count(s):
    s = s.replace(',', '').strip().upper()
    try:
        if s.endswith('K'): return float(s[:-1]) * 1000
        if s.endswith('M'): return float(s[:-1]) * 1000000
        return float(s)
    except: return 0

def get_tier(count_str):
    n = parse_count(count_str)
    if n == 0: return 'unknown'
    if n < 10000: return 'nano'
    if n < 100000: return 'micro'
    if n < 500000: return 'mid'
    return 'macro'

tier = get_tier(followers_str)

# ── DM 状态 ──
dm_open = bool(re.search(r'\bMessage\b|\b发消息\b', raw))
dm_status = '开放DM' if dm_open else '未开放DM'

# ── 区域 ──
has_chinese = bool(re.search(r'[\u4e00-\u9fff]', raw[:3000]))
has_japanese = bool(re.search(r'[\u3040-\u30ff]', raw[:3000]))
region = 'cn' if has_chinese else ('jp' if has_japanese else 'en')

# ── 账号标签 ──
text_lower = raw[:3000].lower()
tags = []
if any(k in text_lower for k in ['ai', 'artificial intelligence', 'gpt', 'llm', 'claude', 'openai']):
    tags.append('AI')
if any(k in text_lower for k in ['vibe cod', 'coding', 'developer', 'engineer', 'software', 'programmer']):
    tags.append('Vibe Coding')
if any(k in text_lower for k in ['no-code', 'nocode', 'no code', 'automation', 'zapier', 'make.com']):
    tags.append('No Code')
if any(k in text_lower for k in ['productivity', 'growth', 'marketing', 'newsletter', 'strategy']):
    tags.append('Productivity')
if any(k in text_lower for k in ['builder', 'indie', 'saas', 'startup', 'founder', 'building']):
    tags.append('Builder')
if not tags:
    tags.append('AI')

# ── 近5条推文互动数据 ──
# 从页面文本中提取浏览数和点赞数（格式：数字K/M + Views/Likes）
view_nums = re.findall(r'([\d,.]+[KMkm]?)\s*(?:Views|浏览)', raw, re.IGNORECASE)
like_nums = re.findall(r'([\d,.]+[KMkm]?)\s*(?:Likes|喜欢|Like)', raw, re.IGNORECASE)

views_sample = [parse_count(v) for v in view_nums[:5]]
likes_sample = [parse_count(v) for v in like_nums[:5]]
avg_views = round(sum(views_sample) / len(views_sample)) if views_sample else 0
avg_likes = round(sum(likes_sample) / len(likes_sample)) if likes_sample else 0

# ── 最后发帖时间 ──
# 提取时间戳或相对时间（如 "2h", "1d", "Jun 5"）
time_patterns = [
    r'\b(\d+)h\b',      # Xh ago
    r'\b(\d+)d\b',      # Xd ago
    r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b',
]
last_post_str = ''
last_post_iso = ''
for p in time_patterns:
    m = re.search(p, raw)
    if m:
        last_post_str = m.group(0)
        break

# 判断活跃状态
is_inactive = False
m_hours = re.search(r'\b(\d+)h\b', raw)
m_days = re.search(r'\b(\d+)d\b', raw)
if m_days and int(m_days.group(1)) > 30:
    is_inactive = True
active_status = '不活跃（>30天无更新）' if is_inactive else '活跃'

# ── 跨平台关联：bio 里是否有 YouTube 链接 ──
yt_link = ''
m = re.search(r'(https?://(?:www\.)?youtube\.com/[@\w/\-]+)', raw)
if m:
    yt_link = m.group(1)

print(f'followers={followers_str}')
print(f'tier={tier}')
print(f'dm_status={dm_status}')
print(f'region={region}')
print(f'tags={",".join(tags)}')
print(f'avg_views={avg_views}')
print(f'avg_likes={avg_likes}')
print(f'last_post={last_post_str}')
print(f'active_status={active_status}')
print(f'yt_link={yt_link}')
```

---

#### YouTube 抓取流程

```bash
# 主页
$B goto "<youtube_url>" 2>/dev/null && sleep 0.8
$B text 2>/dev/null > /tmp/kol_yt_main.txt

# About 页（email + Twitter 链接）
$B goto "<youtube_url>/about" 2>/dev/null && sleep 0.8
$B text 2>/dev/null > /tmp/kol_yt_about.txt

# 视频列表（均播 + 最后发布日期）
$B goto "<youtube_url>/videos" 2>/dev/null && sleep 0.8
$B text 2>/dev/null > /tmp/kol_yt_videos.txt
```

```python
import re

with open('/tmp/kol_yt_main.txt') as f:
    raw = f.read()
with open('/tmp/kol_yt_about.txt') as f:
    about = f.read()
with open('/tmp/kol_yt_videos.txt') as f:
    videos_raw = f.read()

# ── 订阅数 ──
m = re.search(r'([\d,.]+[KMkm]?)\s*(?:subscribers|订阅者)', raw, re.IGNORECASE)
subs_str = m.group(1) if m else ''

# ── 层级 ──
def parse_count(s):
    s = s.replace(',', '').strip().upper()
    try:
        if s.endswith('K'): return float(s[:-1]) * 1000
        if s.endswith('M'): return float(s[:-1]) * 1000000
        return float(s)
    except: return 0

def get_tier(s):
    n = parse_count(s)
    if n == 0: return 'unknown'
    if n < 10000: return 'nano'
    if n < 100000: return 'micro'
    if n < 500000: return 'mid'
    return 'macro'

tier = get_tier(subs_str)

# ── Email ──
m = re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', about)
email = m.group(0) if m else ''

# ── 近十均播 ──
def parse_view(s):
    s = s.replace(',', '').strip().upper()
    try:
        if s.endswith('K'): return float(s[:-1]) * 1000
        if s.endswith('M'): return float(s[:-1]) * 1000000
        return float(s)
    except: return 0

view_strs = re.findall(r'([\d,.]+[KMkm]?)\s*(?:views|次观看|次播放)', videos_raw, re.IGNORECASE)
nums = [parse_view(v) for v in view_strs[:10]]
avg_views_k = round(sum(nums) / len(nums) / 1000, 1) if nums else 0
sample_count = len(nums)

# ── 最后发布时间 ──
time_patterns = [r'\b(\d+)\s*(?:hours?|小时)\s*ago\b', r'\b(\d+)\s*(?:days?|天)\s*ago\b',
                 r'\b(\d+)\s*(?:weeks?|周)\s*ago\b', r'\b(\d+)\s*(?:months?|月)\s*ago\b']
last_video_str = ''
days_since = 0
m_week = re.search(r'\b(\d+)\s*(?:weeks?|周)\s*ago\b', videos_raw, re.IGNORECASE)
m_month = re.search(r'\b(\d+)\s*(?:months?|月)\s*ago\b', videos_raw, re.IGNORECASE)
m_day = re.search(r'\b(\d+)\s*(?:days?|天)\s*ago\b', videos_raw, re.IGNORECASE)
if m_month: days_since = int(m_month.group(1)) * 30; last_video_str = m_month.group(0)
elif m_week: days_since = int(m_week.group(1)) * 7; last_video_str = m_week.group(0)
elif m_day: days_since = int(m_day.group(1)); last_video_str = m_day.group(0)

active_status = '不活跃（>30天无更新）' if days_since > 30 else '活跃'

# ── 区域 ──
full_text = (raw + about).lower()
has_chinese = bool(re.search(r'[\u4e00-\u9fff]', raw[:3000]))
india_kw = ['india', 'bangalore', 'mumbai', 'delhi', 'hyderabad', 'gujarat', 'hindi', 'pune']
region = '中文' if has_chinese else ('印度' if any(k in full_text for k in india_kw) else '英文')

# ── 账号标签 ──
tags = []
if any(k in full_text for k in ['ai', 'artificial intelligence', 'chatgpt', 'gpt', 'llm', 'claude']):
    tags.append('AI')
if any(k in full_text for k in ['vibe cod', 'coding', 'developer', 'engineer', 'programming']):
    tags.append('Vibe Coding')
if any(k in full_text for k in ['no-code', 'nocode', 'automation', 'zapier']):
    tags.append('No Code')
if any(k in full_text for k in ['productivity', 'growth', 'marketing']):
    tags.append('Productivity')
if any(k in full_text for k in ['developer', 'engineer', 'software', 'full stack', 'saas builder']):
    tags.append('Dev')
if not tags:
    tags.append('AI')

# ── 跨平台关联：About 页里是否有 Twitter/X 链接 ──
tw_link = ''
m = re.search(r'(https?://(?:www\.)?(?:twitter|x)\.com/[\w]+)', about)
if m:
    tw_link = m.group(1)

print(f'subs={subs_str}')
print(f'tier={tier}')
print(f'email={email}')
print(f'avg_views_k={avg_views_k}')
print(f'sample_count={sample_count}')
print(f'last_video={last_video_str}')
print(f'active_status={active_status}')
print(f'region={region}')
print(f'tags={",".join(tags)}')
print(f'tw_link={tw_link}')
```

---

### 第四步：批量写入 Notion

所有 KOL 数据抓取完毕后，**并行**调用 notion-create-pages 写入。

**Twitter** 写入 `twitter_db_id`：
```
Handle:      "@<handle>"
账号链接:     "https://x.com/<handle>"
粉丝:        "<followers_str>"
层级:        "<tier>"          ← 新增
DM状态:      "<dm_status>"
区域:        "<region>"
账号标签:     ["AI", "Builder"]
近5均浏览:    <avg_views>       ← 新增
近5均赞:      <avg_likes>       ← 新增
最后发帖:     "<last_post_str>" ← 新增（date 字段）
活跃状态:     "<active_status>" ← 新增
YouTube链接:  "<yt_link>"       ← 新增（有值才填）
回复状态:     "reach out"
```

**YouTube** 写入 `youtube_db_id`：
```
Handle:      "<channel_name>"
账号链接:     "<youtube_url>"
粉丝:        "<subs_str>"
层级:        "<tier>"           ← 新增
Email:       "<email>"
区域:        "<region>"
账号标签:     ["AI"]
近十均播K:    <avg_views_k>
最后发布:     "<last_video_str>" ← 新增（date 字段）
活跃状态:     "<active_status>"  ← 新增
Twitter链接:  "<tw_link>"        ← 新增（有值才填）
回复状态:     "reach out"
```

---

### 第五步：输出汇总 + 可选 DM 草稿

#### 入库结果表

```
✅ 入库完成（共 N 个）

| 平台    | Handle       | 粉丝    | 层级   | 均浏览/均播  | 活跃  | 标签           |
|---------|--------------|---------|--------|-------------|-------|----------------|
| Twitter | @rohanpaul_ai| 147.4K  | micro  | 8.2K views  | ✅    | AI, Builder    |
| YouTube | Chase-H-AI   | 128K    | micro  | 45.3K/video | ✅    | AI, Vibe Coding|
| Twitter | @swyx        | 372.6K  | mid    | —（未获取）  | ✅    | AI             |

⚠️ 注意：
- @xxx：粉丝数未显示，已入库，需手动补充
- @yyy：已存在于数据库，跳过
- ChannelZ：近十均播样本仅3条，数据仅供参考
- @zzz：⚠️ 最后发帖超过30天，已标记为不活跃
```

跨平台关联如有发现，单独列出：
```
🔗 跨平台关联发现：
- @rohanpaul_ai 的 bio 包含 YouTube 链接，已自动填入 YouTube链接字段
```

---

#### 可选：生成外联 DM 草稿

所有 KOL 入库完成后询问：
> "需要为刚入库的 KOL 生成个性化外联 DM 草稿吗？（是/否）"

**回答「是」**：为每个 KOL 基于其标签、层级和内容垂类生成英文 DM，格式：

```
── @rohanpaul_ai（Twitter · micro · AI/Builder）──
Hi Rohan, been following your AI content — especially your takes on [从bio/标签推断的具体方向].

We're building [your product] and think your audience would genuinely benefit from it. We're looking for authentic voices in the AI space to try it out and share their honest take.

Would love to explore a collab — open to chat?
```

**规则：**
- 第一句基于账号标签和内容垂类个性化，不套模板
- 不写产品名（用户自己填），用 `[your product]` 占位
- 不超过 4 句话
- 不用感叹号开头
- 不用 "check it out" / "sign up" 等词

---

### 注意事项

- **Cookie 失效**：Twitter cookie 通常 7 天内有效。遇到登录失效（重定向到 sign in）时主动提示重新导出，不静默失败
- **抓取失败处理**：单个 KOL 失败时等待 2s 重试一次，仍失败则跳过并在汇总中标注，不阻塞其他 KOL
- **重复保护**：写入前检查 Handle 是否已存在，存在则跳过
- **macOS 兼容**：所有 grep 用 `-E` 不用 `-P`；文本提取用 python3
- **互动数据说明**：Twitter 浏览量仅在用户已登录时可见；未登录时 avg_views 填 0，在备注中标注"需登录查看"
- **`/kol-refresh`**：如需刷新已有 KOL 的数据，使用 `/kol-refresh @handle` 命令

## LinkedIn 入库流程（识别为 linkedin.com 时走这里）

输入：$ARGUMENTS（LinkedIn URL 列表，空格或换行分隔；留空则提示粘贴）

### 用途

将一批 LinkedIn KOL 主页链接批量录入 Notion「LinkedIn KOL 总表」数据库，自动抓取粉丝数、headline 作为备注，并智能推断账号标签。

**触发场景：** 用户粘贴一批 LinkedIn 链接要求入库、或说"帮我把这些 LinkedIn 加进 Notion"

---

### 第零步：解析输入

从 $ARGUMENTS 或用户消息中提取所有 LinkedIn URL，支持格式：
- `https://www.linkedin.com/in/username/`
- `linkedin.com/in/username`
- 混合 X.com DM 链接（`x.com/i/chat/...`）— 识别后关联到紧邻的 LinkedIn 账号

将解析结果列出，格式：
```
找到 N 个 LinkedIn 账号：
1. username → https://www.linkedin.com/in/username/
...
[X 链接] nandi-bishal → https://x.com/i/chat/xxx（DM链接，保存到X链接字段）
```

如果未找到任何链接，提示：
> "请粘贴 LinkedIn 主页链接，每行一个，然后回车两次。"

---

### 第一步：读取 Notion 数据库结构

fetch Notion 数据库：`https://www.notion.so/e5c1a20031874a99a56a4466f79e1d50`

确认 data_source_id 和 schema，特别记录：
- 标题字段：`名字`
- `账号链接`（url）、`X链接`（url）
- `区域`（select）：英文 / 中文 / 印度
- `粉丝`（text）
- `账号标签`（multi_select）：AI / Vibe Coding / No Code / Productivity / Dev
- `回复状态`（multi_select）：reach out / 推进中 / 未报价 / 已合作
- `备注`（text）

---

### 第二步：LinkedIn Cookie 检查

```bash
B="$HOME/.claude/skills/gstack/browse/dist/browse"
$B goto https://www.linkedin.com 2>/dev/null
$B text 2>/dev/null | grep -q "authwall\|Join LinkedIn\|Sign in" && echo "NOT_LOGGED_IN" || echo "LOGGED_IN"
```

**LOGGED_IN** → 直接进入第三步。

**NOT_LOGGED_IN** → 提示用户：
> "LinkedIn 需要登录。请用 Cookie-Editor（Chrome 插件）导出 LinkedIn cookies（JSON 格式），然后粘贴给我。"
>
> 用户粘贴 JSON 后：
> 1. 保存到 `/tmp/linkedin_cookies_raw.json`
> 2. 运行格式修复脚本（sameSite 转换）：
>
> ```bash
> python3 << 'PYEOF'
> import json
> with open('/tmp/linkedin_cookies_raw.json') as f:
>     cookies = json.load(f)
> sameSite_map = {'no_restriction': 'None', 'lax': 'Lax', 'strict': 'Strict', None: 'None'}
> out = []
> for c in cookies:
>     c['sameSite'] = sameSite_map.get(c.get('sameSite'), 'None')
>     c.pop('storeId', None)
>     c.pop('hostOnly', None)
>     out.append(c)
> with open('/tmp/linkedin_cookies.json', 'w') as f:
>     json.dump(out, f)
> print(f'done: {len(out)} cookies')
> PYEOF
> ```
>
> 3. 导入：`$B goto https://www.linkedin.com && $B cookie-import /tmp/linkedin_cookies.json`
> 4. 验证：`$B goto https://www.linkedin.com/feed/ && $B text | grep -q "首页\|Home\|Feed" && echo OK`

---

### 第三步：批量抓取 LinkedIn 数据

对每个账号依次执行（每次 sleep 0.5s 避免限速）：

```bash
B="$HOME/.claude/skills/gstack/browse/dist/browse"
$B goto "https://www.linkedin.com/in/SLUG/" 2>/dev/null
$B text 2>/dev/null > /tmp/li_profile.txt
```

然后用 python3 提取：

```python
import re
with open('/tmp/li_profile.txt') as f:
    raw = f.read()
raw = re.sub(r'--- BEGIN.*?---\n?', '', raw)
raw = re.sub(r'--- END.*?---', '', raw)

# 粉丝数
followers = re.search(r'([\d,]+)\s*位关注者', raw)
followers = followers.group(0) if followers else ''

# Headline（简介）
headline = ''
for pattern in [
    r'(Founder|Co-Founder|Creator|Developer|Engineer|Builder|Strategist|Manager|Director|CEO|CTO|Helping|I (post|share|teach)|AI [A-Za-z]|Automation|Sharing|Teaching|Coach)[^\n·]{15,250}',
]:
    m = re.search(pattern, raw)
    if m:
        headline = m.group(0)[:250].strip()
        break
```

**标签推断规则**（根据 headline 关键词，可多选）：
- `AI`：含 AI / artificial intelligence / ChatGPT / GPT / LLM / machine learning
- `Vibe Coding`：含 vibe cod / coding / developer / engineer / software / dev
- `No Code`：含 no.code / nocode / automation / zapier / make.com / workflow
- `Productivity`：含 productivity / marketing / growth / lead gen / newsletter / strategy
- `Dev`：含 developer / engineer / software / full.stack / backend / frontend / SaaS builder

**区域推断规则**（根据 profile 文字）：
- 含印度地名（India / Bangalore / Mumbai / Delhi / Hyderabad / Gujarat / 印度）→ `印度`
- 含中文内容 → `中文`
- 其他 → `英文`

记录每个账号的提取结果，准备批量写入。

---

### 第四步：批量创建 Notion 条目

用 notion-create-pages 一次性创建所有条目，parent 使用 data_source_id：

每个 page 包含：
```json
{
  "名字": "提取的姓名（从 headline 前的名字行，或 URL slug 转 Title Case）",
  "账号链接": "https://www.linkedin.com/in/slug/",
  "X链接": "如有则填入",
  "区域": "英文 / 中文 / 印度",
  "粉丝": "102,754（原始格式，含逗号）",
  "账号标签": "[\"AI\", \"Productivity\"]",
  "回复状态": "[\"reach out\"]",
  "备注": "headline 原文（不超过 250 字符）"
}
```

**姓名提取逻辑**：
- 优先从页面文字抓取：`re.search(r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})', raw)`
- 次选：URL slug 转 Title Case（`ansh-bhatnagar-b4b495262` → `Ansh Bhatnagar`，去掉末尾数字段）

---

### 第五步：输出汇总

操作完成后输出表格：

```
✅ 已入库 N 个账号：

| 名字 | 粉丝 | 标签 | 备注（摘要） |
|------|------|------|------------|
| Mayank Tayal | 102,754 | AI, Productivity | Founder @AilaunchX... |
...
```

如有抓取失败的账号，单独列出：
```
⚠️ 以下账号需手动补充（未能抓取完整数据）：
- vikasguptag：粉丝数未显示
```

---

### 注意事项

- Cookie 文件保存在 `/tmp/linkedin_cookies.json`，下次运行时若 LinkedIn 仍然登录则无需重新导入
- macOS 上使用 `grep -E`，不使用 `grep -P`（-P 在 macOS 不支持）
- 所有 LinkedIn 文本提取使用 `python3 处理 $B text 输出文件`，不用 JS querySelector（React 动态渲染）
- 粉丝数显示 "500+" 或页面未显示时，备注中注明"粉丝数未公开"

---

# 模式二 · 刷新（refresh）

输入：$ARGUMENTS（一个或多个 @handle 或 KOL 链接；留空则询问）

### 用途

重新爬取已入库 KOL 的最新数据，只更新数据字段，**不覆盖**手动填写的字段（回复状态、报价、合作备注、推进状态等）。

适用场景：
- 入库超过 1 个月，粉丝/均播已变化
- 想检查某个 KOL 是否还活跃
- 批量刷新所有「推进中」KOL 的最新数据

---

### 第零步：读取配置

```bash
CONFIG="$HOME/.claude/kol-tracker/config.json"
[ -f "$CONFIG" ] && cat "$CONFIG" || echo "NOT_FOUND"
```

**NOT_FOUND** → 提示：
> "还没有初始化配置，请先运行 `/kol-add` 完成首次设置。"
停止。

从 config 读取 `twitter_db_id`、`youtube_db_id`、`twitter_cookie_file`。

---

### 第一步：解析目标

**情况 A：有 $ARGUMENTS**

解析输入中的 handle 或链接，识别平台（规则同 `/kol-add` 第一步）。

**情况 B：$ARGUMENTS 为空**

询问：
> "要刷新哪些 KOL？可以：
> 1. 输入 @handle 或链接（支持批量）
> 2. 输入 `all-twitter` 刷新所有 Twitter KOL
> 3. 输入 `all-youtube` 刷新所有 YouTube KOL
> 4. 输入 `推进中` 只刷新回复状态为推进中的 KOL"

**`all-twitter` / `all-youtube`**：
用 notion-fetch 读取对应数据库的全部 Handle，依次刷新。数量超过 20 个时先确认：
> "共找到 N 个 KOL，全部刷新预计需要约 X 分钟，确认继续？"

**`推进中`**：
用 notion-fetch 读取两个数据库中回复状态 = 推进中的条目。

---

### 第二步：从 Notion 读取已有记录

对每个 handle，用 notion-search 或 notion-fetch 找到对应 page_id，并记录以下**不可覆盖字段**（保留用户手动填写的内容）：

**Twitter 不可覆盖：** 回复状态、推进状态、合作方式、报价、imp_24h、imp_72h、engagement、CPM、发布日期、post链接、合作备注

**YouTube 不可覆盖：** 回复状态、达人报价、CPM、合作方式、备注

找不到对应记录时标注「未在数据库中，跳过（可用 /kol-add 添加）」。

---

### 第三步：登录检查

同 `/kol-add` 第二步，此处不重复，直接执行相同流程。

---

### 第四步：重新爬取数据

抓取逻辑与 `/kol-add` 第三步完全相同，此处不重复。

对每个 KOL 完成爬取后，与已有数据对比，记录变化：

```python
changes = []
if new_followers != old_followers:
    changes.append(f'粉丝：{old_followers} → {new_followers}')
if new_tier != old_tier:
    changes.append(f'层级：{old_tier} → {new_tier}')
if new_active_status != old_active_status:
    changes.append(f'活跃状态：{old_active_status} → {new_active_status}')
if new_avg_views != old_avg_views:
    changes.append(f'均浏览：{old_avg_views} → {new_avg_views}')
```

---

### 第五步：更新 Notion

调用 notion-update-page，**只更新**以下字段（其余保持原值不动）：

**Twitter 可更新：** 粉丝、层级、DM状态、区域、账号标签、近5均浏览、近5均赞、最后发帖、活跃状态、YouTube链接

**YouTube 可更新：** 粉丝、层级、Email、区域、账号标签、近十均播K、最后发布、活跃状态、Twitter链接

多个 KOL 并行更新。

---

### 第六步：输出变化汇总

```
✅ 刷新完成（共 N 个）

| Handle        | 平台    | 变化                                      |
|---------------|---------|-------------------------------------------|
| @rohanpaul_ai | Twitter | 粉丝 147K→162K，均浏览 8.2K→11.4K         |
| Chase-H-AI    | YouTube | 近十均播 45K→52K                           |
| @swyx         | Twitter | 无变化                                     |
| @oldaccount   | Twitter | ⚠️ 活跃→不活跃（最后发帖超30天）            |

⚠️ 以下 KOL 刷新失败（已保留原有数据）：
- @handle：页面加载异常，建议手动检查
```

---

### 注意事项

- 不可覆盖字段由代码严格保护，不会因为刷新丢失手动填写的报价、备注等
- 活跃状态从「活跃」变为「不活跃」时，额外在合作备注里追加一条记录：`[YYYY-MM-DD 刷新] 已转为不活跃`，方便追溯
- 批量刷新时如果中途失败，已完成的不会回滚，重新运行会跳过无变化的条目

---

# 模式三 · 评估（eval）

输入：$ARGUMENTS（Notion 表格链接或页面名称；留空则自动搜索 KOL 相关表格）

### 用途

从 Notion 表格读取 KOL 链接和报价，自动抓取 Twitter/YouTube 主页和近期内容数据，
输出账号画像、受众画像、完整量化指标和合作建议，并将结果写回 Notion。

---

### 第零步：首次运行检查（每次都执行）

在开始评估之前，先做以下环境检查。发现任何问题时**不要跳过**，引导用户完成配置后再继续。

#### 检查 1：kol-eval 工具是否安装

先动态定位安装目录：
```bash
KOL_EVAL_DIR=$(find "$HOME" -maxdepth 4 -name "pyproject.toml" 2>/dev/null \
  | xargs grep -l "kol.eval\|kol_eval" 2>/dev/null | head -1 | xargs dirname 2>/dev/null)
[ -z "$KOL_EVAL_DIR" ] && KOL_EVAL_DIR="$HOME/kol-eval"
[ -f "$KOL_EVAL_DIR/pyproject.toml" ] && echo "FOUND: $KOL_EVAL_DIR" || echo "NOT_FOUND"
```

- **NOT_FOUND** → 提示用户：
  > "需要先安装 kol-eval 工具。请运行：
  > ```bash
  > cd ~
  > git clone https://github.com/YoriHan/kol-eval.git
  > cd kol-eval && uv sync
  > uv run playwright install chromium
  > ```
  > 完成后再运行 `/kol-eval`。"
  然后停止。

- **FOUND** → 将路径记为 `$KOL_EVAL_DIR`，后续所有操作都在此目录下执行，继续下一项检查。

#### 检查 2：`.env` 配置是否完整

检查 `$KOL_EVAL_DIR/.env` 是否存在，且包含 `NOTION_API_KEY` 和 `NOTION_DATABASE_ID`。

- **`.env` 不存在，或缺少这两项** → 引导用户完成配置：

  **Step 2a — 创建 Notion Integration**
  > "需要先创建 Notion API Key：
  > 1. 打开 https://www.notion.so/my-integrations
  > 2. 点击「New integration」，名称填 kol-eval，选择你的工作区
  > 3. 复制生成的 `secret_xxx` token
  >
  > 你的 Notion API Key 是？（粘贴 `secret_` 开头的值）"

  等用户提供后继续。

  **Step 2b — 获取 Notion Database ID**
  > "现在需要你的 KOL Notion 数据库 ID：
  > 打开你的 Notion KOL 表格，复制浏览器地址栏 URL，
  > 例如：`https://notion.so/abc123def456...?v=xxx`
  > 其中 `abc123def456...` 就是 Database ID（问号前面的部分）。
  >
  > 请粘贴你的 Notion 表格 URL 或 Database ID："

  等用户提供后，提取 ID（去掉连字符），继续。

  **Step 2c — 写入 .env**
  运行：
  ```bash
  cd "$KOL_EVAL_DIR"
  cp .env.example .env
  # 将用户提供的值写入 .env
  ```
  用 Edit 工具将 `NOTION_API_KEY` 和 `NOTION_DATABASE_ID` 填入 `$KOL_EVAL_DIR/.env`。

  完成后告知用户："`.env` 已配置好 ✓"

- **两项都存在** → 继续下一项检查。

#### 检查 3：Notion 表格已连接到 Integration

提示用户（只在首次或 Notion 报权限错误时检查）：
> "确认一下：请打开你的 Notion KOL 数据库，点击右上角「...」→「Connections」，
> 确保 kol-eval integration 已连接。如果没有，点击「+」添加。完成后告诉我。"

等用户确认后继续。

#### 检查 4：Notion 表格是否有输出列

运行以下命令检查缺少哪些列：
```bash
cd "$KOL_EVAL_DIR"
NOTION_API_KEY=$(grep NOTION_API_KEY .env | cut -d= -f2) \
NOTION_DATABASE_ID=$(grep NOTION_DATABASE_ID .env | cut -d= -f2) \
uv run python -c "from kol_eval.notion_io import validate_output_schema; missing = validate_output_schema(); print('MISSING:' + ','.join(missing) if missing else 'OK')"
```

- **有缺少的列** → 列出清单，引导用户添加：
  > "你的 Notion 数据库还缺少以下输出列，需要手动添加后工具才能写回结果：
  >
  > | 列名 | 类型 |
  > |------|------|
  > | Followers | 数字（Number） |
  > | Avg Views | 数字（Number） |
  > | ER | 数字（Number） |
  > | CPM | 数字（Number） |
  > | C/L Ratio | 数字（Number） |
  > | Score | 数字（Number） |
  > | Rating | 选项（Select），选项值：S、A、B、C、D |
  > | Verdict | 选项（Select），选项值：合作、有条件合作：先小单测试、合作，但必须压价、暂缓：等更多数据或大幅压价、暂缓：数据不足、不合作 |
  > | Eval Date | 日期（Date） |
  > | Negotiation | 文本（Text） |
  >
  > 在 Notion 里添加好后告诉我，我会重新检查。"

  等用户确认后重新运行检查，直到所有列都存在。

- **全部存在（返回 OK）** → 继续下一项检查。

#### 检查 5：Twitter Cookie（如果表格里有 Twitter KOL）

检查 `.env` 中 `TWITTER_COOKIE_FILE` 指向的文件是否存在。

- **文件不存在** → 引导：
  > "抓取 Twitter/X 需要登录 cookie。在当前聊天窗口运行：
  > ```
  > /setup-browser-cookies
  > ```
  > 选择 twitter.com / x.com，完成导出后，把导出的文件路径告诉我，
  > 我来更新 `.env` 里的 `TWITTER_COOKIE_FILE`。"

  等用户提供路径后，用 Edit 更新 `.env`，然后继续。

- **文件存在** → 打印 "Twitter cookie ✓"，继续。

#### 检查完成

所有检查通过后，打印：
```
✓ 环境配置完整
✓ Notion 连接正常
✓ 输出列已就绪
✓ Twitter cookie 已配置（如适用）

开始评估 KOL...
```

然后继续执行下面的第一步。

---

---

### 第一步：读取 Notion 表格

#### 定位表格

**读取 Notion 的两条路径，按优先级选择：**

**路径 A（有 Notion MCP 时）：**
检查当前会话的可用 MCP 工具列表里是否有 Notion 相关工具（常见名：`notion-fetch`、`notion_retrieve`、`notion-search` 等，工具名因 MCP 实现而异）。
- 如果 $ARGUMENTS 包含 Notion 链接或页面名称 → 用可用的 Notion fetch/retrieve 工具直接读取
- 如果 $ARGUMENTS 为空 → 用 Notion search 工具搜索关键词 "KOL" 或 "达人"，展示给用户确认后继续

**路径 B（无 Notion MCP 时）：**
从 `.env` 读取 API Key，通过以下命令获取数据：
```bash
cd "$KOL_EVAL_DIR"
NOTION_API_KEY=$(grep NOTION_API_KEY .env | cut -d= -f2) \
NOTION_DATABASE_ID=$(grep NOTION_DATABASE_ID .env | cut -d= -f2) \
uv run python -c "
from kol_eval.notion_io import fetch_kol_records
records = fetch_kol_records()
for r in records:
    print(r.name, r.url, r.price, r.currency)
"
```

#### 读取字段

从表格中提取每个 KOL 的：
- **链接**：Twitter/X 或 YouTube 主页 URL（必须有）
- **询价**：每条内容的报价，支持 ¥ 或 $（必须有）
- **备注**：如有，保留，用于报告补充信息

如果某行没有链接或询价，跳过该行，在最终报告中标注"信息不全，已跳过"。

告诉用户："找到 X 个 KOL，开始逐一抓取数据..."

---

### 第二步：逐个抓取 KOL 数据

对每个 KOL，依次完成以下抓取。使用 `/browse` 工具访问页面。

#### 平台识别

根据链接自动判断平台：
- 包含 `twitter.com` 或 `x.com` → Twitter/X
- 包含 `youtube.com` 或 `youtu.be` → YouTube
- 其他平台 → 标注"暂不支持该平台"，跳过

**注意：**
- Twitter/X 需要登录才能看到完整曝光数据。如果抓取时遇到登录墙，提示用户先运行 `/setup-browser-cookies` 导入 Twitter cookies，然后继续。
- YouTube 无需登录，公开数据可直接抓取。

---

#### Twitter/X 抓取流程

**Step A：抓取主页**

访问 `x.com/[handle]`，提取：
- 粉丝数（Followers）
- 关注数（Following）
- 账号简介（Bio）
- 加入时间
- 置顶推文（如有）
- 总推文数

**Step B：抓取近期推文**

在主页向下滚动，收集最近 10 条推文的数据（排除转推他人的内容，只看原创帖）：
- 发布时间
- 内容摘要（前50字）
- 曝光数（Views）
- 点赞数（Likes）
- 评论数（Replies）
- 转推数（Retweets/Reposts）
- 书签数（如显示）

如果推文不足 10 条，记录实际数量，标注样本量。

**Step C：抓取评论区（取互动量最高的前3条推文）**

对互动量最高的前3条推文，点进去读评论区前20条评论，提取：
- 评论语言分布（中文/英文/其他）
- 评论情感基调（正面/中性/争议/负面）
- 评论者画像特征（普通用户/行业人士/粉丝/机器人迹象）
- 是否有大量重复语义评论（刷评论信号）

---

#### YouTube 抓取流程

**Step A：抓取频道主页**

访问频道链接，提取：
- 订阅数（Subscribers）
- 总播放量（Total Views，在"关于"页）
- 频道创建时间
- 频道简介
- 内容分类/标签

**Step B：进入"视频"标签，抓取近期视频**

切换到视频列表，按"最新"排序，收集最近 10 个视频：
- 标题
- 发布时间
- 播放量
- 点赞数（如显示）
- 评论数
- 视频时长

**Step C：抓取评论区（取播放量最高的前2个视频）**

点进视频，读评论区前20条，提取：
- 评论语言分布
- 评论情感基调
- 是否有水军特征（大量 emoji 堆砌、过度吹捧、语义重复）
- 粉丝类型信号（忠实粉丝 vs 路过观众 vs 专业人士）

---

### 第三步：构建画像

对每个 KOL，基于抓取数据生成两个画像。

#### 账号画像（KOL Profile）

```
账号名称：
平台：
粉丝/订阅量：
账号成立时间：
内容垂类：[自动判断，如：科技/财经/生活方式/美妆/游戏/教育/综合]
内容形式：[文字为主 / 图文 / 视频 / 混合]
发布频率：[根据近10条内容的时间间隔推算，如：日更 / 3次/周 / 周更]
内容风格：[专业知识型 / 娱乐互动型 / 观点评论型 / 生活记录型]
账号简介摘要：
```

#### 受众画像（Audience Profile）

基于评论区分析推断，明确标注"基于评论区样本推断，非官方数据"：

```
主要语言：[中文xx% / 英文xx% / 其他]
地域信号：[基于评论语言和话题推断]
受众类型：[忠实粉丝型 / 泛兴趣路人型 / 行业专业人士型 / 混合型]
互动情感：[正面主导 / 中性讨论为主 / 存在争议]
水军风险：[低 / 中 / 高（说明依据）]
典型评论风格举例：[1-2句代表性评论描述]
```

---

### 第四步：计算量化指标

对每个 KOL，计算以下所有指标。展示公式和数值。

#### 基础统计

- **样本量**：实际收集的内容条数
- **平均曝光/播放量**（Avg Views）
- **平均点赞数**（Avg Likes）
- **平均评论数**（Avg Comments）
- **平均转发/分享数**（Avg Shares，有则计算）
- **数据波动性**：最高曝光 / 最低曝光，比值 > 5x 则标记"数据不稳定"
- **内容发布频率**（条/周，基于样本时间跨度）

#### 互动率指标

**综合互动率 ER**
```
ER = (Avg Likes + Avg Comments + Avg Shares) / 粉丝数 × 100%
```

**曝光互动率 View ER**
```
View ER = (Avg Likes + Avg Comments + Avg Shares) / Avg Views × 100%
```

**点赞率 Like Rate**
```
Like Rate = Avg Likes / Avg Views × 100%
```

**评论深度比 C/L Ratio**
```
C/L Ratio = Avg Comments / Avg Likes × 100%
```
> 低于 1% 是买赞信号；高于均值说明内容引发真实讨论

**粉丝触达率 Reach Rate**
```
Reach Rate = Avg Views / 粉丝数 × 100%
```

#### 商业价值指标

**CPM（千次曝光成本）**
```
CPM = 询价 / (Avg Views / 1000)
```

**CPE（单次互动成本）**
```
CPE = 询价 / (Avg Likes + Avg Comments + Avg Shares)
```

**粉丝千人价**
```
粉丝CPM = 询价 / (粉丝数 / 1000)
```

---

### 第五步：打分

#### Twitter 行业基准

| 粉丝体量 | ER 优秀 | ER 合格 | ER 偏低 | 合理 CPM 区间（$） |
|---------|---------|---------|---------|-----------------|
| 纳米 1K-10K | >5% | 2-5% | <2% | $3-10 |
| 微型 10K-100K | >3% | 1-3% | <1% | $5-20 |
| 中型 100K-500K | >1.5% | 0.5-1.5% | <0.5% | $10-40 |
| 大型 500K-1M | >1% | 0.3-1% | <0.3% | $20-80 |
| 头部 1M+ | >0.5% | 0.2-0.5% | <0.2% | $40-150 |

#### YouTube 行业基准

| 订阅量 | 触达率优秀 | 触达率合格 | 点赞率参考 | 合理 CPM 区间（$） |
|-------|----------|----------|----------|-----------------|
| 1万以下 | >30% | 10-30% | >3% | $10-30 |
| 1-10万 | >20% | 8-20% | >2.5% | $15-50 |
| 10-50万 | >15% | 5-15% | >2% | $20-80 |
| 50-100万 | >10% | 3-10% | >1.5% | $30-120 |
| 100万+ | >8% | 2-8% | >1% | $50-200 |

#### 打分规则（满分100分）

**A. CPM 性价比（30分）**
- CPM 低于行业基准下限：30分
- CPM 在基准范围内：20分
- CPM 超出上限 50% 以内：10分
- CPM 超出上限 50% 以上：0分

**B. 互动率质量（30分）**
- ER 达到"优秀"：30分
- ER 达到"合格"：20分
- ER 偏低但 View ER > 3%：10分
- ER 偏低且 View ER < 2%：0分

**C. 真实性信号（25分）**
- C/L Ratio 高于均值：8分；正常区间：5分；< 1%：0分
- 数据稳定性 < 3x：8分；3-5x：4分；> 5x：0分
- Reach Rate 高于合格基准：8分；偏低：4分；极低：0分
- 受众画像水军风险低：+1分；中：0分；高：-3分

**D. 报价合理性（15分）**
- 询价 < 行业 CPM 基准下限对应报价：15分
- 询价在合理区间：10分
- 询价偏高但有谈判空间：5分
- 询价远超市场价：0分

#### 综合评级

| 总分 | 评级 | 建议 |
|------|------|------|
| 80-100 | S 强烈推荐 | 优先锁定，可争取长期合作 |
| 65-79 | A 推荐合作 | 值得合作，可适当压价 |
| 50-64 | B 谨慎合作 | 建议先小单测试 |
| 35-49 | C 风险偏高 | 大幅压价或等更多数据 |
| 0-34 | D 不建议 | 数据存疑，跳过 |

---

### 第六步：合作决策判断

#### 一票否决项（触发任一项，直接降级或覆盖评级）

| 否决项 | 触发条件 | 结果 |
|--------|---------|------|
| 数据真实性存疑 | C/L Ratio < 1% 且 ER 偏低 | 强制判 D，无论总分 |
| 受众水军风险高 | 评论区水军信号明显 | 降一档，标注风险 |
| 数据极度不稳定 | 最高/最低曝光比 > 10x | 降一档 |
| 报价严重虚高 | CPM > 行业基准上限 3 倍 | 降一档 |
| 样本量不足 | 实际抓取数据 < 3 条 | 判"数据不足，暂缓" |

#### 加分信号（在结论中说明）

| 加分信号 | 触发条件 | 含义 |
|---------|---------|------|
| 双重真实认证 | C/L Ratio 高于均值 且 ER 优秀 | 粉丝真实且活跃，强买信号 |
| 极致性价比 | CPM 低于基准下限 50% 以上 | 罕见，优先锁定 |
| 内容稳定可靠 | 最高/最低曝光比 < 2x | 风险低，适合长期合作 |
| 增长期 KOL | Reach Rate > 30%（Twitter）或 > 40%（YouTube） | 算法在推，现在比以后便宜 |
| 受众精准 | 画像与品牌目标受众高度吻合 | 转化潜力高（需结合品牌判断） |

#### 最终结论五选一

**合作** — 分数 ≥ 65 且无否决项
> 直接推进，谈细节

**有条件合作：先小单测试** — 分数 50-64 或数据稳定性弱
> 先投一条，看实际转化再决定续投

**合作，但必须压价** — 分数 ≥ 65 但 CPM 偏高
> KOL 质量没问题，问题在报价，给出目标价区间

**暂缓：等更多数据** — 样本量不足，或数据波动极大
> 要求 KOL 提供更多历史内容数据再评估

**不合作** — 分数 < 35，或触发真实性存疑否决项
> 明确拒绝，节省运营时间

---

### 第七步：输出报告

#### 单个 KOL 完整报告

```
========================================
KOL 评估报告：[@handle / 频道名] [平台]
抓取时间：[时间]
========================================

账号画像
--------
粉丝/订阅：xxx
成立时间：xxxx年
内容垂类：xxx
发布频率：xxx
内容风格：xxx
简介：xxx

受众画像（基于评论区样本推断）
--------
主要语言：中文xx% / 英文xx%
地域信号：xxx
受众类型：xxx
互动情感：xxx
水军风险：低/中/高

数据统计
--------
样本量：x 条内容（时间跨度：x天）
平均曝光：xxx（最低 xxx / 最高 xxx，波动比 x.x倍）
平均点赞：xxx
平均评论：xxx
平均转发：xxx

互动指标
--------
ER（粉丝互动率）：x.xx%  [优秀/合格/偏低]
View ER（曝光互动率）：x.xx%
Like Rate（点赞率）：x.xx%
C/L Ratio（评论深度比）：x.xx%  [优质/正常/偏低]
Reach Rate（粉丝触达率）：x.xx%  [优秀/合格/偏低]

商业指标
--------
询价：¥/$ xxx
CPM：¥/$ xx.xx  [低于/处于/高于行业基准]
CPE：¥/$ xx.xx
粉丝千人价：¥/$ xx.xx

综合评分
--------
CPM 性价比：xx/30
互动率质量：xx/30
真实性信号：xx/25
报价合理性：xx/15
总分：xx/100  →  [S/A/B/C/D]
[否决项触发说明，如有]
[加分信号说明，如有]

合作建议
--------
结论：[合作 / 有条件合作：先小单 / 合作但必须压价 / 暂缓 / 不合作]

理由：
- [最关键理由，带具体数字]
- [第二个理由]
- [否决项或加分信号，如有]

目标成交价：¥/$ xxx（如建议合作）
谈判切入点：[一句话可以直接用的说辞]
========================================
```

#### 多 KOL 横向对比表

所有 KOL 评估完成后，输出汇总对比表，按综合分从高到低排序：

```
| KOL | 平台 | 粉丝 | 询价 | CPM | ER | C/L | 水军风险 | 综合分 | 结论 |
|-----|------|------|------|-----|-----|-----|---------|--------|------|
```

---

### 第八步：写回 Notion（自动执行，无需用户确认）

所有 KOL 评估完成后，**立即自动**将结果写回 Notion，不需要询问用户。

#### 写回路径选择

**路径 A（有 Notion MCP 时）：**
用当前可用的 Notion update 工具（常见名：`notion-update-page`、`notion_update`、`notion-update-data-source` 等）写入。
如果 Notion 页面是**页面内嵌表格**（非独立 Database），用 update page 的 `replace_content` 或 `update_content` 命令操作表格内容。

**路径 B（无 Notion MCP 时）：**
通过 Python CLI 写回：
```bash
cd "$KOL_EVAL_DIR"
NOTION_API_KEY=$(grep NOTION_API_KEY .env | cut -d= -f2) \
NOTION_DATABASE_ID=$(grep NOTION_DATABASE_ID .env | cut -d= -f2) \
uv run kol-eval run --handle @[handle]
```

#### 表格列定义（供参考，实际以用户 Notion 表格结构为准）

| 列名 | 说明 | 数据来源 |
|------|------|---------|
| 名字 | Twitter handle | 原表保留 |
| 推特链接 | x.com URL | 原表保留 |
| 粉丝数 | 抓取到的最新粉丝数 | 抓取更新 |
| 个人简介 | 账号 bio | 原表保留 |
| 报价 | 用户填写的询价 | 原表保留 |
| 转:赞:播 | 均转发:均点赞:均浏览，归一化为 1:x:y（除以均转发）；衡量内容扩散力 | 计算写入 |
| CPM$ [报价÷中位浏览K] | 报价($) ÷ (中位数曝光 ÷ 1000)；用中位数避免病毒帖拉偏 | 计算写入 |
| 均浏览量 | 近期帖子平均曝光/播放量（算术平均） | 抓取计算 |
| 均点赞 | 近期帖子平均点赞数 | 抓取计算 |
| 均评论 | 近期帖子平均评论数 | 抓取计算 |
| 均转发 | 近期帖子平均转发/转推数 | 抓取计算 |
| ER% [互动÷粉丝] | (均点赞+均评论+均转发) ÷ 粉丝数 × 100 | 计算写入 |
| C/L% [评论÷点赞] | 均评论 ÷ 均点赞 × 100；<1% 是买赞信号 | 计算写入 |
| 综合分 | 0-100 总分，带降级标注（如"72→B"表示原分72但因否决降为B级） | 计算写入 |
| 评级 | S/A/B/C/D 最终评级（含否决降级后） | 计算写入 |
| 建议 | 操作建议（合作/先小单测试/大幅压价/不合作） | 计算写入 |
| 目标价 | 建议成交价（$）；不合作填"-" | 计算写入 |
| 评估日期 | YYYY-MM-DD | 自动写入 |

#### 写入规则

- **已评估的 KOL**：填入所有评估列
- **未评估的 KOL**：保留原有数据，新增列留空
- **报价统一换算为美元**：人民币按 1 USD = 7.2 CNY 换算，写入表格时统一显示为 $xxx（不保留原始 ¥ 格式）
- 写入完成后打印："✓ 已自动写回 Notion（共更新 N 条）"

---

### 注意事项

- Twitter 抓取如遇登录墙，提示用户运行 `/setup-browser-cookies`，完成后继续，不要放弃
- 抓取时如遇反爬（页面加载异常），等待3秒后重试一次，仍失败则标注"抓取失败"，跳过该 KOL
- 货币统一换算：混用人民币/美元时，按 1 USD = 7.2 CNY，并在报告中注明
- 不要捏造或估算抓取失败的数据，缺失项直接标注"未获取"
- 受众画像结论必须注明"基于评论区样本推断，非官方数据"，避免过度确定
- 样本量不足 5 条时，所有结论加注"样本量有限，仅供参考"

---

# 模式四 · 计划（plan）

输入：$ARGUMENTS（可填平台、时间范围、总预算、Launch日期；留空则逐步询问）

### 用途

根据产品阶段和 Launch 节点，将 KOL 合作拆分为多条并行线，为每条线生成完整的预算表和漏斗数据。

---

### 第一步：收集基本信息

如果 $ARGUMENTS 为空或信息不全，依次询问以下问题（一次问完，不要逐个提问）：

> "需要几个信息来生成计划：
> 1. **平台**：Twitter / YouTube / LinkedIn / 组合？
> 2. **注册目标**：目标注册人数是多少？
> 3. **计划开始日期**：从哪天开始（默认今天）？
> 4. **总预算上限**：这次 KOL 投放的总预算是多少？（$或¥）
> 5. **注册→付费目标转化率**：有目标值吗？（没有则用行业均值 5-8%）
> 6. **[Twitter/YouTube限定] Launch 日期**：产品正式发布是哪天？（LinkedIn不需要）"

等用户回答后继续。

---

### 第二步：判断阶段结构

根据「计划开始日」到「Launch 日」的天数，自动判断阶段划分：

**天数 ≥ 21天（有完整准备周期）：**
- Track A：日常运营期（开始日 → Launch 前1天）
- Track B：Launch KOL 准备（与 A 并行，建联截止 = Launch 日 - 21天）
- Launch Day：集中发布（Launch 日当天）

**天数 < 21天（时间紧张）：**
- 标注警告：⚠️ 距 Launch 不足 21 天，YouTube 来不及（制作周期 3-4 周），只能做 Twitter
- 只输出 Twitter 单线计划

**YouTube 特别说明（每次都输出）：**
> YouTube KOL 从建联到视频发出最快 3 周。建联截止日 = Launch 日 - 21天。超过截止日签不下来的直接放弃，不要拖。

**LinkedIn 阶段结构（无 Launch Day 概念，按周滚动）：**

LinkedIn 不依赖 Launch 节点，而是以「每周签约→次周发帖」的滚动节奏推进：

1. 根据注册目标反推所需曝光：注册目标 ÷ 0.28% = 总曝光
2. 根据总曝光反推 KOL 数量：总曝光 ÷ 35K（标准档均值）= 所需人数
3. 根据所需人数反推外联量：KOL人数 ÷ 34%（签约转化率）= 需接触人数
4. 每周签约节奏：6条DM/天 × 40%回复 × 85%同意 × 5天 = **9人/周**
5. 完成时间 = ceil(KOL总数 ÷ 9) + 1 周（第1周只签不发，第2周起每周同步发帖）

自动生成每周节奏表（格式见第四步 LinkedIn 模板）。

---

### 第三步：平台参数表

根据用户选择的平台，调用对应参数：

#### Twitter 参数基准

| 指标 | 数值 | 说明 |
|------|------|------|
| 平均每条曝光 | 1.5w - 3w | 10k-50k粉丝账号正常范围；爆帖可达 30w+ |
| CTR（曝光→官网点击） | 1% - 2% | 垂类 AI/tech 受众 |
| 官网→注册转化率 | 20% - 25% | |
| CPM 参考 | $30 - $50 | 中文推特正常范围 |
| 每人预算参考 | $150 - $300 | 按账号量级和内容形式浮动 |
| 合作形式 | Post / Thread | 禁发理念/观点类，只发用户场景/Aha Moment/功能介绍 |

**Launch Day Twitter 加成：**
- CPM 略降至 $20-$40（集中发布算法加权）
- 配合 Quote 转发扩散

#### YouTube 参数基准

| 指标 | 数值 | 说明 |
|------|------|------|
| 平均每条播放量 | 1w - 3w | 5w-50w 订阅频道，发布后2周内 |
| CTR（播放→官网点击） | 1% - 2% | 描述栏链接，垂类受众 |
| 官网→注册转化率 | 10% - 20% | YouTube 冷流量略低于 Twitter |
| CPM 参考 | $67 - $200 | mid-micro 账号有 minimum fee，CPM 天然偏高 |
| 每人预算参考 | $500 - $2,000 | 按订阅量级浮动 |
| 合适量级 | 5w - 50w 订阅 | 大号响应慢，优先中小号 |
| 合作形式 | 专题测评 / Tutorial / Use Case | 非贴片广告，需深度内容 |
| 建联→发布周期 | 3 - 4 周 | 硬约束，不可压缩 |

#### LinkedIn 参数基准

**漏斗结构（LinkedIn 专属）：**

| 步骤 | 转化率 | 说明 |
|------|--------|------|
| 曝光 → 官网点击（CTR） | **1%** | 链接必须放**评论区**；放正文则被算法压制 -30~50% |
| 官网 → 下载 | **40%** | |
| 下载 → 注册 | **70%** | |
| **综合转化率（曝光→注册）** | **0.28%** | = 1% × 40% × 70% |

**阶梯定价方案：**

| 档位 | 赞助曝光保底 | 支付金额 | CPM | CPR |
|------|------------|---------|-----|-----|
| 入门档 | 15–25K | **$30** | $1.50 | $0.54 |
| 标准档 | 25–45K | **$50** | $1.43 | $0.45 |
| 优质档 | 45–70K | **$70** | $1.40 | $0.36 |
| 头部档 | 70K+ | **$100** | $1.25 | $0.36 |

**预算估算用标准档均值：35K曝光 / $50 / CPM $1.43**

**KOL筛选标准：**

| 指标 | 标准 | 说明 |
|------|------|------|
| 粉丝数 | 8万–20万 | 大号响应慢、CPM贵，中小号性价比高 |
| 近30天Top3帖均值曝光 | ≥ 25K | 有机表现基准 |
| 含外链帖赞助曝光 | ≥ 15K | **最关键指标** |
| **赞助/有机比** | **> 50%** | **硬过滤器：低于50%直接淘汰**（Fakhre Alam 14% = 红旗） |
| 发帖频率 | 每周 ≥ 2篇 | |
| 内容垂类 | AI / SaaS / Productivity | |

**其他参数：**

| 指标 | 数值 | 说明 |
|------|------|------|
| 外联签约转化率 | 34% | 需接触人数 = KOL数 ÷ 34% |
| 每周签约节奏 | 9人/周 | 6条DM/天 × 40%回复 × 85%同意 × 5天 |
| 建联→发布周期 | **1 周** | 远快于 YouTube；签约后催发素材包 |
| 合作形式 | 个人故事 / Aha Moment / 功能步骤 | **禁止：广告文案、"sign up"等词、理念宏观叙事** |

---

### 第四步：生成每条线的预算表

**Twitter / YouTube 用标准模板：**

```
## [线名称]（[日期范围]）

| 维度 | 内容 | 备注 |
|------|------|------|
| 计划时间 | [开始日 - 结束日（X天）] | [阶段名称] |
| 核心目标 | [量化目标，如：累计曝光150w / 筛出20人优质KOL List] | |
| 合作内容类型 | [Post/Thread 或 专题测评/Tutorial] | [内容禁忌说明] |
| 合作数量 | [X篇（X篇/天 × X天）] | |
| KOL 画像 | [描述] | |
| 量级与筛选标准 | [粉丝/订阅量范围] | |
| 平均每条曝光 | [Xw] | |
| 每人预算 | [$X - $X] | [砍价策略] |
| CPM 参考 | [$X - $X] | |
| 预计总曝光 | [数量 × 均值 = Xw] | |
| 预计官网点击 | [总曝光 × CTR = X次] | |
| 预计注册人数 | [点击 × 注册率 = X人] | |
| 预计注册→付费 | [注册 × 转化率% = X人] | |
| 总预算 | [$X - $X] | [X篇 × $X-$X] |
| 参考Brief | [链接，如有] | |
```

**LinkedIn 用专属模板（含阶梯预算明细 + 周节奏表）：**

```
## LinkedIn KOL 计划

### 核心指标

| 指标 | 数值 | 计算依据 |
|------|------|---------|
| 注册目标 | [X人] | |
| 所需总曝光 | [X万] | 注册目标 ÷ 0.28% |
| 所需KOL数量 | [X人] | 总曝光 ÷ 35K（标准档均值） |
| 需接触人数 | [X人] | KOL数 ÷ 34%（签约转化率） |
| 每周签约节奏 | 9人/周 | 6条DM × 40%回复 × 85%同意 × 5天 |
| 完成时间 | [X周后，即X月X日] | ceil(KOL数 ÷ 9) + 1 周 |
| 每日DM量 | 6条/天 | |

### 预算明细（阶梯定价）

| 档位 | 赞助曝光保底 | 人数 | 占比 | 单价 | 小计 |
|------|------------|------|------|------|------|
| 入门档 | 15–25K | [X人] | 10% | $30 | $[X] |
| 标准档 | 25–45K | [X人] | 60% | $50 | $[X] |
| 优质档 | 45–70K | [X人] | 25% | $70 | $[X] |
| 头部档 | 70K+ | [X人] | 5% | $100 | $[X] |
| **合计** | | **[X人]** | 100% | **均值~$55** | **$[总计]** |

三档预算情景：底线 $[X]（全入门）/ 预期 $[X]（阶梯分布）/ 上限 $[X]（全优质）

### CPM / CPR

| 指标 | 数值 | 计算 |
|------|------|------|
| CPM | $[X] | 总预算 ÷ 总曝光万数 × 1,000 |
| CPR | $[X] | 总预算 ÷ 注册目标 |
| ROI（12个月） | +[X]% | (注册目标 × 5%付费 × $20/月 × 12 − 总预算) ÷ 总预算 |

### 每周签约与发帖节奏

| 周次 | 日期 | 签约目标 | 累计签约 | 当周发帖 | 累计曝光 | 累计注册 |
|------|------|---------|---------|---------|---------|---------|
| Week 1 | [日期] | 9人 | 9人 | 0（建联期） | 0 | 0 |
| Week 2 | [日期] | 9人 | 18人 | 9人 | [X]万 | ~[X] |
| ... | | | | | | |
| **Week N** | **[日期]** | **—** | **[X人]** | **[X人]** | **[X]万** | **~[目标] ✅** |
```

---

### 第五步：漏斗汇总表

**Twitter / YouTube 用标准汇总：**

```
## 全渠道漏斗汇总

| 线 | 时间 | 合作数量 | 预计总曝光 | 官网点击 | 注册 | 付费转化 | 预算 |
|----|------|---------|----------|---------|------|---------|------|
| Track A 日常运营 | | | | | | | |
| Track B Launch准备 | | | | | | | |
| YouTube | | | | | | | |
| **合计** | | | | | | | |
```

**LinkedIn 用时间线汇总（含阶段注册进度）：**

```
## LinkedIn 注册进度预测

| 时间节点 | 累计已发帖KOL | 累计曝光 | 累计注册 | 预算消耗 |
|---------|------------|---------|---------|---------|
| [开始日+1周] | 0 | 0 | 0 | $0 |
| [中期节点] | [X人] | [X万] | ~[X] | ~$[X] |
| [目标达成日] | [X人] | [X万] | ~[目标] ✅ | ~$[总计] |
```

---

### 第六步：前置条件清单

```
## 前置条件（缺一不可）

| # | 条件 | 截止时间 | 适用平台 |
|---|------|---------|---------|
| 1 | KOL候选名单锁定（150+人）| [开始日] | 全部 |
| 2 | 内容素材包就绪（场景图/截图/Aha Moment文案） | [开始日] | 全部 |
| 3 | 官网UTM追踪链接配置（每KOL独立短链） | 发帖前 | 全部 |
| 4 | Brief文档最终版确认 | [开始日] | 全部 |
| 5 | [YouTube限定] 建联截止日（Launch - 21天）= [日期] | [日期] | YouTube |
| 6 | [LinkedIn限定] KOL筛选：赞助/有机比截图已收集 | 签约前 | LinkedIn |
| 7 | [LinkedIn限定] 链接统一放评论区（Brief明确注明） | 发帖前 | LinkedIn |
```

---

### 注意事项

- 所有曝光和转化数据均为预估范围，实际以投放后数据为准
- Twitter 内容类型严格限定为：用户场景 / Aha Moment / 功能步骤介绍；**不发理念/观点/宏观叙事类内容**
- YouTube CPM 天然偏高（因 minimum fee），不要用 Twitter CPM 标准衡量 YouTube
- Launch Day 的核心逻辑是集中爆发，KOL 发布时间尽量对齐同一天
- 预算超出用户上限时，优先削减合作数量，不降每人预算（低预算导致内容质量下降）
- **[LinkedIn专属]** 筛选 KOL 的核心指标是**赞助/有机曝光比**，而非粉丝数。低于50%直接淘汰，无论粉丝多少
- **[LinkedIn专属]** 链接必须放评论区，不放正文。Brief里明确注明，否则算法压制帖子曝光 -30~50%
- **[LinkedIn专属]** 内容禁止广告文案感；第一人称故事格式、禁用"sign up""try now"等词
- **[LinkedIn专属]** 阶梯预算用预期值（阶梯分布）做计划，不用底线（全入门档）做承诺
