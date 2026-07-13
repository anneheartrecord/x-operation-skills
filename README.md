[English](./README_EN.md)

# x-operation-skills

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3%20%2B%20Markdown-green.svg)

X(Twitter) 运营 skill 合集。每个子目录是一个独立 skill,可单独安装到 Claude Code / Codex 等支持 SKILL.md 的 agent。

## Skill 列表

| Skill | 用途 | 触发 |
|---|---|---|
| [x-content-review](./x-content-review/) | 数据内容复盘:发帖时段转化(北京时间)、类别效率、单帖 A/B/C 分级,输出周报 + 下周发帖指导 | 「X复盘」「出X周报」 |
| [x-account-audit](./x-account-audit/) | 账号门面诊断:bio、置顶、封面、头像、辨识度、主页分流能力,逐项体检 + 可直接替换的改写稿 | 「诊断我的X账号」「主页体检」 |
| [x-post](./x-post/) | 官方 API 发帖:先 dry-run 预览内容与费用,用户确认后才发布;支持回复与 thread | 「把这条发到X」「发布这条推文」 |

规划中:x-hotspot-radar(热点雷达:热点总结 → 推文草稿全流程)。

## 凭证配置

### 官方 API(推荐:读自己数据 + 发帖)

X 官方 API 是预充值信用点、按请求扣费、无订阅。关键单价:读自己的帖/粉丝/书签 $0.001/请求(一次复盘不到 1 美分),发纯文字帖 $0.015/条,发含链接帖 $0.20/条(X 刻意抑制外链)。

1. 到 developer.x.com 创建项目,充值信用点。
2. 项目的 Keys and tokens 页生成 Consumer Keys 和 Access Token(勾选 **Read and write**)。
3. 四个值存成环境变量(推荐 `~/.config/secrets/api-keys.env`):

```bash
export X_API_KEY="..."
export X_API_SECRET="..."
export X_ACCESS_TOKEN="..."
export X_ACCESS_TOKEN_SECRET="..."
```

4. 安装依赖:`pip3 install tweepy`。

### cookie(免费兜底:只读)

不想充值时,x-content-review 和 x-account-audit 也能用登录 cookie 读数据(x-post 发帖必须走官方 API,cookie 不支持写):

1. 浏览器登录 x.com。
2. 按 F12 打开开发者工具 → 顶部选 **Application**(Chrome/Edge;Firefox 是 Storage)→ 左侧 **Cookies** → 点开 `https://x.com`。
3. 在列表里找到 `auth_token` 这一行,复制它的 **Value**;再找到 `ct0`,同样复制 Value。
4. 存成环境变量(推荐放 `~/.config/secrets/api-keys.env` 之类只有自己可读的文件,由 shell 启动时 source):

```bash
export X_AUTH_TOKEN="第3步复制的 auth_token 值"
export X_CT0="第3步复制的 ct0 值"
```

5. 安装依赖:`pip3 install twscrape`。

注意:cookie 等同账号密码,只放本机私密文件,绝不提交进仓库;浏览器里退出 x.com 登录会使 cookie 失效,重新登录后按上面步骤再复制一次即可。

可选增强:x-content-review 支持吃 X Analytics 后台导出的 CSV(独有净涨粉、主页访问数据),导了就自动用,不导不影响使用。

## 安装(Claude Code)

```bash
git clone https://github.com/anneheartrecord/x-operation-skills.git
ln -s "$(pwd)/x-operation-skills/x-content-review" ~/.claude/skills/x-content-review
ln -s "$(pwd)/x-operation-skills/x-account-audit" ~/.claude/skills/x-account-audit
ln -s "$(pwd)/x-operation-skills/x-post" ~/.claude/skills/x-post
```

## 方法论来源

- 数据复盘口径:收藏(或涨粉)/万曝光转化率、A/B/C 帖子分级、Snowflake ID 反推发帖时间。
- 账号诊断框架:《把才华变成钱》(王梦珂,信任与变现)+ 向阳乔木(@vista8)X 增长方法论(定位与关注结构)。

## License

MIT
