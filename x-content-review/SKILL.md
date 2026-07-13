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

## 数据源(两条路,CSV 为权威源)

1. **CSV 模式(默认、权威)**:用户从 X Analytics 后台导出两份 CSV:
   - `account_overview_analytics*.csv` — 日度总览(曝光/涨粉/掉粉/发帖数/主页访问)
   - `account_analytics_content*.csv` — 单帖明细(曝光/收藏/涨粉/主页访问)
   - 用户惯例存放目录:`30-outputs/运营/`(知识库内)。自动选**文件名日期最新**的一对。
2. **Pulse 模式(可选、快速)**:用户没导 CSV 又想看最新情况时,跑 `scripts/fetch_x_pulse.py`(cookie 登录态,env `X_AUTH_TOKEN`/`X_CT0`,依赖 twscrape)。只有公开指标,**没有净涨粉和主页访问数据**,只做「最近帖子表现速览」,不出正式周报。

## 工作流程

### 第 1 步:定位数据

在运营目录找最新的 overview + content CSV。若 overview 最新日期距今超过 2 天,提醒用户重新导出(X Analytics → 下载数据),不要拿旧数据出周报。

### 第 2 步:跑分析脚本

```bash
python3 <skill目录>/scripts/analyze_x_data.py \
  --overview <最新overview.csv> --content <最新content.csv> --days 7
```

脚本输出 JSON:
- `overview.window_summary` / `window_daily` / `weekly_trend`:窗口汇总、日度明细、周度趋势
- `content.time_slots_beijing`:发帖时间从 Post id(Snowflake)反推,北京时间 2 小时分桶,含「涨粉/万曝光」
- `content.categories`:类别转化(涨粉/万曝光),reply 单列
- `content.window_top_posts` / `repost_candidates_grade_b`:窗口 Top 帖与 B 级(低曝光高收藏,换头重发候选)

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
