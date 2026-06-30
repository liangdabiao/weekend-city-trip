#!/bin/bash
# ============================================================
# build_map.sh — 一键地图生成管线
# 用法:
#   bash build_map.sh <城市> <日期范围> -m <markdown.md> [-o <output.html>]
#
# 示例:
#   bash build_map.sh 金华 "2026年7月(未来一个月)" \
#     -m "D:/fireclaw/金华未来一个月调查报告_博查版.md" \
#     -o "D:/fireclaw/金华地图_博查版.html"
#
# 环境变量(必需):
#   AMAP_KEY      高德 Web 服务 API Key (用于 geocode.py)
#   AMAP_JS_KEY   高德 Web 端 JS API Key (用于 inject.py)
#   AMAP_SECURITY 高德安全密钥 (用于 inject.py)
#   BOCHA_API_KEY 博查 API Key (用于 clean_geojson.py LLM 过滤)
# ============================================================
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS_DIR="$SKILL_DIR/scripts"

# 加载 .env 文件(如存在),已设置的环境变量不覆盖
_load_dotenv() {
  local env_file
  for env_file in "$SKILL_DIR/.env" "$PWD/.env"; do
    if [[ -f "$env_file" ]]; then
      while IFS='=' read -r key val || [[ -n "$key" ]]; do
        key="$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        val="$(echo "$val" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s/^"//;s/"$//;s/^'\''//;s/'\''$//')"
        [[ -z "$key" || "$key" == \#* ]] && continue
        # 不覆盖已设置的环境变量
        if [[ -z "${!key:-}" ]]; then
          export "$key=$val"
        fi
      done < "$env_file"
    fi
  done
}
_load_dotenv

OUTPUT_DIR="${OUTPUT_DIR:-D:/fireclaw}"

CITY=""
DATE_RANGE=""
MD_FILE=""
OUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--markdown) MD_FILE="$2"; shift 2 ;;
    -o|--output)   OUT_FILE="$2"; shift 2 ;;
    *)
      if [[ -z "$CITY" ]]; then CITY="$1"
      elif [[ -z "$DATE_RANGE" ]]; then DATE_RANGE="$1"
      else echo "未知参数: $1"; exit 1
      fi
      shift ;;
  esac
done

if [[ -z "$CITY" ]]; then
  echo "❌ 用法: bash build_map.sh <城市> <日期范围> -m <markdown.md> [-o <output.html>]"
  exit 1
fi

# 自动推断文件路径
if [[ -z "$MD_FILE" ]]; then
  # 自动搜索城市对应的 .md 文件
  MD_FILE=$(ls "$OUTPUT_DIR"/*${CITY}*调查报告_博查版.md 2>/dev/null | head -1 || true)
  if [[ -z "$MD_FILE" ]]; then
    echo "❌ 未找到 ${CITY} 的 Markdown 报告文件,请用 -m 指定"
    exit 1
  fi
fi

if [[ ! -f "$MD_FILE" ]]; then
  echo "❌ 文件不存在: $MD_FILE"
  exit 1
fi

BASE="${MD_FILE%.md}"
PLACES_JSON="${BASE}.places.json"
GEO_JSON="${BASE}.places.geo.json"

if [[ -z "$OUT_FILE" ]]; then
  OUT_FILE="${OUTPUT_DIR}/${CITY}地图_博查版.html"
fi

echo "=============================================="
echo "  🏗️  地图生成管线: $CITY"
echo "  📄  Markdown: $MD_FILE"
echo "  🗺️  输出地图: $OUT_FILE"
echo "  📅  日期范围: ${DATE_RANGE:-未指定}"
echo "=============================================="

# ---- Step 1: extract_places.py ----
echo ""
echo "【Step 1/5】抽取地点..."
if [[ -f "$PLACES_JSON" ]]; then
  echo "  ⏭️  跳过: $PLACES_JSON 已存在"
else
  python "$SCRIPTS_DIR/extract_places.py" "$MD_FILE"
fi

# ---- Step 2: geocode.py ----
echo ""
echo "【Step 2/5】地理编码..."
if [[ -f "$GEO_JSON" ]]; then
  # 检查是否所有地点都已编码
  ALL_OK=$(python -c "
import json
with open('$GEO_JSON', encoding='utf-8') as f:
    data = json.load(f)
ok = sum(1 for p in data if p.get('geocoded'))
print('all' if ok == len(data) else f'{ok}/{len(data)}')
")
  if [[ "$ALL_OK" == "all" ]]; then
    echo "  ⏭️  跳过: $GEO_JSON 已全部编码"
  else
    echo "  🔄  部分未编码 ($ALL_OK),重新执行..."
    python "$SCRIPTS_DIR/geocode.py" "$PLACES_JSON" "$CITY"
  fi
else
  python "$SCRIPTS_DIR/geocode.py" "$PLACES_JSON" "$CITY"
fi

# ---- Step 3: clean_geojson.py (仅对当前文件) ----
echo ""
echo "【Step 3/5】清理地点..."
python -c "
import sys, json
sys.path.insert(0, '$SCRIPTS_DIR')
from clean_geojson import clean_geo
with open('$GEO_JSON', encoding='utf-8') as f:
    data = json.load(f)
cleaned = clean_geo('$GEO_JSON')
with open('$GEO_JSON', 'w', encoding='utf-8') as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)
print(f'  ✅ 清理完成: {len(data)}→{len(cleaned)}')
"

# ---- Step 4: inject.py ----
echo ""
echo "【Step 4/5】生成地图 HTML..."

# 清理旧地图文件(避免重复)
OLD_MAPS=$(ls "$OUTPUT_DIR"/*${CITY}*地图_博查版.html 2>/dev/null || true)
for old in $OLD_MAPS; do
  if [[ "$old" != "$OUT_FILE" ]]; then
    rm -f "$old"
    echo "  🗑️  清理旧地图: $old"
  fi
done

python "$SCRIPTS_DIR/inject.py" "$GEO_JSON" "$OUT_FILE" "$CITY" "$DATE_RANGE"

# ---- Step 5: validate_map.py ----
echo ""
echo "【Step 5/5】验证地图..."
VALIDATION_OUTPUT=$(python "$SCRIPTS_DIR/validate_map.py" "$OUT_FILE" 2>&1) || true
echo "$VALIDATION_OUTPUT"

if echo "$VALIDATION_OUTPUT" | grep -q "❌"; then
  echo ""
  echo "⚠️  验证发现问题,请检查以上输出"
  exit 1
fi

echo ""
echo "=============================================="
echo "  ✅ 地图生成完成!"
echo "  🗺️  $OUT_FILE"
echo "=============================================="
