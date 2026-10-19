#!/usr/bin/env node
/**
 * render-cover.mjs — 把一篇文章的元信息渲染成一张编辑风封面图 PNG。
 *
 * 管线：本脚本用参数拼出一段自包含 HTML（内联 CSS + SVG），写到临时文件，再用本机
 * Chrome 的 headless 截图能力渲染成 PNG。全程无需联网、无文生图模型，只用系统字体
 * （PingFang SC / Songti SC / Hiragino Sans GB / SF Mono），因此风格永远一致、可复现。
 *
 * v3（2026-07-29）：从「1 套版式 × 5 个配色」改成「7 套版式模板 × 8 套主题」。
 * v2 只换强调色和右侧小插画，八张并排看像同一家人；v3 让每套主题在五个轴上同时不同：
 * 底色明暗、字体路线、版式结构、色彩体系、有无插画。旧版备份见同目录 .bak 文件。
 *
 * 用法：
 *   node render-cover.mjs --style ledger --ratio article \
 *     --hook "公积金 5% 提到 12%|到手*怎么变*" --bignum "12%" \
 *     --subtitle "一增一降之后，到手为什么接近税前" \
 *     --out "/abs/path/xxx-cover.png"
 *
 * 八套主题（--style）：
 *   lab        工程实测    冷白+蓝图网格 · 等宽标签 · 左文右图   · 电光蓝     · 等轴测线稿
 *   thesis     判断帖      深墨黑       · 反白超粗 · 全幅大字   · 亮黄       · 无插画
 *   archi      架构分层    暖灰纸纹     · 粗黑     · 左文右堆叠 · 正红       · 材质分层块
 *   ledger     钱与账本    账簿纸+横线格 · 衬线数字 · 满版大数字 · 墨绿/赭红  · 折线
 *   howto      开户教程    纯白         · 粗黑     · 卡片分栏   · 单蓝       · 步骤卡
 *   people     人物点名    暖砂         · 宋体     · 头像阵列   · 暖多色     · 圆形格
 *   essay      随笔        宣纸         · 宋体大字 · 大留白     · 单赭       · 墨与印
 *   translate  译写        冷灰白       · 衬线引文 · 上下分栏   · 灰+橙      · 引文块
 *
 * 三种画幅（--ratio）：article 1012×386（X Article，默认）| wide 1600×900 | xhs 1080×1440
 */

import { writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";

/** 解析 --key value 形式的命令行参数为对象。 */
function parseArgs(argv) {
  const parsed = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token.startsWith("--")) {
      const key = token.slice(2);
      const next = argv[index + 1];
      if (next === undefined || next.startsWith("--")) parsed[key] = true;
      else { parsed[key] = next; index += 1; }
    }
  }
  return parsed;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/** 先转义，再把 *词* 换成强调色 span。顺序很重要，否则 span 自己会被转义。 */
function inlineEm(text) {
  return escapeHtml(text).replace(/\*([^*]+)\*/g, '<span class="em">$1</span>');
}

/** 把 "a,b,c" 拆成数组，去空、限长。 */
function splitList(raw, max) {
  return String(raw || "").split(",").map((x) => x.trim()).filter(Boolean).slice(0, max);
}

const SANS = '"PingFang SC", "Hiragino Sans GB", "STHeiti", -apple-system, sans-serif';
const SERIF = '"Songti SC", "STSong", "Hiragino Mincho ProN", serif';
const MONO = '"SF Mono", "Menlo", "Monaco", monospace';

const RATIOS = {
  article: { width: 1012, height: 386 },
  wide: { width: 1600, height: 900 },
  xhs: { width: 1080, height: 1440 },
};

/**
 * 八套主题。layout 决定版式骨架（见 renderBody），其余字段决定色彩与字体路线。
 *   bg/ink/accent  底色 / 主字色 / 强调色
 *   accent2        第二强调色（只有 ledger 用，做涨跌双色）
 *   texture        blueprint（双层蓝图网格）| ruled（账簿横线格）| paper（纸纹）| none
 *   family         标题字体：sans | serif
 *   layout         版式模板名
 */
