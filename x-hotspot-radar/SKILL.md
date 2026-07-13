---
name: x-hotspot-radar
description: |
  X(Twitter) 热点雷达:从热点扫描 → 五重过滤 → 角度与结构提纲 → 风格校准 → 全文 → 去 AI 味 → 配图/封面 → 落盘草稿的落地推文全流程。本 skill 是编排层,写作文风、去 AI 味、生图都调用用户已有系统,不重造。产物默认落盘 tweets 目录草稿,发布交给 x-post。
  触发方式:/x-hotspot-radar、「X热点」「扫下热点」「今天发什么」「热点做条推文」「热点雷达」。
  X hotspot radar: scan hot topics → five-filter → angle & outline → style calibration → full draft → de-AI → cover/illustration → save as draft. An orchestration skill that reuses the user's writing/de-AI/image systems.
  Trigger: /x-hotspot-radar, "X hotspot", "what to post today", "turn this hot topic into a tweet".
---

# X 热点雷达(热点 → 落地推文)

把「今天有什么值得蹭的热点」变成一条符合用户文风、去过 AI 味、配好图、可直接发布的推文草稿。

**本 skill 只做编排**:热点扫描 + 五重过滤 + 流程串联。文风、去 AI 味、配图、发布都调用下面列出的已有系统,严禁在本 skill 里重新发明这些环节。

## 依赖的已有系统(糊在流水线上)

| 环节 | 调用什么 | 位置 |
|---|---|---|
| 文风(所有写作) | 写作系统三件套 + 镇库范文 | `~/.agent-harness/writing/writing-style*.md` |
| 开头诊断 | `dbs-hook` | 已装 skill |
| 发布前共鸣诊断 | `dbs-resonate` | 已装 skill |
| 去 AI 味 | `de-ai-flavor`(观点文走 A-E) | 已装 skill |
| 正文配图 | `ian-xiaohei-illustrations`(观点/隐喻)、`guizang-material-illustration`(机制/数据图) | 已装 skill |
| 封面 | `cover-image` | 已装 skill |
| 发布 | 同仓 `x-post`(dry-run + 确认) | 同仓 skill |

## 账号定位(过滤热点的基准,可被用户运营手册覆盖)

用户 @Charles77xixi 的稀缺交叉地带:**真写代码、真用 Agent、真拿钱在市场交过学费**。三个反复问题(选题只服务这三条):AI 真落地、钱真打理、路真自己选。不做纯 AI 工具搬运、纯新闻评论、MBTI/情绪流水账(历史数据验证这些 0 涨粉)。若用户运营目录有 `账号运营手册.md`/`选题库.md`,以其为准。

## 工作流程

### 第 1 步:扫热点

按账号定位分领域扫,来源:

```bash
python3 <skill目录>/scripts/scan_hotspots.py --topics ai,investing,career
```

脚本用给定关键词生成一批 WebSearch/WebFetch 查询建议(HN、各大 AI 厂商发布、GitHub Trending、财经要闻)。agent 拿建议后**实际执行 WebSearch/WebFetch** 抓当天热点。可选:配了 cookie(`X_AUTH_TOKEN`/`X_CT0`)时,用同仓 `x-content-review/scripts/fetch_x_pulse.py --user <对标账号> --profile` 看对标账号最近在讲什么。

也支持用户直接丢链接/截图进来,跳过扫描。

### 第 2 步:五重过滤(排掉不值得做的)

对每个候选热点过五关,任一不过就淘汰:

1. **相关性**:落在三个反复问题(AI 落地/钱/路)里吗?蹭不上定位的再热也不做。
2. **稀缺角度**:用户有没有别人没有的一手视角(真实代码/真实持仓/真实踩坑)?只有转述没有增量 → 淘汰(历史数据:纯新闻评论 0 涨粉)。
3. **时效**:热点还在窗口内吗?过气的不做。
4. **信任增益**:发出来能不能让人更信用户(露出判断/证据)?纯蹭流量不增信 → 降级。
5. **可持续**:能不能接到已有系列、沉淀成资产?一次性消耗 → 降级。

输出候选热点表:热点 + 过滤结论 + 推荐做/不做。

### 第 3 步:出角度和结构提纲,等用户拍板(硬性分步)

按全局写作规范三步走的第一步:给 2-3 个角度选项 + 每个的编号结构提纲。**停下等用户选**,不直接铺全文(除非用户说「直接出全文」)。

### 第 4 步:写开头段落做风格校准,等用户反馈

先读写作系统三件套,按用户文风写开头段(具体场景/一笔账/一次真实取舍切入,绝不抽象开场)。用 `dbs-hook` 自检开头。**停下等用户反馈**。

### 第 5 步:铺全文

按镇库范文的编号说理骨架铺全文(短推是压缩版):具体开场 + 反共识判断 + emoji 编号观点 + 每节落判断 + 极致具体 + 坦诚暴露。守写作系统硬禁忌(不用引号强调、不用破折号、连接词胶水≤1、结尾不用反问钩子)。

### 第 6 步:去 AI 味

走 `de-ai-flavor`(观点文按 A-E 五条强制动作)。这一步不可省——热点稿最容易带 AI 味。

### 第 7 步:配图(可选,用户要就做)

- 观点/隐喻类插图 → `ian-xiaohei-illustrations`
- 机制/概念拆解/数据图 → `guizang-material-illustration`
- 需要封面(thread 首图)→ `cover-image`(文案走好奇/共鸣钩子,不塞关键词)

### 第 8 步:落盘草稿

产物落 `30-outputs/tweets/`,命名 `热点推文-<主题>-YYYY-MM-DD.md`,标注「草稿,待用户改后手动发」。**默认到此为止**(遵守用户「不代替发 X」规则)。

### 第 9 步:发布(仅当用户明确说发)

用户明确要发时,交给同仓 `x-post`:dry-run 预览 → 用户确认 → 发布。含链接帖提醒 $0.20 溢价。

## 判断规则(硬口径)

- 只做编排,不重造文风/去 AI 味/配图逻辑,一律调已有系统。
- 三步分步(提纲→开头→全文)是硬性的,用户没说「直接出全文」就不能跳。
- 落盘即止,不主动发布;发布只走 x-post 且需用户明确确认。
- 五重过滤宁缺毋滥:一天没有值得做的热点,就如实说「今天没有值得蹭的」,不硬凑。
- 所有产物是初稿,用户会自己改最终版。
