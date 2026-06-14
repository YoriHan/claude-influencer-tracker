---
name: kol-refresh
description: "Re-scrape already-tracked KOLs and update ONLY auto-scraped data fields (followers, views, last-post), never overwriting manual notes, pricing, or pipeline status. Trigger when: 'kol-refresh', '刷新 KOL 数据', '更新达人数据', 'refresh all-twitter', 'refresh all-youtube', '刷新推进中'."
---

> **Helio 运行说明**：本 skill 由你的自然语言请求触发（不是 Claude Code 的 `/命令`）。下文中出现的 `$ARGUMENTS` 指你在请求里给出的参数——链接 / @handle / 关键词等；没给参数时，按各步骤里的「留空」分支处理。

# KOL 数据刷新

输入：$ARGUMENTS（一个或多个 @handle 或 KOL 链接；留空则询问）

## 用途

重新爬取已入库 KOL 的最新数据，只更新数据字段，**不覆盖**手动填写的字段（回复状态、报价、合作备注、推进状态等）。

适用场景：
- 入库超过 1 个月，粉丝/均播已变化
- 想检查某个 KOL 是否还活跃
- 批量刷新所有「推进中」KOL 的最新数据

---

## 第零步：读取配置

```bash
CONFIG="$HOME/.claude/kol-tracker/config.json"
[ -f "$CONFIG" ] && cat "$CONFIG" || echo "NOT_FOUND"
```

**NOT_FOUND** → 提示：
> "还没有初始化配置，请先运行 `/kol-add` 完成首次设置。"
停止。

从 config 读取 `twitter_db_id`、`youtube_db_id`、`twitter_cookie_file`。

---

## 第一步：解析目标

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

## 第二步：从 Notion 读取已有记录

对每个 handle，用 notion-search 或 notion-fetch 找到对应 page_id，并记录以下**不可覆盖字段**（保留用户手动填写的内容）：

**Twitter 不可覆盖：** 回复状态、推进状态、合作方式、报价、imp_24h、imp_72h、engagement、CPM、发布日期、post链接、合作备注

**YouTube 不可覆盖：** 回复状态、达人报价、CPM、合作方式、备注

找不到对应记录时标注「未在数据库中，跳过（可用 /kol-add 添加）」。

---

## 第三步：登录检查

同 `/kol-add` 第二步，此处不重复，直接执行相同流程。

---

## 第四步：重新爬取数据

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

## 第五步：更新 Notion

调用 notion-update-page，**只更新**以下字段（其余保持原值不动）：

**Twitter 可更新：** 粉丝、层级、DM状态、区域、账号标签、近5均浏览、近5均赞、最后发帖、活跃状态、YouTube链接

**YouTube 可更新：** 粉丝、层级、Email、区域、账号标签、近十均播K、最后发布、活跃状态、Twitter链接

多个 KOL 并行更新。

---

## 第六步：输出变化汇总

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

## 注意事项

- 不可覆盖字段由代码严格保护，不会因为刷新丢失手动填写的报价、备注等
- 活跃状态从「活跃」变为「不活跃」时，额外在合作备注里追加一条记录：`[YYYY-MM-DD 刷新] 已转为不活跃`，方便追溯
- 批量刷新时如果中途失败，已完成的不会回滚，重新运行会跳过无变化的条目