const STYLES = {
  lab: {
    label: "工程实测", layout: "sideArt",
    bg: "#fafbfc", ink: "#14171a", accent: "#1f6feb",
    texture: "blueprint", family: "sans", monoEyebrow: true, art: "isoStack",
    use: "Q1 一手实测、工具、开源项目、Claude Code 工作流",
  },
  thesis: {
    label: "判断帖", layout: "fullType",
    bg: "#16181c", ink: "#f4f4f0", accent: "#f5d90a",
    texture: "none", family: "sans", heavy: true, art: null,
    use: "Q1/Q3 反共识判断、机制分析（唯一深色反白，字号最大）",
  },
  archi: {
    label: "架构分层", layout: "sideArt",
    bg: "#eeebe3", ink: "#131313", accent: "#cf2130",
    texture: "paper", family: "sans", art: "slabs", tri: true,
    use: "Q1 记忆架构、知识库、分层体系、仓位结构",
  },
  ledger: {
    label: "钱与账本", layout: "bigNum",
    bg: "#f7f2e4", ink: "#1a1a16", accent: "#1f5c46", accent2: "#b03a2e",
    texture: "ruled", family: "sans", numSerif: true, art: "trendline",
    use: "Q2 真实账户复盘、数据帖、账本型内容",
  },
  howto: {
    label: "开户教程", layout: "stepCards",
    bg: "#ffffff", ink: "#101418", accent: "#0b6bcb",
    texture: "none", family: "sans", art: null,
    use: "Q2 开户 / 出入金 / affiliate how-to（唯一纯白）",
  },
  people: {
    label: "人物点名", layout: "avatars",
    bg: "#f2e9dc", ink: "#1d1a15", accent: "#c2622c",
    texture: "paper", family: "serif", art: null,
    use: "curation 点名推荐帖（471/万，全账号最高转化机制）",
  },
  essay: {
    label: "随笔", layout: "whitespace",
    bg: "#f6f2e9", ink: "#1b1a17", accent: "#b0533a",
    texture: "paper", family: "serif", art: "inkSeal",
    use: "生活、离职、认知、两性（大留白，不追数据）",
  },
  translate: {
    label: "译写", layout: "quoteBlock",
    bg: "#f4f5f6", ink: "#16181a", accent: "#e07a3f",
    texture: "none", family: "sans", quoteSerif: true, art: "threeLayer",
    use: "Learn in public 译写档（每周 ≤1，必须叠自己的实践层）",
  },
  plain: {
    label: "极简居中", layout: "centered",
    bg: "#d9d9d7", ink: "#1a1a1a", accent: "#1a1a1a",
    texture: "grain", family: "sans", art: null,
    use: "只想要一行标题的极简头图（重噪点灰底 + 居中大字 + 右下角小标记，无插画无强调色）",
  },
};

/** people 版式里头像圈用的暖色轮，唯一用多色的一套。 */
const WARM_WHEEL = ["#c2622c", "#a8763b", "#8d6a4f", "#b4553f", "#96703a", "#a35c4c"];

const GRAIN =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/></filter><rect width='240' height='240' filter='url(#n)' opacity='0.55'/></svg>`
  );

/**
 * plain 专用的重颗粒。和 GRAIN 的区别：先 feColorMatrix 去饱和成灰度、再拉对比，
 * 让噪点分布在中灰两侧，配 overlay 混合时明暗两个方向都出点，整体明度基本不偏移。
 * 直接复用 GRAIN（半透明黑噪点）在 overlay 下几乎看不见，别再退回去。
 */
const HEAVY_GRAIN =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='hn'>` +
      `<feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/>` +
      `<feColorMatrix type='saturate' values='0'/>` +
      `<feComponentTransfer><feFuncR type='linear' slope='2.2' intercept='-0.6'/>` +
      `<feFuncG type='linear' slope='2.2' intercept='-0.6'/>` +
      `<feFuncB type='linear' slope='2.2' intercept='-0.6'/>` +
      `<feFuncA type='linear' slope='0' intercept='1'/></feComponentTransfer></filter>` +
      `<rect width='200' height='200' filter='url(#hn)'/></svg>`
  );

/** 背景纹理层。四种纹理长相差别很大，是拉开主题差异的第一个轴。 */
function textureLayer(kind, width, height, ink, accent, u) {
  if (kind === "blueprint") {
    // 双层蓝图网格：细格 + 每五格一条深线，只有 lab 用
    return `<svg class="tex" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      <defs>
        <pattern id="mi" width="${20 * u}" height="${20 * u}" patternUnits="userSpaceOnUse">
          <path d="M ${20 * u} 0 L 0 0 0 ${20 * u}" fill="none" stroke="${accent}" stroke-width="1"/>
        </pattern>
        <pattern id="ma" width="${100 * u}" height="${100 * u}" patternUnits="userSpaceOnUse">
          <path d="M ${100 * u} 0 L 0 0 0 ${100 * u}" fill="none" stroke="${accent}" stroke-width="1.4"/>
        </pattern>
      </defs>
      <rect width="${width}" height="${height}" fill="url(#mi)" opacity="0.13"/>
      <rect width="${width}" height="${height}" fill="url(#ma)" opacity="0.2"/>
    </svg>`;
  }
  if (kind === "ruled") {
    // 账簿横线格 + 左侧红色装订边线，只有 ledger 用
    let lines = "";
    for (let y = 0; y <= height; y += 34 * u) {
      lines += `<line x1="0" y1="${y}" x2="${width}" y2="${y}" stroke="${ink}" stroke-width="1"/>`;
    }
    return `<svg class="tex" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      <g opacity="0.09">${lines}</g>
      <line x1="${34 * u}" y1="0" x2="${34 * u}" y2="${height}" stroke="#b03a2e" stroke-width="${1.6 * u}" opacity="0.3"/>
      <line x1="${39 * u}" y1="0" x2="${39 * u}" y2="${height}" stroke="#b03a2e" stroke-width="${1.6 * u}" opacity="0.16"/>
    </svg>`;
  }
  return "";
}

