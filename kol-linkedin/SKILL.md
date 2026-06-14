---
name: kol-linkedin
description: "Batch-import LinkedIn KOL profiles into a Notion database: scrape follower count + headline, infer tags (AI/Vibe Coding/No Code/Productivity/Dev) and region, handle mixed X.com DM links. Trigger when: 'kol-linkedin', '导入 LinkedIn KOL', '把这些 LinkedIn 加进 Notion', pasting a batch of LinkedIn profile URLs."
---

> **Helio 运行说明**：本 skill 由你的自然语言请求触发（不是 Claude Code 的 `/命令`）。下文中出现的 `$ARGUMENTS` 指你在请求里给出的参数——链接 / @handle / 关键词等；没给参数时，按各步骤里的「留空」分支处理。

# LinkedIn KOL 批量入库

输入：$ARGUMENTS（LinkedIn URL 列表，空格或换行分隔；留空则提示粘贴）

## 用途

将一批 LinkedIn KOL 主页链接批量录入 Notion「LinkedIn KOL 总表」数据库，自动抓取粉丝数、headline 作为备注，并智能推断账号标签。

**触发场景：** 用户粘贴一批 LinkedIn 链接要求入库、或说"帮我把这些 LinkedIn 加进 Notion"

---

## 第零步：解析输入

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

## 第一步：读取 Notion 数据库结构

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

## 第二步：LinkedIn Cookie 检查

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

## 第三步：批量抓取 LinkedIn 数据

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

## 第四步：批量创建 Notion 条目

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

## 第五步：输出汇总

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

## 注意事项

- Cookie 文件保存在 `/tmp/linkedin_cookies.json`，下次运行时若 LinkedIn 仍然登录则无需重新导入
- macOS 上使用 `grep -E`，不使用 `grep -P`（-P 在 macOS 不支持）
- 所有 LinkedIn 文本提取使用 `python3 处理 $B text 输出文件`，不用 JS querySelector（React 动态渲染）
- 粉丝数显示 "500+" 或页面未显示时，备注中注明"粉丝数未公开"
