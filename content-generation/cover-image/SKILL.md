---
name: cover-image
description: Use when the user asks to make/generate/add a cover image (封面图/题图/banner) for an article, blog post, xiaohongshu/wechat post, tweet thread, or long-form essay. Cover copy is written FOR HUMANS (curiosity/resonance hook, CTR), never for search keywords — titles handle search. Renders a deterministic cover PNG from system fonts (no AI image model, no network) and embeds it at the top of the doc by default.
---

# 封面图生成（cover-image）

## 第一性原则（骨架，先于一切排版）

> **封面是给人看的，标题大部分是给机器看的。**

- 瀑布流里人的第一视觉落在面积最大的封面图上，封面文案决定 CTR。封面文案**只对人**：要抓睛、接地气，路线只有两条——**引发好奇**或**产生共鸣**。
- 标题的首要任务是**搜索索引**：在表达清楚的前提下覆盖尽可能多的核心关键搜索词、承接用户会输入的长尾问题（如「苹果手机如何设置捷径？」）。爆款常常是「封面抓人 + 标题读起来奇奇怪怪」，如「小学单词速记！单词脑图助记600词」——覆盖了【小学单词】【单词速记】【单词脑图】【助记】等一串搜索词。
- **本 skill 只负责封面这一半**。绝不往封面文案里堆关键词；标题那一半交给 `xhs-title` / `dbs-xhs-title`（起标题）和 `xhs-keyword-strategy`（关键词覆盖）。用户要「标题+封面」整套时，两条线分开做：封面走情绪，标题走搜索。

## 封面文案怎么写（核心工序）

封面上最大的那行是**钩子（hook）**，不是文章标题。原标题降级为下方小字（`--subtitle`）或干脆交给标题线去做关键词版。

1. **从原文挖真实的观点/金句**，不凭空造、不标题党到失真。
2. 每个钩子明确走一条路线并标注：
   - **好奇路线**：反常识、留悬念、直接抛扎眼结论（「一夫一妻，本就是反人性的」「去人才高地竞争，到人才洼地赚钱」）。
   - **共鸣路线**：说出目标读者心里那句没说出口的话，越口语越好（「不怕黑子，就怕没黑子」）。
3. **接地气**：口语、短句、具体名词；书面语和抽象大词一律毙掉。
4. 形式约束：整句 ≤ ~14 字，用 `|` 分两行、每行 ≤ ~7 字；用 `*词*` 高亮 2-3 个最扎眼的字。
5. **默认给 4-6 个候选（好奇、共鸣两条路线各 2-3 个），标明路线，让用户挑**，再定稿渲染。
6. 自检：把候选放进想象中的瀑布流——旁边全是别人的封面，这句话能不能让手停下来？不能就重写。

## 渲染管线

`HTML/内联CSS/SVG → 本机 Chrome headless 截图 → PNG`，只用系统字体（Songti SC / Kaiti SC / Heiti SC），不联网、不用文生图模型，确定性、免费、风格一致。核心工具：`render-cover.mjs`（本目录）。

```bash
node ~/.agent-harness/skills/cover-image/render-cover.mjs \
  --theme life \
  --kicker "随笔 · 两性" \
  --hook "一夫一妻|本就是*反人性*的" \
  --subtitle "我对两性的理解" \
  --out "/绝对路径/我对两性的理解-cover.png"
```

- `--hook` 必填：封面主角钩子，`|` 分行、`*词*` 高亮。
- `--subtitle` 文章真实标题（渲染成「本文 · <标题>」小字），可省略。
- `--kicker` 左上栏目标签、`--byline` 左下中性描述、`--brand` 右下角标，均可省略。
- `--theme` = `invest` | `tech` | `life`（省略默认 life）；`--out` 必填绝对路径。
- 尺寸：默认 16:9（1600×900，输出 2x=3200×1800），适合博客/公众号/推文。小红书竖版可试 `--width 1080 --height 1440`（3:4），但排版按 16:9 调的，**竖版渲染后必须目视检查**字号和母题是否失衡。

## 三类主题（按文章内容选 theme）

共用近黑底 + 宋体标题骨架，靠强调色 + 母题区分：

| theme | 适用内容 | 强调色 | 母题 |
|---|---|---|---|
| `invest` | 投资 · 商业 · 财富：简单致富、ETF、港卡/券商、止盈、生意/赚钱方法论 | 琥珀金 `#d4a24e` | 底部 K 线 + 趋势线 |
| `tech` | AI 与工程：Agent、Claude Code、K8S、Go、译文、AI 工作流 | 墨青 `#5b8fb0` | 节点连线 + 细网格 + 等宽 kicker |
| `life` | 人生与思考：两性、离职、职业感悟、注意力、认知/随笔 | 赭红 `#c2724a` | 毛笔横扫 |

他山之石/转载/翻译的稿子没有独立主题：按内容实际主题归进上面三类，且**不署来源**（用户会自己重写后再发）。`--byline` 只放非归属性中性描述（如「个人长文」）。

## 默认约定

- 生成后默认把封面图嵌到文章最上面：无 frontmatter 放第一行（H1 之前）；有 YAML frontmatter 放在 frontmatter 之后、H1 之前。用相对路径嵌入：`![封面：<钩子>](<文件名>.png)`。
- 封面 PNG 与文章 `.md` 同目录，命名 `<短名>-cover.png`。
- 生成后**务必用 Read 打开 PNG 目视检查**（钩子有没有截断、母题有没有压住字、高亮对不对），再嵌入文章。

## Common Mistakes

- **往封面文案里塞搜索关键词** → 违反第一性原则。关键词是标题的活，封面只管情绪。
- **把文章原标题直接当封面正文** → 封面正文必须是钩子，原标题放 `--subtitle` 或交给标题线。
- 钩子书面语、抽象大词（「浅谈」「思考」「方法论」）→ 不接地气，人不会停，重写。
- 钩子不分行导致溢出 → 用 `|` 分两行，每行 ≤ ~7 字。
- 把图嵌到 YAML frontmatter 之前 → 破坏 frontmatter。
- 用绝对系统路径嵌入 → 换机失效，用同目录相对文件名。
- 生成后不看图直接嵌 → 一定先 Read 目视验收。

## 扩展新主题

在 `render-cover.mjs` 的 `THEMES` 里加一项（accent/glow/tint），并在 `motifSvg()` 里加母题分支，其余骨架复用。
