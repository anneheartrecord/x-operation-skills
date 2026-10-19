---
name: x-schedule
description: |
  X(Twitter) 批量定时发帖排期。用登录 cookie 把一批文稿排进 X 原生定时队列(CreateScheduledTweet),到点由 X 服务器发布;用户可随时在 x.com「未发送的帖子」里审改删。默认时段 11:00/14:00/20:00/23:00(北京时间)。带确认门槛:先 dry-run 出排期计划,用户明确确认后才真正排期。
  触发方式:/x-schedule、「批量定时发布」「把这批文稿排期」「定时发帖」。
  Batch-schedule tweets into X's native scheduled queue via logged-in cookies. Dry-run plan first; schedules only after explicit user confirmation. Posts remain editable/deletable in x.com's unsent-posts UI until fire time.
  Trigger: /x-schedule, "schedule these tweets", "batch schedule posts".
---

# X 批量定时发帖(cookie · 原生定时队列)

把一批定稿文稿排进 X 的原生定时队列。核心原则:**排期就是发布指令,永远先 dry-run 出计划、等用户确认、再排**;排完用户仍可在 x.com「未发送的帖子 → 已排定」里改或删,这是最后一道人工审核权。

## 前置条件

- 环境变量 `X_AUTH_TOKEN` / `X_CT0`(与 x-content-review 同一套 cookie),国内另需 `X_PROXY`。
- 依赖 `curl_cffi`。本机用 x-skills 专用 venv 跑:`~/.venvs/x-skills/bin/python`(与 pulse 拉数 runner 同一环境);dry-run 不碰网络,系统 python3 也能跑。
- ⚠️ **非官方接口**:queryId 随 X 前端版本更换,404 时从浏览器 DevTools 抓新 id 更新脚本顶部常量。保持低频(每天几条),不批量高频调用。

## 工作流程(硬性顺序,不可跳步)

### 第 0 步:内容过闸

每条文稿先过 `x-post-gate`(发帖前四问 + 不发清单),被判「不发」的稿子不进排期。

### 第 1 步:dry-run 出排期计划

```bash
python3 <skill目录>/scripts/schedule_tweets.py --drafts a.md b.md [--start-date 2026-07-22]
# 或整个目录(按文件名排序):--drafts-dir <目录>
```

输出每条的排期时间(北京时间)、加权长度、内容预览。默认时段 `11,14,20,23`,可用 `--slots` 覆盖。超长(>280 加权字符)的稿会被标出,必须先改稿。把计划原样给用户看。

### 第 2 步:等用户明确确认

**只有用户明确说「排」「确认排期」「就按这个计划」等肯定指令才进第 3 步。**用户只是让「看看/改改」、或没对本次计划表态,一律不排。改了文稿或时段必须重新 dry-run。

### 第 3 步:排期

```bash
python3 <skill目录>/scripts/schedule_tweets.py --drafts a.md b.md --start-date 2026-07-22 --yes
```

逐条排入,条间隔 2 秒;任一条失败立即中止(不自动重试),如实报告已排/未排清单。

### 第 4 步:回报与登记

- 把排期结果(每条的时间 + scheduled_tweet_id)给用户,提醒可在 x.com「未发送的帖子」里最后审改。
- 已排期的文稿把 frontmatter `status` 改为 `scheduled` 并记 `scheduled_at`,发布后用户/复盘流程再改 `published`。

## 队列管理

```bash
python3 <skill目录>/scripts/schedule_tweets.py --list          # 查看当前定时队列
python3 <skill目录>/scripts/schedule_tweets.py --delete <id>   # 删除一条排期
```

## 判断规则(硬口径)

- 没过 x-post-gate 的内容不排;没 dry-run 过的计划不排;一次确认只对应一批排期。
- 排期失败不重试超过 1 次,不静默吞错;404 优先怀疑 queryId 过期。
- 每天不超过一批(≤ 时段数条);这是排期工具,不是刷量工具。
