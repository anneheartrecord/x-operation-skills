---
name: cover-image
description: Use when the user asks to make/generate/add a cover image (封面图/题图/banner/X Article 头图) for an article, blog post, xiaohongshu/wechat post, tweet thread, or long-form essay. Nine content-mapped visual themes (lab / thesis / archi / ledger / howto / people / essay / translate / plain), each with its own layout skeleton, palette and typography — not colour variants of one template. Three canvas presets (X Article banner / 16:9 / 3:4). Cover copy is written FOR HUMANS (curiosity/resonance hook, CTR), never for search keywords — titles handle search. Nine themes render deterministic cover PNGs from system fonts (no AI image model, no network); two extra generative themes (doodle hand-drawn map / black-yellow brush poster) call gpt-image-2 via gen-cover-ai.mjs and embeds it at the top of the doc by default.
---

# 封面图生成（cover-image）

## 第一性原则（骨架，先于一切排版）

> **封面是给人看的，标题大部分是给机器看的。**

- 瀑布流里人的第一视觉落在面积最大的封面图上，封面文案决定 CTR。封面文案**只对人**：要抓睛、接地气，路线只有两条——**引发好奇**或**产生共鸣**。
- 标题的首要任务是**搜索索引**：在表达清楚的前提下覆盖尽可能多的核心关键搜索词、承接用户会输入的长尾问题。爆款常常是「封面抓人 + 标题读起来奇奇怪怪」。
- **本 skill 只负责封面这一半**。绝不往封面文案里堆关键词；标题那一半交给 `xhs-title` / `dbs-xhs-title`（起标题）和 `xhs-keyword-strategy`（关键词覆盖）。用户要「标题+封面」整套时，两条线分开做：封面走情绪，标题走搜索。

## 封面文案怎么写（核心工序）

封面上最大的那行是**钩子（hook）**，不是文章标题。原标题降级为 `--subtitle`，或干脆交给标题线去做关键词版。

1. **从原文挖真实的观点/金句**，不凭空造、不标题党到失真。
2. 每个钩子明确走一条路线并标注：
   - **好奇路线**：反常识、留悬念、直接抛扎眼结论。
   - **共鸣路线**：说出目标读者心里那句没说出口的话，越口语越好。
3. **接地气**：口语、短句、具体名词；书面语和抽象大词一律毙掉。
4. 形式约束：用 `|` 分两行，用 `*词*` 高亮 2-3 个最扎眼的字。每行字数上限**按主题不同**（见下方各主题的字数上限表），`thesis` 最少、`howto` / `translate` 能多一点。
5. **默认给 4-6 个候选（好奇、共鸣两条路线各 2-3 个），标明路线，让用户挑**，再定稿渲染。
6. 自检：把候选放进想象中的瀑布流——旁边全是别人的封面，这句话能不能让手停下来？不能就重写。

## 八套主题（v3，2026-07-29 用户确认定稿）

设计原则：**八套在五个轴上同时不同**（底色明暗 / 字体路线 / 版式结构 / 色彩体系 / 有无插画），并排看不像一家人。这是 v3 相对 v2 的核心改动——v2 那五套只换强调色和右侧小插画，本质是一个家族的五个变体，用户判定「太类似」。

