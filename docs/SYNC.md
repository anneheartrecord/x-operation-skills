# 单一事实源与同步方向

## 内容生成层的权威源是本仓库

`content-generation/` 下的 `cover-image` / `xhs-title` / `xhs-keyword-strategy` **以本仓库为唯一权威源**(2026-07-14 起,原来是本地为源、仓库为镜像,现已反转)。

本地消费方通过软链指向仓库,不再各存一份:

```
~/.agent-harness/skills/<skill>  ->  <repo>/content-generation/<skill>   (软链)
~/.claude/skills/<skill>         ->  ~/.agent-harness/skills/<skill>       (软链,透传到仓库)
~/.codex/skills/<skill>          ->  ~/.agent-harness/skills/<skill>       (软链,透传到仓库)
```

**改动只在仓库副本里做**,Claude/Codex 立即透传生效,不会再出现"本地改了仓库没跟上"或反向漂移。

前提:本仓库需常驻本地(clone 在 `~/Anneheartrecord/x-operation-skills`)。换机器用 `setup.sh` 重建软链。

## 与 sync-harness.sh 的相处

`~/.agent-harness/bin/sync-harness.sh` 做的是「Claude/Codex → 共享目录(`~/.agent-harness/skills`)的收拢」。现在这三个 skill 的 `~/.agent-harness/skills/<skill>` 已是**软链到仓库**,不是实体目录:

- sync-harness 若只做「把 Claude/Codex 侧新增 skill 收拢进共享目录」,不会破坏这三个已存在的软链。
- **不要**让 sync-harness 把这三个软链替换成实体拷贝(那会重新制造镜像漂移)。如需在 sync 脚本里排除,按 skill 名跳过这三个。
- 运营层的 4 个 skill(`x-content-review` 等)不在 `~/.agent-harness/skills` 体系里,由 `setup.sh` 直接软链到 `~/.claude/skills`,与本节无关。

## 校验

```bash
# 确认三个软链都指向仓库
for s in cover-image xhs-title xhs-keyword-strategy; do readlink ~/.agent-harness/skills/$s; done
# 确认能透传解析到文件
ls ~/.claude/skills/cover-image/render-cover.mjs
```
