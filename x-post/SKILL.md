---
name: x-post
description: |
  通过 X 官方 API 发布推文(按量计费:纯文字 $0.015/条,含链接 $0.20/条)。带确认门槛:先 dry-run 预览内容和预估费用,用户明确确认后才真正发布;支持回复指定帖子、发多条 thread。
  触发方式:/x-post、「把这条发到X」「发布这条推文」「用API发帖」。
  Post tweets via the official X API (pay-per-use). Dry-run preview with cost estimate first; publishes only after explicit user confirmation. Supports replies and threads.
  Trigger: /x-post, "post this to X", "publish this tweet".
---

# X 发帖(官方 API)

把定稿内容通过官方 API 发到 X。核心原则:**发布是不可逆的对外动作,永远先预览、后确认、再发布**。

## 前置条件

官方 API 的 OAuth 凭证,四个环境变量(developer.x.com → 项目 → Keys and tokens,Access Token 需勾选 Read and write;按惯例存 `~/.config/secrets/api-keys.env`):

```
export X_API_KEY="..."
export X_API_SECRET="..."
export X_ACCESS_TOKEN="..."
export X_ACCESS_TOKEN_SECRET="..."
```

依赖:`pip3 install tweepy`。计费为预充值信用点、按请求扣费、无订阅。

## 工作流程(硬性顺序,不可跳步)

### 第 1 步:dry-run 预览

```bash
python3 <skill目录>/scripts/post_tweet.py --text "帖子内容"
```

输出内容、字数、预估费用。把预览结果原样给用户看,特别是:

- **含链接的帖单价 $0.20,是纯文字($0.015)的 13 倍**(X 刻意抑制外链)。检测到链接必须显式提醒,并建议备选:链接放到自回复里(主帖纯文字 $0.015 + 回复含链接 $0.20,总价不变但主帖曝光不受外链抑制)。
- 超过 280 字符会发布失败,预览时先检查(中文按 2 字符计)。

### 第 2 步:等用户明确确认

**只有用户明确说「发」「确认发布」「就这条」等肯定指令才进入第 3 步。**以下情况一律不发:用户只是让你「生成/改一下/看看」;内容还是草稿阶段;用户没有对本次预览的具体内容表态。修改内容后必须重新 dry-run,不能拿旧确认发新内容。

### 第 3 步:发布

```bash
python3 <skill目录>/scripts/post_tweet.py --text "帖子内容" --yes
```

### 发 thread(长文自动拆分)

长文一条发不下时,用同仓 `split_thread.py` 拆:按句界切成 ≤270 加权长度(中文算 2),**把所有链接归拢到末条自回复**,这样整个 thread 只有末条付 $0.20,正文各条 $0.015。

```bash
python3 <仓库>/x-post/scripts/split_thread.py --file draft.md --number > thread-plan.json
python3 <skill目录>/scripts/post_tweet.py --thread-file thread-plan.json        # dry-run 预览
python3 <skill目录>/scripts/post_tweet.py --thread-file thread-plan.json --yes  # 确认后顺序发
```

注意:链接被抽到末条后,正文里原本「仓库在 <链接>」这类句子会留空档,拆分前把这类句子改成不依赖内联链接的说法(如「仓库和链接放在末条」)。dry-run 会显示每条正文、加权长度、预估总价,让用户确认整个 thread 再发。

### 第 4 步:回报结果

把返回的帖子 URL 给用户;发布记录(时间、内容、费用)追加到用户运营目录的发布日志(若有)。

## 判断规则(硬口径)

- 没有 dry-run 过的内容绝不发布。
- 一次确认只对应一次发布;批量发 thread 需要用户对整个 thread 文案确认过。
- 发布失败(限流/凭证过期)时原样报错,不重试超过 1 次,不静默吞错。
- 费用敏感:单次会话累计发帖费用预估超过 $1 时,汇总提醒用户。
