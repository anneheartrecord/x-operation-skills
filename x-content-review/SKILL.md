---
name: x-content-review
description: |
  X(Twitter) 账号数据内容复盘。分析上一周期的流量与内容表现:周度趋势、发帖时段转化(北京时间)、内容类别涨粉效率、单帖 A/B/C 分级,输出复盘报告并给出下周发帖指导(发什么、什么时候发)。
  触发方式:/x-content-review、「X复盘」「出X周报」「跑X数据」「复盘推特数据」,或用户丢 X Analytics CSV 进运营目录。
  X account content & traffic review. Analyzes weekly trends, posting time-slot conversion, category follower-efficiency, and post grading; outputs a review report with next-week posting guidance.
  Trigger: /x-content-review, "X review", "X weekly report", or new analytics CSVs.
---

# X 数据内容复盘

把 X Analytics 数据变成可执行的运营决策:什么类别涨粉快、什么时段发效率高、哪些帖子该扩成系列、哪些该换头重发、哪些选题该停。

## 数据源(三条路,按优先级)

1. **API 模式(首选,配了官方 API 凭证时)**:X 官方 pay-per-use 接口读自己账号数据,$0.001/请求,一次复盘不到 1 美分。官方接口稳定,且 `impression_count` 是真曝光数,口径与 analytics 后台对齐。凭证为四个 env(`X_API_KEY`/`X_API_SECRET`/`X_ACCESS_TOKEN`/`X_ACCESS_TOKEN_SECRET`),依赖 tweepy。
2. **Pulse 模式(免费兜底)**:cookie 登录态(env `X_AUTH_TOKEN`/`X_CT0`,依赖 twscrape)拉公开指标,views 为公开浏览数。
3. **CSV 模式(增强,用户主动导出时)**:X Analytics 后台两份 CSV(`account_overview_analytics*.csv` + `account_analytics_content*.csv`),独有「净涨粉/主页访问」,转化口径升级为「涨粉/万曝光」。**运营目录里有 7 天内的新 CSV 对时自动改走 CSV 模式**。

API 和 pulse 模式的涨粉趋势都靠粉丝数快照 JSONL 差值(每次跑自动追加快照,越用越准),转化口径为「收藏/万曝光」。

## 工作流程

### 第 1 步:选数据路径

- 先看用户运营目录(惯例 `30-outputs/运营/`)有无 7 天内导出的 CSV 对:有 → CSV 模式;
- 没有,四个 API env 齐 → API 模式:

```bash
python3 <skill目录>/scripts/fetch_x_api.py --limit 100 \
  --snapshot-file <运营目录>/x-follower-snapshots.jsonl > /tmp/x-pulse.json
```

- API 凭证不全 → pulse 模式:

```bash
python3 <skill目录>/scripts/fetch_x_pulse.py --user <handle> --limit 100 \
  --snapshot-file <运营目录>/x-follower-snapshots.jsonl > /tmp/x-pulse.json
```

两个脚本输出同构 JSON,后续分析命令一样。凭证缺失时脚本会报错并给配置指引。

### 第 2 步:跑分析脚本

```bash
# API / pulse 模式(两者输出同构,统一走 --pulse)
python3 <skill目录>/scripts/analyze_x_data.py --pulse /tmp/x-pulse.json \
  --snapshots <运营目录>/x-follower-snapshots.jsonl --days 7
# CSV 模式
python3 <skill目录>/scripts/analyze_x_data.py \
  --overview <最新overview.csv> --content <最新content.csv> --days 7
```

脚本输出 JSON(两种模式同构):
- `content.time_slots_beijing`:北京时间 2 小时分桶的时段表现(CSV 模式从 Post id 雪花 ID 反推发帖时间)
- `content.categories`:类别转化,reply 单列;pulse 口径「收藏/万曝光」,CSV 口径「涨粉/万曝光」
- `content.window_top_posts` / `repost_candidates_grade_b`:窗口 Top 帖与 B 级(低曝光高收藏,换头重发候选)
- pulse 另有 `followers_now`/`follower_trend`(粉丝快照趋势);CSV 另有 `overview.*`(周度趋势/净涨粉)

类别关键词表可用 `--categories 自定义.json` 覆盖(格式:`{"类别名": ["关键词", ...]}`)。

### 第 3 步:写复盘报告

基于 JSON 写 Markdown 周报,结构固定:

1. **本周大盘**:曝光、净涨粉、日均净涨粉(对照验收线,如日均 25+)、发帖数;与上周环比。
2. **时段结论**:哪个北京时间段「涨粉/万曝光」最高。注意剔除单帖爆款扭曲——若某时段数据由 1-2 条爆款贡献,要指出样本量问题,不要直接下结论。
3. **类别结论**:各类别涨粉效率排名,对照历史基准线,指出漂移。
4. **单帖分级**:A 级(扩成系列)、B 级(换头重发,列出候选)、C 级(停掉的选题方向)。
5. **下周指导**:发什么(3-5 个具体选题方向,可对照选题库)、什么时段发、避免什么。

报告落盘到用户运营目录(如 `30-outputs/运营/`),命名 `X周报-YYYY-MM-DD.md`。

### 第 4 步:顺手检查

- 若用户有 media kit 且数据超过 30 天未更新,提醒刷新。
- 若用户有账号运营手册/选题库,下周指导须与其对齐,不另起炉灶。

## 判断规则(硬口径)

- 涨粉效率一律用「涨粉数/万次曝光」,不用绝对涨粉数(消除曝光量差异)。
- A/B/C 分级:A=高曝光高收藏→扩系列;B=低曝光高收藏→内容好但包装/时机差,换头重发;C=双低→停选题。
- 时段/类别结论至少 3 条帖子样本才可下,不足时标注「样本不足,仅供参考」。
- reply 不参与时段分析(时间由对话决定,不是运营决策)。
- 所有时间以北京时间(UTC+8)表述。

## 登录态说明(Pulse 模式)

cookie 获取:浏览器登录 x.com → F12 → Application → Cookies → 复制 `auth_token` 和 `ct0`,存入 `~/.config/secrets/api-keys.env`:

```
export X_AUTH_TOKEN="..."
export X_CT0="..."
```

注意:退出 x.com 登录会使 cookie 失效;cookie 等同账号密码,绝不写入仓库或配置文件。