/** 右侧 / 底部母题。统一画在 400×300 viewBox 里，外层按 meet 缩放，三种画幅都不变形。 */
function artSvg(name, accent, accent2, ink) {
  const open = `<svg viewBox="0 0 400 300" preserveAspectRatio="xMidYMid meet" class="art">`;
  const close = `</svg>`;

  if (name === "isoStack") {
    const sats = [
      [40, 62], [40, 152], [58, 240], [152, 34], [152, 262],
      [300, 46], [340, 122], [336, 210], [268, 262],
    ];
    let links = "", boxes = "";
    sats.forEach(([x, y]) => {
      const mx = (x + 26 + 200) / 2;
      links += `<path d="M ${x + 26} ${y + 16} L ${mx} ${y + 16} L ${mx} 150 L 200 150" fill="none" stroke="${ink}" stroke-width="1.5" opacity="0.34"/>`;
      boxes += `<rect x="${x}" y="${y}" width="52" height="34" rx="3" fill="#fff" stroke="${ink}" stroke-width="1.7" opacity="0.92"/>`;
      boxes += `<rect x="${x + 12}" y="${y + 12}" width="28" height="3.2" rx="1.6" fill="${ink}" opacity="0.4"/>`;
      boxes += `<rect x="${x + 12}" y="${y + 20}" width="17" height="3.2" rx="1.6" fill="${ink}" opacity="0.2"/>`;
    });
    const slab = (dy, fill) =>
      `<path d="M 200 ${104 + dy} l 62 26 l -62 26 l -62 -26 z" fill="${fill}" stroke="${ink}" stroke-width="1.7"/>`;
    return `${open}<g>${links}</g><g>${boxes}</g>
      ${slab(46, "#e4e7ea")}${slab(28, "#f0f2f4")}${slab(10, "#fcfdfd")}
      <path d="M 200 137 l 19 13 l -19 13 l -19 -13 z" fill="${accent}"/>${close}`;
  }

  if (name === "slabs") {
    const plate = (y, top, side, ball) => `
      <path d="M 96 ${y} l 108 -34 l 108 34 l -108 34 z" fill="${top}"/>
      <path d="M 96 ${y} l 0 20 l 108 34 l 0 -20 z" fill="${side}"/>
      <path d="M 312 ${y} l 0 20 l -108 34 l 0 -20 z" fill="${side}" opacity="0.82"/>
      <circle cx="204" cy="${y - 34}" r="10" fill="${ball}"/>`;
    return `${open}
      ${plate(268, "#c9241f", "#8d1714", "#e0483f")}
      ${plate(212, "#2b2b2b", "#141414", "#4a4a4a")}
      ${plate(156, "#4f4f4f", "#2c2c2c", "#7d7d7d")}
      ${plate(100, "#dedbd2", "#b3b0a6", "#f2f0ea")}
      <line x1="204" y1="66" x2="204" y2="268" stroke="${ink}" stroke-width="2" opacity="0.26"/>${close}`;
  }

  if (name === "trendline") {
    // 涨跌双色折线 + 柱：绿在上、红在下，账本语义
    return `${open}
      <line x1="24" y1="262" x2="376" y2="262" stroke="${ink}" stroke-width="1.8" opacity="0.3"/>
      <line x1="24" y1="150" x2="376" y2="150" stroke="${ink}" stroke-width="1" opacity="0.16" stroke-dasharray="5 5"/>
      <polyline points="34,224 96,196 158,208 220,142 282,116 344,58" fill="none" stroke="${accent}" stroke-width="3.4"/>
      <polyline points="34,246 96,252 158,238 220,258 282,244 344,254" fill="none" stroke="${accent2}" stroke-width="2.4" opacity="0.75" stroke-dasharray="7 5"/>
      <circle cx="344" cy="58" r="7" fill="${accent}"/>
      <g opacity="0.2">
        <rect x="88" y="196" width="16" height="66" fill="${accent}"/>
        <rect x="212" y="142" width="16" height="120" fill="${accent}"/>
        <rect x="336" y="58" width="16" height="204" fill="${accent}"/>
      </g>${close}`;
  }

  if (name === "threeLayer") {
    // 译写三段式：原文 → 我学到什么 → 我怎么用。第三块染强调色，
    // 对应写作系统的硬规则「没有第三段就不发」。
    const block = (y, w, fill, op) => `
      <rect x="40" y="${y}" width="${w}" height="9" rx="4.5" fill="${fill}" opacity="${op}"/>`;
    const group = (top, fill, op, label) => `
      <rect x="16" y="${top - 14}" width="4" height="70" rx="2" fill="${fill}" opacity="${op}"/>
      ${block(top, 300, fill, op)}
      ${block(top + 20, 246, fill, op * 0.66)}
      ${block(top + 40, 190, fill, op * 0.45)}`;
    return `${open}
      ${group(38, ink, 0.3)}
      ${group(128, ink, 0.42)}
      ${group(218, accent, 0.95)}
    ${close}`;
  }

  if (name === "inkSeal") {
    return `<svg viewBox="0 0 300 400" preserveAspectRatio="xMidYMid slice" class="wash">
      <path d="M 196 -20 C 168 70, 214 150, 186 236 C 166 300, 200 366, 176 420
               L 232 420 C 250 362, 224 296, 242 236 C 266 152, 226 70, 250 -20 Z"
        fill="${accent}" opacity="0.15"/>
      <path d="M 150 12 C 128 96, 168 176, 142 262 C 124 322, 152 372, 136 414"
        fill="none" stroke="${accent}" stroke-width="2" opacity="0.22"/>
      <rect x="58" y="292" width="46" height="46" rx="4" fill="none" stroke="${accent}" stroke-width="2.6" opacity="0.48"/>
      <rect x="70" y="304" width="22" height="22" rx="2" fill="${accent}" opacity="0.36"/>
    </svg>`;
  }
  return "";
}

