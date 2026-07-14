#!/usr/bin/env node
/**
 * render-cover.mjs — 把一篇文章的元信息渲染成一张 16:9 编辑风封面图 PNG。
 *
 * 管线：本脚本用参数拼出一段自包含 HTML（内联 CSS + SVG 母题），写到临时文件，
 * 再用本机 Chrome 的 headless 截图能力渲染成 PNG。全程无需联网、无文生图模型，
 * 只用系统字体（Songti SC / Kaiti SC / Heiti SC），因此风格永远一致、可复现。
 *
 * 用法：
 *   node render-cover.mjs \
 *     --theme life \
 *     --kicker "随笔 · 两性" \
 *     --title "我对两性的理解" \
 *     --byline "个人长文" \
 *     --out "/abs/path/我对两性的理解-cover.png"
 *
 * 参数：
 *   --theme   四选一：invest（投资理财）| tech（AI与工程）| life（人生与思考）| curation（他山之石/剪藏）
 *   --title   主标题；用竖线 | 手动分行，如 "一红16年|干啥啥赚钱"。不分行则按宽度自动换行。
 *   --kicker  左上角小标签（栏目），如 "投资 · 简单致富"。可省略。
 *   --byline  左下角署名/来源，如 "课代表立正 · 屠龙博士"。可省略。
 *   --brand   右下角品牌角标，可省略。
 *   --out     输出 PNG 的绝对路径（必填）。
 *   --width   画布宽，默认 1600（输出按 2x = 3200）。
 *   --height  画布高，默认 900（输出按 2x = 1800）。
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
      if (next === undefined || next.startsWith("--")) {
        parsed[key] = true;
      } else {
        parsed[key] = next;
        index += 1;
      }
    }
  }
  return parsed;
}

/** 转义 HTML 特殊字符，防止标题里的 < & 等破坏结构。 */
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * 四类主题的视觉配置：共用近黑底 + 宋体羊皮纸标题骨架，靠 accent 强调色和 motif 母题区分。
 * accent  = 强调色（kicker/细线/辉光）
 * glowPos = 辉光位置
 * tint    = 背景暖/冷微调叠色
 */
const THEMES = {
  invest: {
    accent: "#d4a24e",
    glow: "radial-gradient(circle at 82% 78%, rgba(212,162,78,0.20), transparent 60%)",
    tint: "radial-gradient(ellipse at 28% 18%, rgba(60,52,34,0.55), transparent 62%)",
  },
  tech: {
    accent: "#5b8fb0",
    glow: "radial-gradient(circle at 80% 72%, rgba(91,143,176,0.22), transparent 60%)",
    tint: "radial-gradient(ellipse at 28% 18%, rgba(34,48,60,0.55), transparent 62%)",
  },
  life: {
    accent: "#c2724a",
    glow: "radial-gradient(circle at 78% 30%, rgba(194,114,74,0.20), transparent 58%)",
    tint: "radial-gradient(ellipse at 26% 22%, rgba(62,42,32,0.58), transparent 62%)",
  },
};

