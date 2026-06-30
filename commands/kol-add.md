# KOL 一键入库

输入：$ARGUMENTS（一个或多个 Twitter/X 或 YouTube 链接或 @handle，空格或换行分隔）

## 用途

粘贴 KOL 链接或 handle → 自动爬取全量数据 → 写入 Notion 数据库。
首次运行自动完成所有配置（建数据库、建视图、存配置），后续零配置直接用。

支持：Twitter/X、YouTube
支持格式：完整 URL 或 `@handle`（Twitter）/ 频道名（YouTube）

---

## 第零步：环境与配置检查（每次都执行）

### 检查 1：gstack browse 是否安装

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

### 检查 2：Notion MCP 是否可用

检查当前会话是否有 `notion-create-database`、`notion-create-pages`、`notion-update-page` 等工具。

**不可用** → 停止，提示：
> "需要先配置 Notion MCP。
> 参考：https://github.com/makenotion/notion-mcp-server
> 安装后重新运行 `/kol-add`。"

---

### 检查 3：读取本地配置

```bash
CONFIG="$HOME/.claude/kol-tracker/config.json"
[ -f "$CONFIG" ] && cat "$CONFIG" || echo "NOT_FOUND"
```

**NOT_FOUND** → 进入「首次配置向导」（Step A）。
**找到配置** → 检查 `twitter_db_id`、`youtube_db_id`、`setup_complete` 是否都有值，缺任意一项则重新走对应步骤。

---

### Step A：首次配置向导（仅第一次运行）

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

## 第一步：解析输入

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

## 第二步：Twitter 登录检查

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

## 第三步：批量抓取数据

依次处理每个 KOL（Twitter sleep 1.5s，YouTube sleep 0.8s）。

---

### Twitter 抓取流程

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

### YouTube 抓取流程

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

## 第四步：批量写入 Notion

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

## 第五步：输出汇总 + 可选 DM 草稿

### 入库结果表

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

### 可选：生成外联 DM 草稿

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

## 注意事项

- **Cookie 失效**：Twitter cookie 通常 7 天内有效。遇到登录失效（重定向到 sign in）时主动提示重新导出，不静默失败
- **抓取失败处理**：单个 KOL 失败时等待 2s 重试一次，仍失败则跳过并在汇总中标注，不阻塞其他 KOL
- **重复保护**：写入前检查 Handle 是否已存在，存在则跳过
- **macOS 兼容**：所有 grep 用 `-E` 不用 `-P`；文本提取用 python3
- **互动数据说明**：Twitter 浏览量仅在用户已登录时可见；未登录时 avg_views 填 0，在备注中标注"需登录查看"
- **`/kol-refresh`**：如需刷新已有 KOL 的数据，使用 `/kol-refresh @handle` 命令
