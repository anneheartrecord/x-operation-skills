[English](./README_EN.md)

# x-hotspot-radar

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3%20%2B%20Markdown-green.svg)

X(Twitter) 热点雷达 skill:把「今天有什么值得蹭的热点」变成一条符合个人文风、去过 AI 味、配好图、可直接发布的推文草稿。

## 定位:编排层,不重造轮子

本 skill 只做三件事:**热点扫描 + 五重过滤 + 流程串联**。文风、去 AI 味、配图、发布全部调用你已装好的系统:

| 环节 | 调用 |
|---|---|
| 文风 | 写作系统三件套 + 镇库范文 |
| 开头 / 发布前诊断 | `dbs-hook`、`dbs-resonate` |
| 去 AI 味 | `de-ai-flavor` |
| 配图 / 封面 | `ian-xiaohei-illustrations`、`guizang-material-illustration`、`cover-image` |
| 发布 | 同仓 `x-post`(dry-run + 确认) |

## 流程

1. 扫热点(`scripts/scan_hotspots.py` 生成查询计划,agent 用 WebSearch/WebFetch 抓)。
2. 五重过滤:相关性 / 稀缺角度 / 时效 / 信任增益 / 可持续,任一不过淘汰。
3. 出角度和结构提纲,等用户拍板(硬性分步)。
4. 写开头段做风格校准,等反馈。
5. 铺全文(镇库范文编号说理骨架)。
6. 去 AI 味(`de-ai-flavor`)。
7. 配图(可选)。
8. 落盘草稿到 `30-outputs/tweets/`,默认到此为止。
9. 发布仅当用户明确要求,交给 `x-post`。

## 使用

安装为 skill 后对 agent 说「扫下热点」「今天发什么」即可。分步产出提纲→开头→全文,不会一步到底(除非你说「直接出全文」),产物是初稿,不代替你发布。

## License

MIT
