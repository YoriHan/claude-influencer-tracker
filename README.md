# Claude KOL Skills

## 在 Helio 安装（推荐）

在 Helio 里直接粘贴这个仓库链接，会一次性装上全部 5 个 KOL skill（kol-add / kol-refresh / kol-eval / kol-linkedin / kol-plan）：

```
https://github.com/YoriHan/influencer-skills
```

或命令行：

```bash
heliox skill install YoriHan/influencer-skills --description "KOL 发现 / 追踪 / 评估 / 投放计划"
```

> Helio 是按 repo 里的 `SKILL.md` 文件来装的（每个 `<名字>/SKILL.md` = 一个 skill）。下面的 `commands/*.md` 是给 Claude Code slash command 用的，两套都可用。

A collection of Claude Code slash commands for KOL (Key Opinion Leader) discovery, tracking, and collaboration planning — built for GTM teams who source influencers on Twitter/X, YouTube, and LinkedIn.

Install once, run forever. First use auto-creates your Notion database structure.

---

## What's Included

| Command | Description |
|---------|-------------|
| `/kol-add` | Paste any Twitter/X or YouTube link → auto-scrape all data → write to Notion |
| `/kol-refresh` | Re-scrape existing KOLs, update only data fields (keeps your manual notes safe) |
| `/kol-eval` | Deep evaluation: pull KOLs from Notion, scrape engagement data, score with CPM/ER/C-L ratio, write verdict back |
| `/kol-linkedin` | Batch import LinkedIn profiles into a Notion database |
| `/kol-plan` | Generate a full KOL collaboration plan with funnel math and budget breakdown |

---

## Prerequisites