| `--style` | 主题 | 适用内容 | 底色 | 字体 | 版式（layout） | 色彩 | 插画 |
|---|---|---|---|---|---|---|---|
| `lab` | 工程实测 | Q1 一手实测、工具、开源项目、Claude Code 工作流 | 冷白 `#fafbfc` + **蓝图双层网格** | 等宽大写标签 + 粗黑 | `sideArt` 左文右图 | 电光蓝 `#1f6feb` | 等轴测卡片堆 + 放射连线 |
| `thesis` | 判断帖 | Q1/Q3 反共识判断、机制分析 | **深墨黑 `#16181c`（唯一深色）** | **反白超粗**，字号最大 | `fullType` 全幅大字 | 亮黄 `#f5d90a` | **无**，右下角巨大引号 |
| `archi` | 架构分层 | Q1 记忆架构、知识库、分层体系、仓位结构 | 暖灰 `#eeebe3` + 纸纹 | 粗黑 | `sideArt` 左文右堆叠 | 正红 `#cf2130` | 四层材质板 + 串联球 |
| `ledger` | 钱与账本 | Q2 真实账户复盘、数据帖、账本型内容 | **账簿米黄 `#f7f2e4` + 横线格 + 左侧红装订边** | **衬线大数字**主角 | `bigNum` 左文右满版数字 | **墨绿 `#1f5c46` + 赭红 `#b03a2e` 涨跌双色** | 折线（退成上方淡水印） |
| `howto` | 开户教程 | Q2 开户 / 出入金 / affiliate how-to | **纯白 `#ffffff`（唯一）** | 粗黑 + 等宽编号 | `stepCards` 上标题下卡片条 | 单蓝 `#0b6bcb` | 步骤卡本身 |
| `people` | 人物点名 | curation 点名推荐帖（471/万，全账号最高转化机制） | 暖砂 `#f2e9dc` + 纸纹 | **宋体** | `avatars` 左文右圆形阵列 | **暖多色六色轮（唯一多色）** | 圆形头像格 |
| `essay` | 随笔 | 生活、离职、认知、两性（不追数据） | 宣纸 `#f6f2e9` + 纸纹 | **宋体大字** | `whitespace` 大留白 | 单赭 `#b0533a` | 右侧竖向墨带 + 一枚印 |
| `translate` | 译写 | Learn in public 译写档（每周 ≤1，必须叠自己的实践层） | 冷灰白 `#f4f5f6` | 衬线引文 + 黑体标题 | **`quoteBlock` 上下分栏（唯一）** | 灰 + 橙 `#e07a3f` | 右侧三段式文本块 |
| `plain` | 极简居中 | 只想要一行标题的极简头图（用户 2026-08-03 指定，参考 Phil Chen 的 X Article 头图） | 灰 `#d9d9d7` + **重胶片颗粒** | 粗黑，字距收紧 | **`centered` 整幅居中（唯一）** | **无强调色**（纯墨黑单色） | **无**，右下角八角星 + 小字标记 |

**选主题的判断顺序**（按内容，不按好看）：

1. 讲**机制 / 一手实测 / 工具** → `lab`
2. 是**反共识判断帖**，靠一句锋利的话立住 → `thesis`
3. 讲**分层结构 / 架构** → `archi`
4. 有**真实数字 / 账本 / 复盘** → `ledger`
5. 是**步骤型 how-to**（开户、出入金、配置流程）→ `howto`
6. 是**点名推荐一批人** → `people`
7. 是**人格 / 感悟 / 生活** → `essay`
8. 是**译写**（有原文引文 + 自己的判断层）→ `translate`
9. 用户**明确说要极简 / 只要一行标题 / 不要那些花活** → `plain`

拿不准就在 `lab` 和 `archi` 之间选，这两套最通用。

**`plain` 的特殊约定**：这一套不套「钩子 + 副标题」的堆叠，居中那一行**直接放文章标题**（或标题的短版），因为极简风的信息密度就该只有一层。不给 `--eyebrow`，`--subtitle` 可选但通常留空。右下角用 `--mark` 放一个 wordmark（如 `CHARLES`）。

**各主题的 hook 每行字数上限**（`article` 画幅，超了会溢出撞母题，`.hook .line` 是 `nowrap` 不会自动折行）：

| 主题 | 字号 | 每行上限 |
|---|---:|---:|
| `thesis` | 70px | ~8 字 |
| `essay` | 56px | ~10 字 |
| `lab` / `archi` | 54px | ~11 字 |
| `ledger` / `people` | 48px | ~12 字 |
| `howto` / `translate` | 42px | ~14 字 |
| `plain` | 62px | ~11 字（居中，两侧留白吃得多，别顶格） |

