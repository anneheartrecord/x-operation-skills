[English](./README_EN.md)

# x-operation-skills

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3%20%2B%20Markdown-green.svg)

X(Twitter) 运营 skill 合集。每个子目录是一个独立 skill,可单独安装到 Claude Code / Codex 等支持 SKILL.md 的 agent。

## Skill 列表

| Skill | 用途 | 触发 |
|---|---|---|
| [x-content-review](./x-content-review/) | 数据内容复盘:周度趋势、发帖时段转化(北京时间)、类别涨粉效率、单帖 A/B/C 分级,输出周报 + 下周发帖指导 | 「X复盘」「出X周报」 |
| [x-account-audit](./x-account-audit/) | 账号门面诊断:bio、置顶、封面、头像、辨识度、主页分流能力,逐项体检 + 可直接替换的改写稿 | 「诊断我的X账号」「主页体检」 |

规划中:x-hotspot-radar(热点雷达:热点总结 → 推文草稿全流程)。

## 安装(Claude Code)

```bash
git clone https://github.com/anneheartrecord/x-operation-skills.git
ln -s "$(pwd)/x-operation-skills/x-content-review" ~/.claude/skills/x-content-review
ln -s "$(pwd)/x-operation-skills/x-account-audit" ~/.claude/skills/x-account-audit
```

## 方法论来源

- 数据复盘口径:涨粉/万曝光转化率、A/B/C 帖子分级、Snowflake ID 反推发帖时间。
- 账号诊断框架:《把才华变成钱》(王梦珂,信任与变现)+ 向阳乔木 X 增长方法论(定位与关注结构)。

## License

MIT