### 1. Claude Code
Install from [claude.ai/code](https://claude.ai/code).

### 2. gstack (browse tool — required for scraping)
```bash
npm install -g @gstack/cli && gstack install
```
The browse daemon (`$B`) powers all Twitter/X and YouTube data extraction.

### 3. Notion MCP
Follow the setup guide at [github.com/makenotion/notion-mcp-server](https://github.com/makenotion/notion-mcp-server).

The following MCP tools must be available in your Claude Code session:
- `notion-create-database`
- `notion-create-pages`
- `notion-update-page`
- `notion-search`
- `notion-fetch`
- `notion-create-view`

### 4. kol-eval tool (required only for `/kol-eval`)
```bash
cd ~
git clone https://github.com/YoriHan/kol-eval.git
cd kol-eval && uv sync
uv run playwright install chromium
```

---

## Installation

Copy the skill files to your Claude Code commands directory:

```bash
mkdir -p ~/.claude/commands
cp commands/*.md ~/.claude/commands/
```

That's it. Restart Claude Code and the `/kol-*` commands will be available.

---

## Usage

### `/kol-add` — One-click KOL import

```
/kol-add @rohanpaul_ai https://youtube.com/@Chase-H-AI @swyx
```

**First run:** The skill auto-creates two Notion databases (`Twitter KOL` and `YouTube KOL`) with full schema and 6 filtered views per database (推进中 / 确认合作 / reach out / 待回复 / 未报价 / 暂停推进). Config is saved to `~/.claude/kol-tracker/config.json` — no setup needed after that.

**What gets scraped:**

| Platform | Fields |
|----------|--------|
| Twitter/X | Followers, tier, DM status, region, tags, avg views (last 5), avg likes (last 5), last post date, active status, YouTube cross-link |
| YouTube | Subscribers, tier, email (from About page), region, tags, avg views/K (last 10 videos), last publish date, active status, Twitter cross-link |

**Supported input formats:**
- `@handle` → Twitter
- `https://x.com/handle` or `https://twitter.com/handle`
- `https://youtube.com/@Channel` or `https://youtube.com/c/Channel`
- Mix of the above in one command

**Twitter cookies:** First Twitter scrape prompts you to export cookies via [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) and paste the file path. Saved to config and reused automatically.

---

### `/kol-refresh` — Refresh existing data

```bash
/kol-refresh @rohanpaul_ai @swyx        # specific handles
/kol-refresh all-twitter                 # all Twitter KOLs
/kol-refresh all-youtube                 # all YouTube KOLs
/kol-refresh 推进中                      # only KOLs in active pipeline
```

Refreshes only the auto-scraped fields. **Never overwrites** your manually entered fields: reply status, pricing, collaboration notes, progress status, etc.

Outputs a change summary table:

```
✅ 刷新完成（共 3 个）

| Handle        | Platform | Changes                           |
|---------------|----------|-----------------------------------|
| @rohanpaul_ai | Twitter  | Followers: 147K→162K, Views: 8.2K→11.4K |
| Chase-H-AI    | YouTube  | Avg views: 45K→52K               |
| @swyx         | Twitter  | No change                         |
```

---

### `/kol-eval` — Deep evaluation with scoring

Reads KOLs from Notion, scrapes full engagement data (comments, reply depth, audience signals), scores each KOL on a 100-point scale using:

- **CPM efficiency** (30 pts): actual CPM vs industry benchmark
- **Engagement quality** (30 pts): ER, View ER, Like Rate
- **Authenticity signals** (25 pts): C/L ratio, data stability, Reach Rate, bot risk
- **Pricing fairness** (15 pts): ask price vs market rate

Outputs verdict (合作 / 先小单测试 / 大幅压价 / 不合作) and writes results back to Notion automatically.

Requires the [kol-eval Python tool](https://github.com/YoriHan/kol-eval) installed separately.

---

### `/kol-linkedin` — Batch LinkedIn import

```
/kol-linkedin https://www.linkedin.com/in/username1/ https://www.linkedin.com/in/username2/
```

Scrapes follower count and headline from each profile, infers tags (AI / Vibe Coding / No Code / Productivity / Dev) and region (English / Chinese / India), and creates entries in a Notion LinkedIn KOL database.

Also handles mixed input with X.com DM links (associates them to the nearest LinkedIn account).

---

### `/kol-plan` — Collaboration plan with funnel math

```
/kol-plan Twitter 500 2025-07-01 $5000
```

Or run with no arguments — it asks for platform, registration target, start date, total budget, and launch date.

Generates a complete plan with:
- Track A (ongoing outreach) + Track B (launch prep) + Launch Day breakdown
- Per-track budget table with CPM, CTR, click-to-register rates
- Full funnel summary (impressions → clicks → registrations → conversions)
- Prerequisites checklist

Supports Twitter, YouTube, LinkedIn, and combined plans.

---

## Database Schema

### Twitter KOL

| Field | Type | Description |
|-------|------|-------------|
| Handle | title | @handle |
| 账号链接 | url | Profile URL |
| 粉丝 | text | e.g. "147.4K" |
| 层级 | select | nano / micro / mid / macro |
| DM状态 | text | 开放DM / 未开放DM |
| 区域 | select | en / cn / jp / other |
| 账号标签 | multi_select | AI / Vibe Coding / No Code / Productivity / Builder / Indie Dev |
| 近5均浏览 | number | Avg views, last 5 tweets |
| 近5均赞 | number | Avg likes, last 5 tweets |
| 最后发帖 | date | Last tweet date |
| 活跃状态 | select | 活跃 / 不活跃 |
| YouTube链接 | url | Cross-platform link |
| 回复状态 | select | reach out / 待回复 / 推进中 / 未报价 / 确认合作 / 暂停推进 |
| 推进状态 | select | 砍价中 / 内容发布 / 已付款 |
| 合作方式 | text | Deal type |
| 报价 | text | Quoted price |
| imp_24h / imp_72h | number | Post impressions at 24h / 72h |
| engagement | number | Total engagements |
| CPM | text | Cost per mille |
| 发布日期 | date | Content publish date |
| post链接 | url | Published content URL |
| 合作备注 | text | Collaboration notes |

### YouTube KOL

| Field | Type | Description |
|-------|------|-------------|
| Handle | title | Channel name |
| 账号链接 | url | Channel URL |
| 粉丝 | text | e.g. "92.2K" |
| 层级 | select | nano / micro / mid / macro |
| Email | email | Contact email from About page |
| 区域 | select | 英文 / 中文 / 印度 / 日本 / 其他 |
| 账号标签 | multi_select | AI / Vibe Coding / No Code / Productivity / Dev |
| 近十均播K | number | Avg views (thousands), last 10 videos |
| 最后发布 | date | Last video date |
| 活跃状态 | select | 活跃 / 不活跃 |
| Twitter链接 | url | Cross-platform link |
| 回复状态 | select | reach out / 待回复 / 推进中 / 未报价 / 确认合作 / 暂停推进 |
| 达人报价 | text | Quoted price |
| CPM | text | Cost per mille |
| Engagement Rate | text | ER% |
| 受众地区 | text | Audience geography |
| 合作方式 | text | Deal type |
| 备注 | text | Notes |

---

## Tier Classification

Applies to both Twitter and YouTube automatically:

| Tier | Followers/Subscribers |
|------|----------------------|
| nano | < 10K |
| micro | 10K – 100K |
| mid | 100K – 500K |
| macro | 500K+ |

---

## Config File

Stored at `~/.claude/kol-tracker/config.json` after first run:

```json
{
  "twitter_db_id": "<your-notion-db-id>",
  "youtube_db_id": "<your-notion-db-id>",
  "twitter_cookie_file": "/path/to/twitter_cookies.json",
  "setup_complete": true
}
```

Delete this file to re-run the first-time setup wizard.

---

## Tips

- **Twitter cookies expire** after ~7 days. Re-export from Cookie-Editor when prompted.
- **Batch add:** paste multiple handles/URLs in one command — they're processed in parallel.
- **Cross-platform detection:** if a Twitter bio contains a YouTube link (or vice versa), it's auto-populated in the corresponding field.
- **Active status:** any account with no posts in 30+ days is automatically flagged as 不活跃. When `/kol-refresh` detects a status change from active to inactive, it appends a timestamped note to the 合作备注 field.
- **Duplicate protection:** `/kol-add` checks if a handle already exists before writing.

---

## License

MIT