> `plain` 的字号和右下角标记跟**画布宽度**挂钩（`uc = width / 1012`），不跟高度。其余八套跟高度（`u = height / 386`）。原因：居中版式的横向留白由宽度决定，用高度派生的单位会让 16:9 的字被放大到撑满（`article` 高瘦、`wide` 高胖，同一个 `u` 差 2.3 倍）。改这套的尺寸时别退回 `u`。

## 两套生成式主题（v4，2026-09-08 新增，走文生图模型）

上面九套是 CSS 确定性渲染；下面两套的核心是**手绘 / 笔刷质感 + 场景插画**，CSS 画不出来，改走 `gen-cover-ai.mjs`（本目录），调 gpt-image-2（配置复用 `~/.config/xhs-cover/config.json`，中转站同一把 key）。产物同样是 X Article 头图 PNG，落盘与嵌入约定和九套一致。**只有这两套是本 skill 的「用 AI 模型」例外。**

| `--style` | 主题 | 适用内容 | 视觉 DNA | 参考 |
|---|---|---|---|---|
| `doodle` | 手绘涂鸦解释图 | 讲机制 / 路径 / 分层的帖子，想要「聪明人在白纸上画给你看」的亲近感；Q1 机制帖、Q2 路线图、认知类都能用 | 米白底，马克笔 + 蜡笔手绘，黑线稿 + 绿 / 蓝 / 橘红涂色；大字手写中文标题占上部，重点词蓝色下划线或圈注；下部一个场景（常见结构：左边一个人物 + 右边一张牛皮纸寻宝地图 / 流程路径） | 「为什么你发了那么多内容，还是没客人？因为你没画过这张图」 |
| `poster` | 黑黄笔刷流程海报 | 「我搭了一条 XX 流水线」「我用 A + B + C 做了 D」这类工具链 / 系统搭建帖，要有工程感和交付感 | 米白纸底 + 边缘墨迹，超粗黑体标题左侧堆叠，关键词压在亮黄或黑色笔刷条上；右侧 3-5 步编号流程，每步一个黄圆图标 + 一块 mock UI 面板；底部黑条放 2-4 个「图标 + 短语」 | 「我用 Codex、飞书多维表格和 TikHub，搭了一条从搜索词到内容发布的小红书内容获客流水线」 |

**选哪套**：讲「为什么 / 机制 / 路」用 `doodle`；讲「我怎么搭的 / 工具链 / 步骤」用 `poster`。两套都能替代九套里的 `lab` / `archi` / `howto`，区别是这两套更「像人做的」、更适合想拿转发的重头帖；日常短推仍用九套（免费、秒出、风格稳定）。

```bash
node ~/.agent-harness/skills/cover-image/gen-cover-ai.mjs --style doodle \
  --hook "为什么你的 Agent 越用越笨？|因为你没给它搭*这一层*" \
  --scene "左侧：一个穿绿毛衣的程序员坐在笔记本前抓头，周围飘着聊天气泡「上次说过了」「再讲一遍」「忘了」；右侧：一张手绘牛皮纸地图" \
  --steps "会话,项目,长期,元记忆" --out "/绝对路径/xxx-cover.png"

node ~/.agent-harness/skills/cover-image/gen-cover-ai.mjs --style poster \
  --hook "我用 Claude Code 和一个本地知识库，|搭了一条从热点到发布的|X 内容生产流水线" \
  --steps "热点扫描,五重过滤,写稿去 AI 味,发帖闸,看板复盘" \
  --footer "每天 09:30 自动跑,32 条候选筛出 4 条,不写推文只给判断,附完整教程" --out "/绝对路径/xxx-cover.png"
```

参数：`--hook`（必填，`|` 分行；`doodle` 里 `*词*` = 蓝色圈注）、`--scene`（`doodle` 必填，用中文把画面说具体：左边谁在干什么、右边是什么、气泡里写什么）、`--steps`（3-5 个节点，逗号分隔）、`--subtitle`、`--footer`（仅 `poster`）、`--ratio article|wide`、`--count 1-3`（多张候选）、`--dry-run`（只看提示词）、`--model`（强制换模型）。

**已知边界与坑（实测 2026-09-08）**：