/**
 * 七套版式骨架。这是 v3 的核心：不同主题走不同 DOM 结构，不只是换色。
 * 每个分支返回 stage 内部的 HTML。
 */
function renderBody(layout, P) {
  const { hookHtml, eyebrowHtml, subtitleHtml, artHtml, tagsHtml, stampHtml,
    bignumHtml, quoteHtml, avatarsHtml, stepsHtml } = P;

  if (layout === "fullType") {
    // 判断帖：全幅大字，无插画，左侧一条强调色粗竖条
    return `<div class="stage full">
      <div class="bar"></div>
      <div class="textpanel">
        ${eyebrowHtml}${hookHtml}${subtitleHtml}
      </div>
    </div>`;
  }

  if (layout === "bigNum") {
    // 钱与账本：左文，右侧上折线水印、下衬线大数字（顺序即视觉顺序，别调换）
    return `<div class="stage">
      <div class="textpanel">${eyebrowHtml}${hookHtml}${subtitleHtml}</div>
      <div class="numpanel">${artHtml}${bignumHtml}</div>
    </div>`;
  }

  if (layout === "stepCards") {
    // 开户教程：上标题，下横排步骤卡片
    return `<div class="stage stack">
      <div class="textpanel">${eyebrowHtml}${hookHtml}${subtitleHtml}</div>
      ${stepsHtml}
    </div>`;
  }

  if (layout === "avatars") {
    // 人物点名：左文，右侧圆形头像阵列
    return `<div class="stage">
      <div class="textpanel">${eyebrowHtml}${hookHtml}${subtitleHtml}</div>
      <div class="avpanel">${avatarsHtml}</div>
    </div>`;
  }

  if (layout === "quoteBlock") {
    // 译写：上引文块，下标题；右侧补一个三段式母题（原文 → 译文 → 我的判断），
    // 既填掉右侧留白，也点出译写档的硬规则「没有第三段就不发」
    return `<div class="stage stack">
      ${quoteHtml}
      <div class="textpanel">${eyebrowHtml}${hookHtml}${subtitleHtml}</div>
      ${artHtml}
    </div>`;
  }

  if (layout === "centered") {
    // 极简：整幅居中一行大字，可选下方一行小副标题；右下角标记由 markHtml 绝对定位
    return `<div class="stage centered">
      <div class="textpanel center">${hookHtml}${subtitleHtml}</div>
    </div>`;
  }

  if (layout === "whitespace") {
    // 随笔：大留白，文字靠左，墨迹在右（墨迹由 wash 层绝对定位，不进 stage）
    return `<div class="stage">
      <div class="textpanel wide">${eyebrowHtml}${hookHtml}${subtitleHtml}</div>
    </div>`;
  }

  // sideArt（lab / archi）：左文右图
  return `<div class="stage">
    <div class="textpanel">${eyebrowHtml}${hookHtml}${subtitleHtml}</div>
    <div class="artpanel">${artHtml}</div>
  </div>`;
}