/** 生成每类主题右下/角落的 SVG 母题。都用 accent 色、低透明度，保证不压过标题。 */
function motifSvg(theme, accent) {
  if (theme === "invest") {
    // 底部极简 K 线 + 趋势线
    let candles = "";
    const heights = [70, 110, 90, 150, 130, 190, 160, 230, 210, 280, 250, 320];
    heights.forEach((h, i) => {
      const x = 60 + i * 128;
      const top = 900 - h;
      const wickTop = top - 34;
      const wickBot = 900 - h + h * 0.55;
      candles += `<line x1="${x + 26}" y1="${wickTop}" x2="${x + 26}" y2="${wickBot}" stroke="${accent}" stroke-width="3"/>`;
      candles += `<rect x="${x}" y="${top}" width="52" height="${h * 0.5}" rx="4" fill="${accent}" opacity="0.9"/>`;
    });
    return `<svg viewBox="0 0 1600 900" preserveAspectRatio="none" style="position:absolute;inset:0;opacity:0.14">
      <polyline points="60,760 200,700 340,720 480,600 620,640 760,500 900,540 1040,420 1180,450 1320,320 1460,360 1560,280"
        fill="none" stroke="${accent}" stroke-width="4" opacity="0.7"/>
      ${candles}
    </svg>`;
  }
  if (theme === "tech") {
    // 右下角节点连线图 + 细网格
    const nodes = [
      [1120, 560], [1260, 500], [1360, 620], [1220, 700], [1440, 540], [1330, 760], [1480, 680],
    ];
    let edges = "";
    const links = [[0,1],[1,2],[0,3],[2,3],[1,4],[2,6],[3,5],[4,6],[5,6]];
    links.forEach(([a, b]) => {
      edges += `<line x1="${nodes[a][0]}" y1="${nodes[a][1]}" x2="${nodes[b][0]}" y2="${nodes[b][1]}" stroke="${accent}" stroke-width="2.5"/>`;
    });
    let dots = "";
    nodes.forEach(([x, y], i) => {
      const r = i % 3 === 0 ? 13 : 8;
      dots += `<circle cx="${x}" cy="${y}" r="${r}" fill="${accent}"/>`;
    });
    let grid = "";
    for (let gx = 0; gx <= 1600; gx += 80) grid += `<line x1="${gx}" y1="0" x2="${gx}" y2="900" stroke="${accent}" stroke-width="1"/>`;
    for (let gy = 0; gy <= 900; gy += 80) grid += `<line x1="0" y1="${gy}" x2="1600" y2="${gy}" stroke="${accent}" stroke-width="1"/>`;
    return `<svg viewBox="0 0 1600 900" style="position:absolute;inset:0">
      <g opacity="0.05">${grid}</g>
      <g opacity="0.22">${edges}${dots}</g>
    </svg>`;
  }
  // life（默认）：一道毛笔横扫（两头收锋的墨迹带）
  return `<svg viewBox="0 0 1600 900" style="position:absolute;inset:0;opacity:0.16">
      <path d="M-40,650 C 320,560 560,690 860,600 C 1160,510 1360,660 1680,560 L 1680,720 C 1360,800 1160,700 860,760 C 560,820 320,730 -40,800 Z"
        fill="${accent}"/>
      <path d="M120,470 C 420,430 720,500 1040,455" fill="none" stroke="${accent}" stroke-width="3" opacity="0.5"/>
    </svg>`;
}

