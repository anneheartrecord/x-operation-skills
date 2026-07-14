# content-generation · 内容生成层

X 内容生成 + 运营包的**内容生成层**。这三个是通用 skill,和仓库根目录的运营层(x-content-review / x-account-audit / x-post / x-hotspot-radar)配套,由 `x-hotspot-radar` 在「热点 → 落地推文」流程里自动编排。

| Skill | 作用 |
|---|---|
| [cover-image](./cover-image/) | 生成封面图:从原文挖情绪钩子(好奇/共鸣),本机 Chrome headless 确定性渲染 PNG,不用文生图模型、不联网。三主题(invest/tech/life) |
| [xhs-title](./xhs-title/) | 标题公式:8 个爆款模板 + 情绪化叠加 + 字词推敲。标题走搜索关键词(和封面的情绪钩子分工) |
| [xhs-keyword-strategy](./xhs-keyword-strategy/) | 关键词策略:主关键词 → 标题/封面/正文/标签对齐,做搜索长尾覆盖 |

## 说明

- **封面给人看、标题给机器看**:封面文案只走情绪(拿点击),标题覆盖搜索词(拿长尾),两条线分开做,别混。
- **本仓库副本是唯一权威源**(2026-07-14 起反转):`~/.agent-harness/skills/<skill>` 已改为软链指向这里,Claude/Codex 透传消费。改动只在本仓库做,本地立即生效,不再有镜像漂移。方向与 sync-harness 相处见 [`docs/SYNC.md`](../docs/SYNC.md)。
- **不含**个人写作系统(文风 DNA / 镇库范文)——那部分是个人 IP,留在本地,由 `x-hotspot-radar` 引用,不公开。
- `cover-image` 依赖 macOS 系统字体(Songti SC / Kaiti SC / Heiti SC)和本机 Chrome。

## 安装

```bash
for s in cover-image xhs-title xhs-keyword-strategy; do
  ln -s "$(pwd)/content-generation/$s" ~/.claude/skills/$s
done
```
