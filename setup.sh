#!/usr/bin/env bash
# x-operation-skills 一键部署:建 venv、装依赖、软链 skill、自检待配项。
# 幂等,可重复跑。默认软链到 ~/.claude/skills 和 ~/.codex/skills(存在才软链)。
#
# 用法:
#   ./setup.sh              # 完整部署
#   ./setup.sh --check      # 只检查依赖/软链/凭证状态,不改动
set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${X_SKILLS_VENV:-$HOME/.venvs/x-skills}"
SECRETS_FILE="$HOME/.config/secrets/api-keys.env"
CHECK_ONLY=0
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=1

OPS_SKILLS=(x-content-review x-account-audit x-post x-hotspot-radar)
CONTENT_SKILLS=(cover-image xhs-title xhs-keyword-strategy)

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }

echo "== x-operation-skills 部署 =="
echo "仓库:$REPO_DIR"

# 1) venv + 依赖
if [[ $CHECK_ONLY -eq 0 ]]; then
  if [[ ! -d "$VENV_DIR" ]]; then
    echo "建 venv:$VENV_DIR"
    python3 -m venv "$VENV_DIR"
  fi
  echo "装依赖(twscrape curl_cffi tweepy pytest)..."
  "$VENV_DIR/bin/pip" install -q --upgrade pip >/dev/null 2>&1 || true
  "$VENV_DIR/bin/pip" install -q twscrape curl_cffi tweepy pytest
  ok "venv 与依赖就绪"
else
  if [[ -x "$VENV_DIR/bin/python" ]]; then ok "venv 存在:$VENV_DIR"; else warn "venv 缺失,跑 ./setup.sh 建立"; fi
fi

# 2) 软链 skill 到 Claude / Codex(哪个存在软链哪个)
realpath_of() { python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$1" 2>/dev/null; }

link_skill() {  # $1=源目录 $2=skill名 $3=目标root
  local src="$1" name="$2" target_root="$3"
  [[ -d "$target_root" ]] || return 0
  local link="$target_root/$name"
  if [[ $CHECK_ONLY -eq 1 ]]; then
    # 比对最终 realpath,允许经 ~/.agent-harness 等中转软链(只要最终落到仓库副本)
    if [[ -e "$link" && "$(realpath_of "$link")" == "$(realpath_of "$src")" ]]; then
      ok "$name → 仓库(解析正确)"
    else
      warn "$target_root/$name 未指向仓库"
    fi
    return 0
  fi
  ln -sfn "$src" "$link"
}

echo "软链 skill..."
for root in "$HOME/.claude/skills" "$HOME/.codex/skills"; do
  [[ $CHECK_ONLY -eq 0 && -d "$(dirname "$root")" ]] && mkdir -p "$root"
  for s in "${OPS_SKILLS[@]}";     do link_skill "$REPO_DIR/$s" "$s" "$root"; done
  for s in "${CONTENT_SKILLS[@]}"; do link_skill "$REPO_DIR/content-generation/$s" "$s" "$root"; done
done
[[ $CHECK_ONLY -eq 0 ]] && ok "7 个 skill 已软链到存在的 Claude/Codex 目录"

# 3) 凭证/代理待配项检查(不打印敏感值)
echo "凭证与代理检查..."
have() { grep -q "^export $1=" "$SECRETS_FILE" 2>/dev/null; }
if [[ -f "$SECRETS_FILE" ]]; then
  have X_AUTH_TOKEN && have X_CT0 && ok "cookie(X_AUTH_TOKEN/X_CT0)已配" || warn "cookie 未配:只读复盘/诊断需要(见 README)"
  if have X_PROXY || grep -qi "^export HTTPS_PROXY=" "$SECRETS_FILE" || [[ -n "${X_PROXY:-}${HTTPS_PROXY:-}${HTTP_PROXY:-}" ]]; then
    ok "代理已配(文件或 live env)"
  else
    warn "代理未配:国内访问 X 必须(export X_PROXY=http://127.0.0.1:7890)"
  fi
  have X_API_KEY && have X_ACCESS_TOKEN && ok "官方 API 凭证已配(发帖/更准读数)" || warn "官方 API 未配:发帖必需,只读可先不配"
else
  warn "$SECRETS_FILE 不存在:按 README 配 cookie(必)+ 代理(国内必)+ 官方 API(发帖必)"
fi

echo
echo "下一步:配好上面标 ! 的项后,跑一次验证:"
echo "  source $SECRETS_FILE && $VENV_DIR/bin/python $REPO_DIR/x-content-review/scripts/fetch_x_pulse.py --user <你的handle> --check"