- **只用 gpt-image-2**。gemini-2.5-flash-image 出的中文成片错字，脚本默认不退到它；配置里的 gemini-3.1-flash-image 当天中转站上游 500。gpt-image-2 偶发失败，脚本自动重试 3 次。
- **模型最宽只出 3:2，裁到 2.6:1 要丢约 40% 高度**。脚本从内容顶端锚定裁（保标题，舍底部）；模型会无视「上下留空带」的指令铺满画布，所以别指望靠提示词解决。**`--scene` 里把重要东西放在中上部，底部只放次要物**（桌面、纸张、脚）。`doodle` 的流程节点标签若写在图标下方容易被裁到，`--scene` 里可以点明「节点名写在图标上方」。
- **每张约 1-2 分钟、按张计费**，先 `--dry-run` 看提示词再跑，默认 `--count 1`，满意再要候选。
- mock UI 面板里的小字会有错字，是设计上的「示意面板」不是截图，可接受；标题和步骤名必须逐字核对，错一个字重跑。
- 生成后同样**必须 Read 目视验收**：标题是否完整、重点词圈注是否落对、步骤顺序是否对、裁切有没有切掉关键物。

## 三种画幅

| `--ratio` | 尺寸 | 用途 |
|---|---|---|
| `article`（默认）| 1012×386（2.62:1）| **X Article 头图**、推文长文题图 |
| `wide` | 1600×900（16:9）| 博客、公众号、个人站 |
| `xhs` | 1080×1440（3:4）| 小红书竖版；**自动切成上下堆叠版式** |

版式在 `宽/高 < 1.6` 时自动切竖版，所以 `xhs` 不需要额外参数；竖版下字号整体放大、右侧母题移到下方。也可以 `--width/--height` 手动覆盖，`--scale` 改输出倍率（默认 2x）。

## 用法

```bash
node ~/.agent-harness/skills/cover-image/render-cover.mjs \
  --style archi --ratio article \
  --eyebrow "为你的 Agent" \
  --hook "配置更好的|*记忆架构*" \
  --subtitle "从四层模型到本地落盘" \
  --tags "会话层/Session,项目层/Project,长期层/Long-term,元记忆/Meta" \
  --stamp "本地优先|隐私可控" \
  --out "/绝对路径/agent记忆架构-cover.png"
```

**通用参数**

- `--hook` **必填**：封面主角钩子。`|` 分行，`*词*` 染强调色。
- `--out` **必填**：输出 PNG 绝对路径。
- `--style` 八选一，省略默认 `lab`。`--ratio` 三选一，省略默认 `article`。
- `--eyebrow` 标题上方引导行。`lab` 下自动渲染成等宽大写 + 强调色。
- `--subtitle` 标题下方副标题一行，通常放文章真实标题。
- `--badge` 左上角带框角标（`lab` 下自动变成等宽 + 蓝框）。旧参数 `--kicker` 等价。
- `--scale` 输出倍率，默认 2。

**主题专属参数**（用在别的主题上位置没调过，会压母题）

| 参数 | 专属主题 | 作用 |
|---|---|---|
| `--tags "中文/English,..."` | `archi` `ledger` | 底部编号标签条，最多 4 项，斜杠后半渲染成小字第二行 |
| `--tags "中文/English,..."` | `howto` | **同一个参数在 `howto` 里当步骤卡渲染**（横排卡片，不是底部标签条） |
| `--stamp "第一行\|第二行"` | `archi` | 右下角红框印章 |
| `--bignum "12%"` | `ledger` | 右侧衬线大数字，这套风格的 signature |
| `--names "@a,@b,..."` | `people` | 圆形头像格，最多 6 个，取 @ 后前两位字母 |
| `--quote` + `--source` | `translate` | 上方引文块（原文）+ 出处 |
| `--mark "CHARLES"` | `plain` | 右下角八角星 + 大写小字 wordmark |

不传参数跑一次会打印完整帮助 + 八套主题的适用说明。

## 渲染管线

