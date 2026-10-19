#!/usr/bin/env node
/**
 * cover-image 生成式主题（v4，2026-09-08）：doodle / poster 两套走文生图模型，不走 HTML 渲染。
 * 和 render-cover.mjs 的分工：九套确定性主题排版靠 CSS；这两套的核心是「手绘 / 笔刷质感 + 场景插画」，
 * CSS 画不出来，所以借 xhs-cover-skill 已配好的图像模型（~/.config/xhs-cover/config.json，OpenAI 兼容
 * chat/completions + response_modalities）。sharp 直接复用 xhs-cover-skill/node_modules。
 *
 * 用法：
 *   node gen-cover-ai.mjs --style doodle --hook "为什么你发了那么多内容，还是没客人？|因为你没画过这张图" \
 *     --scene "左：一个程序员被一堆内容卡片围住抓头；右：一张寻宝地图" \
 *     --steps "内容,流量,咨询,成交,复购" --out /abs/xxx-cover.png
 *   node gen-cover-ai.mjs --style poster --hook "我用 Codex、飞书多维表格和 TikHub，|搭了一条从搜索词到内容发布的|小红书内容获客流水线" \
 *     --steps "搜索词挖掘,飞书多维表格,Codex 自动化执行,TikHub 发布,数据追踪 & 优化" --footer "附完整教程" --out /abs/xxx-cover.png
 * 参数：
 *   --style   doodle | poster（必填）
 *   --hook    封面主文案，| 分行（必填）。doodle 里可用 *词* 标要画蓝色下划线/圈的重点
 *   --subtitle 副标题一行（可选）
 *   --scene   画面描述（doodle 必填，poster 可选）
 *   --steps   流程节点，逗号分隔，3-5 个（两套都可选；poster 建议给）
 *   --footer  poster 底栏文案，逗号分隔的 2-4 个短语（可选）
 *   --ratio   article（1012×386，默认）| wide（1600×900）
 *   --out     输出 PNG 绝对路径（必填）
 *   --count   生成几张候选，默认 1，最多 3（多张时文件名加 -1/-2）
 *   --dry-run 只打印提示词不调模型
 */
import fs from 'fs';
import os from 'os';
import path from 'path';
import https from 'https';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
// cover-image 本体在 x-operation-skills 仓库里、经软链挂到 ~/.agent-harness/skills，import.meta.url 会解析成真实路径，所以不用相对 `..`
const require = createRequire(path.join(os.homedir(), '.agent-harness', 'skills', 'xhs-cover-skill', 'scripts', 'generate.mjs'));
let sharp;
try { sharp = require('sharp'); } catch { console.error('❌ 缺 sharp：cd ~/.agent-harness/skills/xhs-cover-skill && npm install'); process.exit(1); }

const args = process.argv.slice(2);
const arg = (n, d) => { const i = args.indexOf(`--${n}`); return i >= 0 && args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : d; };
const flag = (n) => args.includes(`--${n}`);

const STYLE = arg('style'); const HOOK = arg('hook'); const OUT = arg('out');
if (!STYLE || !HOOK || !OUT || !['doodle', 'poster'].includes(STYLE)) {
  console.error(fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('*/')[0].replace(/^\/\*\*?/, ''));
  process.exit(1);
}
const SUB = arg('subtitle', ''); const SCENE = arg('scene', ''); const FOOTER = arg('footer', '');
const STEPS = arg('steps', '').split(',').map(s => s.trim()).filter(Boolean);
const RATIO = arg('ratio', 'article'); const COUNT = Math.min(3, Math.max(1, parseInt(arg('count', '1'), 10) || 1));
const SIZES = { article: [1012, 386], wide: [1600, 900] };
if (!SIZES[RATIO]) { console.error('❌ --ratio 只能是 article | wide'); process.exit(1); }
if (STYLE === 'doodle' && !SCENE) { console.error('❌ doodle 必须给 --scene 画面描述'); process.exit(1); }

const hookLines = HOOK.split('|').map(s => s.trim()).filter(Boolean);
const emph = [...HOOK.matchAll(/\*([^*]+)\*/g)].map(m => m[1]);
const plainHook = hookLines.map(l => l.replace(/\*/g, ''));

