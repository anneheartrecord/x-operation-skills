[English](./README_EN.md)

# x-operation-skills

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3%20%2B%20Markdown-green.svg)

一套 X(Twitter) 运营的 AI agent skill(Claude Code / Codex 通用)。装好、配一次 cookie,之后用中文对 agent 说一句话就能做:数据复盘、账号诊断、发帖、热点做推文。

## 有什么用

| Skill | 作用 | 对 agent 说 |
|---|---|---|
| **x-content-review** | 拉自己账号数据,算出**什么内容、什么时段涨粉最快**,给下周发帖建议 | 「出X周报」 |
| **x-account-audit** | 体检 bio / 置顶 / 头像 / 封面,直接给能替换的改写稿 | 「诊断我的X账号」 |
| **x-post** | 官方 API 发帖,发前预览内容和费用,确认才发;长文自动拆 thread | 「把这条发到X」 |
| **x-hotspot-radar** | 扫热点 → 过滤 → 写成符合你文风、去过 AI 味、配好图的推文草稿 | 「今天发什么」 |

配套还有:粉丝快照 + 周报**每周自动出稿**(launchd 定时)、对标账号追踪、选题库回环、cookie 健康检查。

## 怎么用

**第一步:配 cookie(一次,几个月不用换)**

1. 浏览器登录 x.com → F12 → Application → Cookies → `x.com`,复制 `auth_token` 和 `ct0` 两项的值。
2. 存进 `~/.config/secrets/api-keys.env`:
   ```bash
   export X_AUTH_TOKEN="第 1 步的 auth_token"
   export X_CT0="第 1 步的 ct0"
   export X_PROXY="http://127.0.0.1:7890"   # 国内必填,换成你的代理端口
   ```
3. 装依赖:`pip3 install twscrape curl_cffi`(发帖还需 `tweepy`)。

**第二步:装 skill**

```bash
git clone https://github.com/anneheartrecord/x-operation-skills.git
for s in x-content-review x-account-audit x-post x-hotspot-radar; do
  ln -s "$(pwd)/x-operation-skills/$s" ~/.claude/skills/$s
done
```

**第三步:用**——对 agent 说「出X周报」「诊断我的X账号」即可。数据都是读你自己账号的公开指标(cookie),发帖走官方 API(按量计费,发前确认)。

> 发帖是官方 API,预充值按次扣费:纯文字 $0.015/条,含链接 $0.20/条(所以 x-post 会把链接归到 thread 末条省钱)。只读复盘/诊断用 cookie,不花钱。

## 实测样例(@Charles77xixi 真实数据)

**本周大盘(近 7 天 vs 前 7 天)**:发帖 26 vs 21,曝光 -34%,但单位效率(收藏/万曝光)44.2 vs 45.1 基本持平——掉的是曝光量不是转化率。

**什么内容涨粉快**(收藏/万曝光):

| 类别 | 帖数 | 效率 |
|---|---|---|
| 投资 | 29 | **39.7** |
| 开户出入金 | 8 | **31.2** |
| 职业成长 | 4 | 26.7(样本少) |
| AI 工程 | 68 | 14.0 |
| 其他 | 109 | 6.9 |

结论:投资/开户是效率天花板,但 AI 工程发得第二多(68 帖)、效率只有投资的 35%——**精力和转化反向**。

**什么时段发效率高**(北京时间):14-16 点(67.4)、20-22 点(54.9)是黄金档,但发得最多的是 18-20 点(54 帖,效率仅 9.1)——**弹药砸错了档位**。

**账号诊断**:bio「00 后｜AI Agent｜长期投资者 / 写一些 AI 干货 & 投资系统」= 身份堆叠 + 能力清单双死法,skill 直接给 3 版可替换的改写稿(如「00 后工程师,自己写代码也自己打理钱。分享技术人怎么把 AI 用在真项目、把工资变成资产」)。

## 数据与自动化

- 运行态数据落 `~/.local/share/x-operation-skills/`(含登录态,刻意不进 git)。
- 可选 launchd 定时(macOS):每日记粉丝数、每周一自动出周报(headless agent 直接写成稿)。
- cookie 失效时(登出/改密)定时任务会先检查并弹通知提示重配,不会刷屏报错。

## 方法论来源

账号诊断框架来自《把才华变成钱》(王梦珂)+ 向阳乔木(@vista8)的 X 增长方法论。

## License

MIT