/** feTurbulence 生成的微噪点，让画面有纸张/胶片质感（内联为 data-uri）。 */
const GRAIN =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/></filter><rect width='240' height='240' filter='url(#n)' opacity='0.5'/></svg>`
  );

/** 用参数拼出整页 HTML。 */
function buildHtml({ theme, hook, subtitle, kicker, byline, brand, width, height }) {
  const t = THEMES[theme] || THEMES.life;
  const accent = t.accent;
  // 钩子金句：用 | 分行，用 *...* 把关键词高亮成强调色（先转义再替换，保证 span 不被转义）
  const hookLines = String(hook)
    .split("|")
    .map((line) => {
      const safe = escapeHtml(line.trim()).replace(/\*([^*]+)\*/g, '<span class="em">$1</span>');
      return `<div class="line">${safe}</div>`;
    })
    .join("");
  const kickerHtml = kicker
    ? `<div class="kicker"><span class="tick"></span>${escapeHtml(kicker)}</div>`
    : "";
  const subtitleHtml = subtitle
    ? `<div class="subtitle">${escapeHtml(subtitle)}</div>`
    : "";
  const bylineHtml = byline ? `<div class="byline">${escapeHtml(byline)}</div>` : "";
  const brandHtml = brand ? `<div class="brand">${escapeHtml(brand)}</div>` : "";
  const monoKicker = theme === "tech";

  return `<!doctype html><html><head><meta charset="utf-8"><style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { width: ${width}px; height: ${height}px; }
    .cover {
      position: relative; width: ${width}px; height: ${height}px; overflow: hidden;
      background:
        ${t.glow},
        ${t.tint},
        radial-gradient(ellipse at 32% 16%, #262b33 0%, #191c21 55%, #131519 100%);
      font-family: "Heiti SC", "PingFang SC", -apple-system, sans-serif;
    }
    .grain {
      position: absolute; inset: 0; background-image: url("${GRAIN}");
      background-size: 320px 320px; opacity: 0.045; mix-blend-mode: overlay; pointer-events: none;
    }
    .vignette {
      position: absolute; inset: 0; pointer-events: none;
      box-shadow: inset 0 0 260px 60px rgba(0,0,0,0.55);
    }
    .frame {
      position: absolute; inset: 44px; border: 1px solid rgba(236,227,200,0.14); border-radius: 2px;
      pointer-events: none;
    }
    .content {
      position: absolute; inset: 0; padding: 108px 112px;
      display: flex; flex-direction: column; justify-content: center;
    }
    .kicker {
      display: flex; align-items: center; gap: 16px;
      color: ${accent}; letter-spacing: ${monoKicker ? "0.14em" : "0.34em"};
      font-size: 27px; font-weight: 600; margin-bottom: 40px;
      ${monoKicker ? 'font-family: "SF Mono", "Menlo", monospace; text-transform: uppercase;' : ""}
    }
    .tick { width: 34px; height: 3px; background: ${accent}; display: inline-block; }
    .hook {
      font-family: "Songti SC", "STSong", "Noto Serif CJK SC", serif;
      font-weight: 900; color: #f2e9ce; font-size: 122px; line-height: 1.2;
      letter-spacing: 0.008em; max-width: 1290px; text-shadow: 0 3px 28px rgba(0,0,0,0.5);
      border-left: 8px solid ${accent}; padding-left: 46px;
    }
    .hook .line { white-space: nowrap; }
    .hook .em { color: ${accent}; }
    .subtitle {
      margin-top: 44px; padding-left: 54px;
      color: rgba(236,227,200,0.60); font-size: 34px; letter-spacing: 0.06em;
    }
    .subtitle::before {
      content: "本文 · "; color: ${accent}; opacity: 0.85;
    }
    .byline {
      position: absolute; left: 112px; bottom: 96px;
      color: rgba(236,227,200,0.62); font-size: 27px; letter-spacing: 0.08em;
    }
    .brand {
      position: absolute; right: 112px; bottom: 96px;
      color: rgba(236,227,200,0.5); font-size: 25px; letter-spacing: 0.14em;
    }
  </style></head><body>
    <div class="cover">
      ${motifSvg(theme, accent)}
      <div class="grain"></div>
      <div class="vignette"></div>
      <div class="frame"></div>
      <div class="content">
        ${kickerHtml}
        <div class="hook">${hookLines}</div>
        ${subtitleHtml}
      </div>
      ${bylineHtml}
      ${brandHtml}
    </div>
  </body></html>`;
}

/** 定位本机 Chrome 可执行文件。 */
function chromeBinary() {
  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  ];
  for (const path of candidates) {
    try {
      execFileSync("test", ["-f", path]);
      return path;
    } catch {
      /* 继续尝试下一个 */
    }
  }
  throw new Error("找不到 Chrome/Chromium/Edge，无法渲染封面。");
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  // --hook 是封面主角（大钩子金句）；没给 hook 则回退用 --title 当钩子
  const hook = args.hook || args.title;
  if (!args.out || !hook) {
    console.error("必填：--out <PNG绝对路径> 和 --hook <钩子金句>（可用 | 分行、*词* 高亮）");
    console.error("可选：--subtitle <真实标题> --kicker <栏目> --theme invest|tech|life --byline --brand");
    process.exit(1);
  }
  const width = Number(args.width || 1600);
  const height = Number(args.height || 900);
  const html = buildHtml({
    theme: args.theme || "life",
    hook,
    subtitle: args.subtitle || "",
    kicker: args.kicker || "",
    byline: args.byline || "",
    brand: args.brand || "",
    width,
    height,
  });

  const workDir = mkdtempSync(join(tmpdir(), "cover-"));
  const htmlPath = join(workDir, "cover.html");
  writeFileSync(htmlPath, html, "utf8");

  const chrome = chromeBinary();
  execFileSync(
    chrome,
    [
      "--headless=new",
      "--disable-gpu",
      "--hide-scrollbars",
      "--no-sandbox",
      "--force-device-scale-factor=2",
      `--window-size=${width},${height}`,
      "--virtual-time-budget=1800",
      "--default-background-color=00000000",
      `--screenshot=${args.out}`,
      `file://${htmlPath}`,
    ],
    { stdio: "ignore" }
  );
  console.log(`封面已生成：${args.out}  (${width * 2}x${height * 2})`);
}

main();