// ─── 两套风格的提示词骨架（改风格改这里）────────────────────────────────────────
const PROMPTS = {
  doodle: () => `Generate one ultra-wide horizontal (about 2.6:1) Chinese article header illustration.

Visual DNA (hand-drawn marker doodle):
Off-white plain background. Everything drawn by hand with colored markers and crayons: wobbly black outlines, loose colored fills that overshoot the lines, visible stroke texture. Palette: black ink, marker green, marker blue, marker orange-red, kraft beige. Playful, energetic, dense but readable. Looks like a smart person sketched it fast on paper. No vector flatness, no gradients, no 3D, no photo, no glossy UI, no children's-book cuteness.

Title (must be rendered exactly, large hand-lettered Chinese marker text across the top, dominant, one line per item):
${plainHook.map((l, i) => `Line ${i + 1}: 「${l}」`).join('\n')}
${emph.length ? `Emphasize these words with a hand-drawn blue underline or a blue circled outline: ${emph.map(e => `「${e}」`).join(' / ')}` : ''}
${SUB ? `Small hand-written subtitle below the title: 「${SUB}」` : ''}

Scene below the title:
${SCENE}
${STEPS.length ? `\nInclude a hand-drawn journey / flow with these labeled stops in order, each stop a small icon plus its Chinese label: ${STEPS.map(s => `「${s}」`).join(' → ')}. Connect the stops with a dashed hand-drawn path.` : ''}

Constraints:
All text must be Chinese, hand-lettered, and spelled exactly as given; no other text. Title occupies roughly the top 30% of the canvas; scene occupies the bottom 70%. Keep the scene readable at thumbnail size: few big shapes, no tiny clutter. No watermark, no signature, no logo.

Canvas layout for cropping (critical): the image will be cropped to an ultra-wide 2.6:1 banner. Compose EVERYTHING (title, scene, all text) inside a horizontal band occupying only the central 55% of the canvas height. The top 22% and bottom 22% must be plain empty background with nothing in them. No element may touch those margins.`,

  poster: () => `Generate one ultra-wide horizontal (about 2.6:1) Chinese poster-style article header.

Visual DNA (brush-stroke black & yellow poster):
Off-white paper background with rough ink splatter at the edges. Headline set in extra-bold black Chinese sans-serif, huge, left-aligned, stacked lines; key words sit on thick hand-brushed highlight bars in bright yellow (#F5C400) or on black bars with white/yellow text. A thick yellow brush stroke sweeps behind the flow. Bottom band is solid black with yellow line icons and white labels. High contrast, editorial, confident. No gradients, no 3D, no photo people, no cute mascots.

Headline (render exactly, one line per item, left side, about 40% of width):
${plainHook.map((l, i) => `Line ${i + 1}: 「${l}」`).join('\n')}
${SUB ? `Smaller line under the headline: 「${SUB}」` : ''}

Right side (about 60% of width):
${STEPS.length ? `A numbered horizontal flow of ${STEPS.length} steps, each with a yellow circle icon on top, bold Chinese step name, and a small mock UI panel underneath (clean flat mock screens: a list, a table, a code editor, a publish button, a phone with a chart; NOT real screenshots). Steps in order: ${STEPS.map((s, i) => `${i + 1}. 「${s}」`).join('  ')}. Thin black arrows between steps.` : (SCENE || 'A few clean flat mock UI panels arranged in a row, connected by thin arrows.')}
${FOOTER ? `\nBottom black band: ${FOOTER.split(',').map(s => `「${s.trim()}」`).join(' | ')} as yellow icon + white label pairs, separated by thin vertical lines.` : ''}

Constraints:
All text Chinese except product names, spelled exactly as given; no invented extra text. Headline must stay fully inside the left area and never overlap the flow. No watermark, no signature.

Canvas layout for cropping (critical): the image will be cropped to an ultra-wide 2.6:1 banner. Compose EVERYTHING (title, scene, all text) inside a horizontal band occupying only the central 55% of the canvas height. The top 22% and bottom 22% must be plain empty background with nothing in them. No element may touch those margins.`,
};

const prompt = PROMPTS[STYLE]();
if (flag('dry-run')) { console.log(prompt); process.exit(0); }

// ─── 调模型（配置复用 xhs-cover-skill）──────────────────────────────────────────
const cfgPath = path.join(os.homedir(), '.config/xhs-cover/config.json');
if (!fs.existsSync(cfgPath)) { console.error(`❌ 缺 ${cfgPath}，先按 xhs-cover-skill 配好图像模型`); process.exit(1); }
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
const url = cfg.apiEndpoint || `${cfg.baseUrl}/v1/chat/completions`;