/** 用参数拼出整页 HTML。 */
function buildHtml(o) {
  const s = STYLES[o.style];
  const { bg, ink, accent } = s;
  const accent2 = s.accent2 || accent;
  const layout = s.layout;
  const { width, height } = o;

  const portrait = width / height < 1.6;
  const u = portrait ? width / 1012 : height / 386;
  // centered 版式的字和角标必须跟「宽度」挂钩：横向留白由宽度决定，
  // 用高度派生的 u 会让 16:9 的字被放大到撑满（article 高瘦、wide 高胖，同一 u 差 2.3 倍）。
  const uc = width / 1012;

  const hookLines = String(o.hook).split("|")
    .map((l) => `<div class="line">${inlineEm(l.trim())}</div>`).join("");
  const hookHtml = `<div class="hook">${hookLines}</div>`;

  const eyebrowHtml = o.eyebrow ? `<div class="eyebrow">${inlineEm(o.eyebrow)}</div>` : "";
  const subtitleHtml = o.subtitle ? `<div class="subtitle">${inlineEm(o.subtitle)}</div>` : "";
  const badgeHtml = o.badge ? `<div class="badge">${escapeHtml(o.badge)}</div>` : "";

  const tagList = splitList(o.tags, 4);
  const tagsHtml = tagList.length && (layout === "sideArt" || layout === "bigNum")
    ? `<div class="tags">${tagList.map((raw, i) => {
        const [main, sub] = raw.split("/");
        return `<div class="tag"><span class="num">0${i + 1}</span><span class="txt">${escapeHtml(main)}${
          sub ? `<em>${escapeHtml(sub)}</em>` : ""}</span></div>`;
      }).join("")}</div>` : "";

  // 步骤卡（howto 专用）：--tags 在这个版式里当步骤用
  const stepsHtml = layout === "stepCards" && tagList.length
    ? `<div class="steps">${tagList.map((raw, i) => {
        const [main, sub] = raw.split("/");
        return `<div class="card"><span class="sn">${String(i + 1).padStart(2, "0")}</span>
          <span class="st">${escapeHtml(main)}</span>
          ${sub ? `<span class="ss">${escapeHtml(sub)}</span>` : ""}</div>`;
      }).join("")}</div>` : "";

  // 头像阵列（people 专用）
  const nameList = splitList(o.names, 6);
  const avatarsHtml = nameList.length
    ? `<div class="avgrid">${nameList.map((n, i) => {
        const label = n.replace(/^@/, "").slice(0, 2).toUpperCase();
        return `<div class="av" style="background:${WARM_WHEEL[i % WARM_WHEEL.length]}">${escapeHtml(label)}</div>`;
      }).join("")}</div>` : "";

  // 引文块（translate 专用）
  const quoteHtml = o.quote
    ? `<div class="quote"><div class="qtext">${inlineEm(o.quote)}</div>${
        o.source ? `<div class="qsrc">${escapeHtml(o.source)}</div>` : ""}</div>`
    : "";

  const bignumHtml = o.bignum ? `<div class="bignum">${escapeHtml(o.bignum)}</div>` : "";
  const stampHtml = o.stamp
    ? `<div class="stamp">${String(o.stamp).split("|").map((l) => `<div>${escapeHtml(l.trim())}</div>`).join("")}</div>`
    : "";

  const art = s.art ? artSvg(s.art, accent, accent2, ink) : "";
  const isWash = s.art === "inkSeal";
  const artHtml = art && !isWash ? `<div class="artpanel-inner">${art}</div>` : "";
  const washHtml = isWash ? art : "";

  const texture = textureLayer(s.texture, width, height, ink, accent, u);
  // paper 是淡纸纹；grain 是 plain 那种明显的胶片颗粒，靠 .grain.heavy 提高不透明度
  const grainHtml = s.texture === "paper" ? `<div class="grain"></div>`
    : s.texture === "grain" ? `<div class="grain heavy"></div>` : "";
  const markHtml = o.mark && layout === "centered"
    ? `<div class="mark"><span class="mk"></span>${escapeHtml(o.mark)}</div>` : "";

  const titleFamily = s.family === "serif" ? SERIF : SANS;
  const titleStroke = s.family === "serif" ? 0 : (s.heavy ? 0.03 : 0.014);
  // 各版式的标题字号不同，这是「版式结构」这个轴的一部分
  const hookSize = {
    fullType: portrait ? 92 : 70, bigNum: portrait ? 70 : 48,
    stepCards: portrait ? 66 : 42, avatars: portrait ? 70 : 48,
    quoteBlock: portrait ? 66 : 42, whitespace: portrait ? 78 : 56,
    sideArt: portrait ? 74 : 54, centered: portrait ? 76 : 62,
  }[layout] * (layout === "centered" ? uc : u);

  const body = renderBody(layout, {
    hookHtml, eyebrowHtml, subtitleHtml, artHtml, tagsHtml, stampHtml,
    bignumHtml, quoteHtml, avatarsHtml, stepsHtml,
  });

  return `<!doctype html><html><head><meta charset="utf-8"><style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { width: ${width}px; height: ${height}px; }
    .cover {
      position: relative; width: ${width}px; height: ${height}px; overflow: hidden;
      background: ${bg}; font-family: ${SANS}; color: ${ink};
    }
    .tex { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
    .grain {
      position: absolute; inset: 0; background-image: url("${GRAIN}");
      background-size: ${260 * u}px ${260 * u}px; opacity: 0.055;
      mix-blend-mode: multiply; pointer-events: none;
    }
    /* plain 的颗粒要看得见：灰度噪点 + overlay，明暗双向出点，明度不偏移 */
    .grain.heavy {
      background-image: url("${HEAVY_GRAIN}");
      background-size: ${120 * u}px ${120 * u}px; opacity: 0.82;
      mix-blend-mode: overlay;
    }
    .wash {
      position: absolute; top: 0; right: 0; height: 100%;
      width: ${portrait ? "100%" : "34%"}; pointer-events: none;
    }
    .stage {
      position: absolute; inset: 0; display: flex; gap: ${24 * u}px;
      flex-direction: ${portrait ? "column" : "row"};
      align-items: ${portrait ? "stretch" : "center"};
      padding: ${portrait ? `${52 * u}px ${46 * u}px` : `${40 * u}px ${52 * u}px`};
    }
    /* stack：上下分栏版式（howto 步骤卡 / translate 引文块），竖直排列且左对齐 */
    .stage.stack { flex-direction: column; align-items: stretch; justify-content: center; }
    .stage.full  { align-items: center; }
    /* centered（极简）：整幅水平垂直居中，忽略 portrait 的列向拉伸 */
    .stage.centered { flex-direction: column; align-items: center; justify-content: center; }
    .textpanel.center { flex: 0 0 auto; align-items: center; text-align: center; }
    .textpanel.center .hook .line { letter-spacing: -0.015em; }
    .textpanel.center .subtitle { text-align: center; }
    .mark {
      position: absolute; right: ${40 * uc}px; bottom: ${28 * uc}px;
      display: flex; align-items: center; gap: ${8 * uc}px;
      font-size: ${17 * uc}px; font-weight: 700; letter-spacing: 0.06em;
      text-transform: uppercase; color: ${ink}; opacity: 0.82;
    }
    .mark .mk {
      width: ${15 * uc}px; height: ${15 * uc}px; background: ${ink};
      clip-path: polygon(50% 0%, 62% 26%, 89% 15%, 82% 43%, 100% 50%, 82% 57%,
        89% 85%, 62% 74%, 50% 100%, 38% 74%, 11% 85%, 18% 57%, 0% 50%, 18% 43%, 11% 15%, 38% 26%);
    }
    .textpanel {
      flex: ${portrait ? "0 0 auto" : "1 1 60%"}; min-width: 0;
      display: flex; flex-direction: column; justify-content: center;
    }
    .stage.stack .textpanel { flex: 0 0 auto; }
    .textpanel.wide { flex: 1 1 66%; }
    .artpanel, .numpanel, .avpanel {
      flex: ${portrait ? "1 1 auto" : "0 0 36%"}; min-width: 0;
      display: flex; align-items: center; justify-content: center; position: relative;
    }
    .artpanel-inner { width: 100%; display: flex; align-items: center; justify-content: center; }
    .art { width: 100%; height: ${portrait ? "100%" : `${262 * u}px`}; }

    .eyebrow {
      font-size: ${19 * u}px; font-weight: 600; letter-spacing: 0.1em;
      opacity: 0.68; margin-bottom: ${13 * u}px;
      ${s.monoEyebrow ? `font-family: ${MONO}; text-transform: uppercase; letter-spacing: 0.14em; color: ${accent}; opacity: 0.9;` : ""}
    }
    .hook {
      font-family: ${titleFamily}; font-weight: ${s.family === "serif" ? 700 : 600};
      font-size: ${hookSize}px; line-height: ${layout === "fullType" ? 1.18 : 1.24};
      letter-spacing: 0.005em; -webkit-text-stroke: ${titleStroke}em ${ink};
    }
    .hook .line { white-space: nowrap; }
    .hook .em { color: ${accent}; -webkit-text-stroke-color: ${accent}; }
    .subtitle {
      margin-top: ${18 * u}px; font-size: ${23 * u}px; font-weight: 500;
      letter-spacing: 0.02em; opacity: 0.62;
    }
    .subtitle .em { color: ${accent}; opacity: 1; }
    .badge {
      position: absolute; left: ${52 * u}px; top: ${26 * u}px;
      font-size: ${16 * u}px; font-weight: 600; letter-spacing: 0.08em;
      padding: ${6 * u}px ${12 * u}px; border: ${1.6 * u}px solid ${ink};
      border-radius: ${3 * u}px; opacity: 0.8;
      ${s.monoEyebrow ? `font-family: ${MONO}; border-color: ${accent}; color: ${accent};` : ""}
    }

    /* fullType（判断帖）：左侧强调色粗竖条 + 右下角超大引号 */
    .bar {
      flex: 0 0 auto; width: ${8 * u}px; height: ${portrait ? "auto" : `${190 * u}px`};
      background: ${accent}; margin-right: ${34 * u}px;
      ${portrait ? `width: 100%; height: ${8 * u}px; margin: 0 0 ${28 * u}px 0;` : ""}
    }
    .cover.fullType::after {
      content: "”"; position: absolute; right: ${30 * u}px; bottom: ${-70 * u}px;
      font-family: ${SERIF}; font-size: ${300 * u}px; color: ${accent};
      opacity: 0.12; line-height: 1; pointer-events: none;
    }

    /* bigNum（钱与账本）：衬线大数字 + 底层折线 */
    /* 大数字是主角，折线退成上方淡水印。用竖向 flex 而不是绝对定位，位置才可控
       （绝对定位那版数字会掉到画面底边） */
    .numpanel {
      flex-direction: column; justify-content: center; gap: ${2 * u}px;
    }
    .numpanel .artpanel-inner { flex: 0 0 auto; width: 100%; }
    .numpanel .art { opacity: 0.3; height: ${118 * u}px; }
    .bignum {
      flex: 0 0 auto;
      font-family: ${s.numSerif ? SERIF : SANS}; font-weight: 700;
      font-size: ${126 * u}px; line-height: 1.02; color: ${accent};
      letter-spacing: -0.02em; white-space: nowrap; text-align: center;
    }

    /* stepCards（开户教程）：横排卡片，纯白底 + 细边 + 轻阴影 */
    .steps { display: flex; gap: ${14 * u}px; margin-top: ${26 * u}px; }
    .card {
      flex: 1 1 0; min-width: 0; background: #fff;
      border: ${1.4 * u}px solid rgba(16,20,24,0.13); border-radius: ${7 * u}px;
      box-shadow: 0 ${3 * u}px ${12 * u}px rgba(16,20,24,0.07);
      padding: ${14 * u}px ${16 * u}px; display: flex; flex-direction: column; gap: ${4 * u}px;
      border-top: ${4 * u}px solid ${accent};
    }
    .card .sn { font-family: ${MONO}; font-size: ${15 * u}px; font-weight: 600; color: ${accent}; }
    .card .st { font-size: ${19 * u}px; font-weight: 600; }
    .card .ss { font-size: ${13 * u}px; font-weight: 500; opacity: 0.5; letter-spacing: 0.04em; }

    /* avatars（人物点名）：圆形阵列，唯一多色 */
    .avgrid {
      display: grid; grid-template-columns: repeat(3, 1fr); gap: ${16 * u}px;
      width: 100%; padding: 0 ${6 * u}px;
    }
    .av {
      aspect-ratio: 1 / 1; border-radius: 50%; display: flex;
      align-items: center; justify-content: center;
      font-family: ${MONO}; font-size: ${24 * u}px; font-weight: 600; color: #fbf6ee;
      box-shadow: 0 ${3 * u}px ${10 * u}px rgba(29,26,21,0.16);
    }

    /* quoteBlock（译写）：上方引文块，左侧粗竖线 */
    .quote {
      border-left: ${5 * u}px solid ${accent}; padding: ${4 * u}px 0 ${4 * u}px ${22 * u}px;
      margin-bottom: ${26 * u}px; max-width: ${portrait ? "100%" : "78%"};
    }
    .qtext {
      font-family: ${s.quoteSerif ? SERIF : SANS}; font-size: ${25 * u}px;
      font-weight: 600; line-height: 1.5; opacity: 0.9;
    }
    .qsrc {
      margin-top: ${9 * u}px; font-size: ${16 * u}px; font-weight: 500;
      letter-spacing: 0.06em; opacity: 0.5;
    }
    .qsrc::before { content: "— "; }
    /* translate 的三段式母题贴右侧，不参与 stack 的竖向流 */
    .cover.quoteBlock .artpanel-inner {
      position: absolute; right: ${44 * u}px; top: 50%;
      transform: translateY(-50%); width: ${portrait ? "60%" : "23%"};
      ${portrait ? `right: auto; left: 50%; transform: translate(-50%, 0); top: auto; bottom: ${40 * u}px;` : ""}
    }
    .cover.quoteBlock .art { height: ${172 * u}px; }

    .tags {
      position: absolute; left: ${52 * u}px; bottom: ${24 * u}px;
      display: flex; gap: ${26 * u}px; align-items: flex-end;
    }
    .tag { display: flex; align-items: center; gap: ${8 * u}px; }
    .tag .num { font-size: ${16 * u}px; font-weight: 600; color: ${accent}; letter-spacing: 0.04em; }
    .tag .txt { font-size: ${17 * u}px; font-weight: 600; opacity: 0.78; line-height: 1.15; }
    .tag .txt em {
      display: block; font-style: normal; font-size: ${12 * u}px;
      font-weight: 500; opacity: 0.5; letter-spacing: 0.06em;
    }
    .stamp {
      position: absolute; right: ${42 * u}px; bottom: ${24 * u}px;
      border: ${2 * u}px solid ${accent}; color: ${accent};
      padding: ${8 * u}px ${12 * u}px; border-radius: ${3 * u}px;
      font-size: ${15 * u}px; font-weight: 600; line-height: 1.38;
      text-align: center; letter-spacing: 0.04em;
    }
  </style></head><body>
    <div class="cover ${layout}">
      ${texture}
      ${washHtml}
      ${grainHtml}
      ${body}
      ${badgeHtml}
      ${tagsHtml}
      ${stampHtml}
      ${markHtml}
    </div>
  </body></html>`;
}