`HTML/内联CSS/SVG → 本机 Chrome headless 截图 → PNG`。只用系统字体（PingFang SC / Songti SC / Hiragino Sans GB / SF Mono），不联网、不用文生图模型，确定性、免费、风格一致。核心工具：`render-cover.mjs`（本目录）。

中文系统字体最粗只到 PingFang Semibold（600），达不到参考图里那种超粗黑的重量感，脚本用 `-webkit-text-stroke` 极细描边补足；`thesis` 的描边最重（0.03em），宋体路线（`people` / `essay`）不描边。

历史版本备份在同目录：`render-cover.v1-dark.mjs.bak`（v1 近黑底宋体单一样式）。兼容映射：v1 的 `--theme tech|invest|life|curation` 和 v2 的 `--style grid|editorial|launch|concrete|ink` 都会自动映射到 v3 主题，老命令不会挂。

## 默认约定

- 生成后默认把封面图嵌到文章最上面：无 frontmatter 放第一行（H1 之前）；有 YAML frontmatter 放在 frontmatter 之后、H1 之前。用相对路径嵌入：`![封面：<钩子>](<文件名>.png)`。
- 封面 PNG 与文章 `.md` 同目录，命名 `<短名>-cover.png`。
- 生成后**务必用 Read 打开 PNG 目视检查**再嵌入：钩子有没有截断、有没有撞上右侧母题、高亮对不对、主题专属参数有没有用错主题。宽幅 `article` 画幅尤其要检查标题是否溢出左侧文字区。

## Common Mistakes

- **往封面文案里塞搜索关键词** → 违反第一性原则。关键词是标题的活，封面只管情绪。
- **把文章原标题直接当封面正文** → 封面正文必须是钩子，原标题放 `--subtitle` 或交给标题线。
- 钩子书面语、抽象大词（「浅谈」「思考」「方法论」）→ 不接地气，人不会停，重写。
- **钩子每行超字数上限** → 撞右侧母题或溢出画布。按上面那张字数表分行，`thesis` 只有 ~8 字的余量。
- **按好看选主题而不是按内容选** → 随笔套 `ledger`、评测套 `essay` 都会显得莫名其妙。走上面那个判断顺序。
- **主题专属参数用错主题**（`--bignum` 给 `lab`、`--stamp` 给 `essay`）→ 位置和透明度只为对应主题调过，别的主题会压母题或飘在空处。
- `--tags` 在 `howto` 里是**步骤卡**不是标签条，写的时候按步骤顺序写（开户 → 养卡 → 入金 → 出金），别写成并列标签。
- 把图嵌到 YAML frontmatter 之前 → 破坏 frontmatter。
- 用绝对系统路径嵌入 → 换机失效，用同目录相对文件名。
- 生成后不看图直接嵌 → 一定先 Read 目视验收。

## 扩展与调试

**加新主题**：在 `render-cover.mjs` 的 `STYLES` 里加一项（`bg` / `ink` / `accent` / `accent2?` / `texture` / `family` / `layout` / `art` / `use`）。如果复用现有 `layout` 就不用改 `renderBody`；要新版式骨架则在 `renderBody` 里加分支，并在 CSS 段加对应的 `.cover.<layout>` 规则。

**加新母题**：在 `artSvg()` 里加分支，统一画在 `400×300` 的 viewBox 里（外层按 `meet` 缩放，三种画幅都不变形）。`essay` 的墨迹是例外，它用 `300×400` 竖向 viewBox 并走 `.wash` 类贴右侧。

**加新纹理**：在 `textureLayer()` 里加分支。现有四种：`blueprint`（双层网格）、`ruled`（账簿横线 + 装订边）、`paper`（feTurbulence 噪点）、`none`。

**版式定位的坑**：绝对定位在这套 flex 布局里容易失控（`ledger` 第一版的大数字就掉到了画面底边）。**新版式优先用 flex 竖向流 + `flex: 0 0 auto` 控制顺序和尺寸**，只有确实要脱离文档流的装饰件（`translate` 的三段式母题、`archi` 的印章、底部标签条）才用绝对定位。