function extractImage(result) {
  const content = result?.choices?.[0]?.message?.content;
  if (typeof content === 'string') { const m = content.match(/!\[.*?\]\(data:([^;]+);base64,([A-Za-z0-9+/=\s]+)\)/s); if (m) return Buffer.from(m[2].replace(/\s/g, ''), 'base64'); }
  const imgs = result?.choices?.[0]?.message?.images;
  if (Array.isArray(imgs) && imgs[0]?.image_url?.url) { const m = imgs[0].image_url.url.match(/^data:[^;]+;base64,(.+)$/s); if (m) return Buffer.from(m[1], 'base64'); }
  for (const p of result?.candidates?.[0]?.content?.parts || []) if (p?.inlineData?.data) return Buffer.from(p.inlineData.data, 'base64');
  throw new Error(`响应里没有图片：${JSON.stringify(result).slice(0, 300)}`);
}

// 模型链：gpt-image-2 中文字渲染最稳，走 images/generations；不通再退 gemini（chat + response_modalities）。
// config.json 里的 model（gemini-3.1-flash-image）2026-09-08 实测中转站上游 500，所以不把它放第一位。--model 可强制指定。
// 这两套封面满是中文字，实测只有 gpt-image-2 写得对（gemini-2.5-flash-image 中文成片错字，不可用）。
// 所以默认只走 gpt-image-2 并重试 3 次；--model 可强制指定别的（自担错字风险）。
const CHAIN = arg('model') ? [arg('model')] : ['gpt-image-2', 'gpt-image-2', 'gpt-image-2'];

function postTo(endpoint, bodyObj) {
  return new Promise((resolve, reject) => {
    const u = new URL(endpoint); const body = JSON.stringify(bodyObj);
    const req = https.request({ hostname: u.hostname, path: u.pathname + u.search, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body), Authorization: `Bearer ${cfg.apiKey}` } }, (res) => {
      const chunks = []; res.on('data', c => chunks.push(c));
      res.on('end', () => { const t = Buffer.concat(chunks).toString(); if (res.statusCode >= 300) return reject(new Error(`HTTP ${res.statusCode}: ${t.slice(0, 200)}`)); try { resolve(JSON.parse(t)); } catch { reject(new Error(`非 JSON：${t.slice(0, 200)}`)); } });
    });
    req.setTimeout(240_000, () => { req.destroy(); reject(new Error('超时 240s')); });
    req.on('error', reject); req.write(body); req.end();
  });
}

async function generate(model) {
  if (model.startsWith('gpt-image')) {
    const r = await postTo(`${cfg.baseUrl}/v1/images/generations`, { model, prompt, size: '1536x1024', n: 1 });
    const b64 = r?.data?.[0]?.b64_json; if (!b64) throw new Error('images 响应无 b64_json');
    return Buffer.from(b64, 'base64');
  }
  return extractImage(await postTo(url, { model, messages: [{ role: 'user', content: prompt + '\n\n【输出规格】横版 16:9。' }], response_modalities: ['image', 'text'] }));
}

const [W, H] = SIZES[RATIO];
for (let i = 1; i <= COUNT; i++) {
  const out = COUNT === 1 ? OUT : OUT.replace(/\.png$/i, `-${i}.png`);
  let buf, used;
  for (const m of CHAIN) {
    process.stdout.write(`🎨 ${STYLE} 第 ${i}/${COUNT} 张 → ${m} ...`);
    try { buf = await generate(m); used = m; console.log(' ✓'); break; } catch (e) { console.log(` ✗ ${e.message.slice(0, 120)}`); }
  }
  if (!buf) { console.error('❌ 模型链全部失败'); process.exit(2); }
  // 模型最宽只给 3:2，要裁到 2.6:1。实测模型会无视「留出上下空带」的指令铺满画布，居中裁会切掉顶部标题，
  // 所以改成从内容顶端锚定：用 trim 找到第一行非背景像素，从它上方留一点边开始裁，牺牲的是底部（桌面、纸张等次要物）。
  const meta = await sharp(buf).metadata();
  const targetH = Math.min(meta.height, Math.round(meta.width * H / W));
  let contentTop = 0;
  try { const { info } = await sharp(buf).trim({ threshold: 30 }).toBuffer({ resolveWithObject: true }); contentTop = Math.max(0, -(info.trimOffsetTop || 0)); } catch {}
  const top = Math.min(Math.max(0, contentTop - Math.round(meta.height * 0.02)), meta.height - targetH);
  await sharp(buf).extract({ left: 0, top, width: meta.width, height: targetH }).resize(W * 2, H * 2).png().toFile(out);
  console.log(`   ${used} → ${out}`);
}