function chromeBinary() {
  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  ];
  for (const path of candidates) {
    try { execFileSync("test", ["-f", path]); return path; } catch { /* next */ }
  }
  throw new Error("找不到 Chrome/Chromium/Edge，无法渲染封面。");
}

/** v1/v2 参数到 v3 主题的兼容映射。 */
const ALIAS = {
  tech: "lab", invest: "ledger", life: "essay", curation: "people",
  grid: "lab", editorial: "translate", launch: "ledger", concrete: "archi", ink: "essay",
};

function usage() {
  console.error("必填：--out <PNG绝对路径> 和 --hook <主标题>（| 分行、*词* 强调）");
  console.error("可选：--ratio article|wide|xhs  --eyebrow --subtitle --badge --scale");
  console.error("      --tags（archi/ledger 标签条；howto 当步骤卡）--stamp（archi）");
  console.error("      --bignum（ledger 大数字）--names（people 头像）--quote --source（translate）");
  console.error("      --mark（plain 右下角小标记，如 CHARLES）");
  console.error("\n九套主题（--style）：");
  for (const [key, v] of Object.entries(STYLES)) {
    console.error(`  ${key.padEnd(10)} ${v.label.padEnd(6)} ${v.use}`);
  }
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const hook = args.hook || args.title;
  let style = args.style || args.theme || "lab";
  if (!STYLES[style] && ALIAS[style]) style = ALIAS[style];

  if (!args.out || !hook) { usage(); process.exit(1); }
  if (!STYLES[style]) {
    console.error(`未知 --style ${style}，可选：${Object.keys(STYLES).join(" | ")}`);
    process.exit(1);
  }

  const preset = RATIOS[args.ratio] || RATIOS.article;
  const width = Number(args.width || preset.width);
  const height = Number(args.height || preset.height);
  const scale = Number(args.scale || 2);

  const html = buildHtml({
    style, hook, width, height,
    eyebrow: args.eyebrow || "", subtitle: args.subtitle || "",
    badge: args.badge || args.kicker || "", tags: args.tags || "",
    stamp: args.stamp || "", bignum: args.bignum || "",
    names: args.names || "", quote: args.quote || "", source: args.source || "",
    mark: args.mark || "",
  });

  const workDir = mkdtempSync(join(tmpdir(), "cover-"));
  const htmlPath = join(workDir, "cover.html");
  writeFileSync(htmlPath, html, "utf8");

  execFileSync(chromeBinary(), [
    "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
    `--force-device-scale-factor=${scale}`, `--window-size=${width},${height}`,
    "--virtual-time-budget=1800", `--screenshot=${args.out}`, `file://${htmlPath}`,
  ], { stdio: "ignore" });

  console.log(`封面已生成：${args.out}  [${style} / ${STYLES[style].layout} / ${width}x${height} @${scale}x]`);
}

main();
