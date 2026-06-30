#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clean_geojson.py — 用 LLM (bocha DeepSeek-V4) 清理 geo.json 中的非地点条目
移除:食物名/活动名/描述/重复项,修复坐标,补充已知坐标

LLM API: POST https://api.bocha.cn/v1/chat/completions
模型: deepseek-v4-flash
环境变量: BOCHA_API_KEY (与博查搜索 API 共用)
"""
import json, glob, os, re, sys, io, urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COORDS_PATH = os.path.join(SKILL_DIR, "scripts", "known_coords.json")


def _load_dotenv():
    """简易 .env 文件加载: 查找 SKILL_DIR/.env 和 工作目录/.env,已设置的环境变量不覆盖"""
    candidates = [
        os.path.join(SKILL_DIR, ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for env_path in candidates:
        if not os.path.isfile(env_path):
            continue
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass


_load_dotenv()

with open(COORDS_PATH, encoding="utf-8") as f:
    KNOWN_COORDS = json.load(f)

BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY", "").strip()
LLM_URL = "https://api.bocha.cn/v1/chat/completions"
LLM_MODEL = "deepseek-v4-flash"
BATCH_SIZE = 25  # 每批送 LLM 判断的名称数


# ── 句法级预过滤(不是内容判断,保留) ──
SYNTAX_REMOVE = [
    re.compile(r'→'), re.compile(r'➡'),         # 路线箭头
    re.compile(r'^图:'),                           # 图片说明
    re.compile(r'^购票平台'),                       # 购票
    re.compile(r'^(准考证|考生)'),                  # 证件
    re.compile(r'^(必吃|必逛|出片)'),               # 推荐标签
    re.compile(r'末班车'),                          # 末班车
    re.compile(r'^\d+条线路$'),                    # 线路统计
    re.compile(r'^[A-Z]\d{4}$'),                   # 车次号
    re.compile(r'^Day\s*\d+', re.I),               # Day 1
    re.compile(r'^\d{1,2}$'),                      # 纯数字
    re.compile(r'^[A-Z\d]\s*出口'),                # B出口
    re.compile(r'^[\d\- ]+号线'),                  # 1号线
    re.compile(r'^\d+条线路$'),                    # 9条线路
    re.compile(r'^(已开通|已运营)'),                # 已开通
    re.compile(r'^\d{1,2}\.\d{1,2}'),              # 7.18 日期
    re.compile(r'^\d{4}-\d{2}-\d{2}'),             # 2026-07-18
    re.compile(r'周一闭馆'),                        # 周一闭馆
    re.compile(r'^[①②③④⑤⑥⑦⑧⑨⑩]$'),            # 序号单字符
]


def prefilter(name):
    """句法级预过滤: 返回 True 表示应移除"""
    if not name or len(name) > 60:
        return True
    for pat in SYNTAX_REMOVE:
        if pat.search(name):
            return True
    return False


def needs_rename_from_addr(name, addr):
    """名字是日期/数字,address才是真地点"""
    if not addr:
        return False
    if re.match(r'^\d{1,2}\.\d{1,2}', name):
        return True
    if re.match(r'^\d{1,2}$', name) and addr != name:
        return True
    if re.match(r'^\d+[/]\d+', name):
        return True
    return False


def llm_classify_batch(names, city=""):
    """
    调用 bocha LLM API 批量判断名称是否为真实地理位置
    返回 {(name: True/False), ...} — True=是地点,保留
    """
    if not BOCHA_API_KEY or not names:
        # 无 API key 时全部保留(安全侧)
        return {n: True for n in names}

    system_prompt = (
        "你是城市旅游地点分类助手。判断以下名称是否为可以在地图上标注的"
        "真实地理位置——比如景点、商场、博物馆、餐厅、公园、地铁站、"
        "街道、集市、夜市、演出场馆、体育场馆等。\n"
        "排除以下类型(不是地理位置):\n"
        "- 食物名称(如'锅包肉''金华火腿''小锅米线')\n"
        "- 活动/演出名称(如'草地音乐节''2026南京艺术节')\n"
        "- 描述性/广告文案(如'必吃7家''出片机位''景区电话')\n"
        "- 统计数据(如'核心景区日均客流')\n"
        "- 路线描述(含→或➡)\n\n"
        "以JSON数组格式回答(不要加markdown代码块标记):\n"
        '[{"name":"...","is_place":true,"reason":"...对真实地点的简要说明"}, ...]'
    )

    user_content = json.dumps(names, ensure_ascii=False)
    if city:
        user_content = f"城市: {city}\n名称列表: {user_content}"

    body = json.dumps({
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.0,
        "max_tokens": 2048,
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        LLM_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {BOCHA_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️  LLM API 调用失败: {e}, 全部保留")
        return {n: True for n in names}

    try:
        reply = result["choices"][0]["message"]["content"]
        # 去掉可能的 markdown 代码块标记
        reply = re.sub(r'^```(?:json)?\s*', '', reply)
        reply = re.sub(r'\s*```$', '', reply)
        classifications = json.loads(reply)
        return {item["name"]: item.get("is_place", True) for item in classifications}
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"  ⚠️  LLM 响应解析失败: {e}, 全部保留")
        return {n: True for n in names}


def llm_filter(places, city=""):
    """
    对 places 列表中未通过预过滤的项目做 LLM 分类
    返回过滤后的列表(移除非地点)
    """
    # 收集需要 LLM 判断的条目
    to_check = []
    kept = []
    for p in places:
        name = p["name"]
        if prefilter(name):
            continue  # 句法过滤移除
        to_check.append(p)

    if not to_check:
        return [p for p in places if not prefilter(p["name"])]

    # 分批送 LLM
    classifications = {}
    for i in range(0, len(to_check), BATCH_SIZE):
        batch = to_check[i:i + BATCH_SIZE]
        names = [p["name"] for p in batch]
        results = llm_classify_batch(names, city=city)
        classifications.update(results)

    # 保留 LLM 判定为地点的
    for p in to_check:
        if classifications.get(p["name"], True):
            kept.append(p)

    return kept


def clean_geo(gf):
    city = ""
    with open(gf, encoding='utf-8') as f:
        places = json.load(f)

    # Step 1: 句法预过滤 + needs_rename + 演出名处理
    pre_keep = []
    llm_candidates = []

    for p in places:
        name = p["name"]
        addr = p.get("address", "")

        if prefilter(name):
            continue

        # 日期/序号→用地址改名
        if needs_rename_from_addr(name, addr):
            new_name = addr.split("(")[0].split(" ")[0].strip()
            new_name = re.sub(r'[🏆⭐🌟✨]', "", new_name).strip()
            if new_name and len(new_name) >= 2:
                p["name"] = new_name
                pre_keep.append(p)
            continue

        # 演出名(C类型)→用场馆地址
        if p["type"] == "C" and not any(w in name for w in ["馆", "场", "中心", "公园", "体育", "剧院"]):
            if addr and any(w in addr for w in ["馆", "场", "中心", "公园", "体育", "剧院"]):
                orig_note = p.get("note", "")
                p["name"] = addr
                p["note"] = name + (" | " + orig_note if orig_note else "")
                pre_keep.append(p)
                continue
            else:
                continue

        # 清理 emoji
        name_clean = re.sub(r'[🏆⭐🌟✨]', "", name).strip()
        p["name"] = name_clean

        # 补充已知坐标
        if not p.get("geocoded"):
            matched = False
            for sn in [name_clean, name_clean + "公园", name_clean.split("(")[0]]:
                if sn in KNOWN_COORDS:
                    coords = KNOWN_COORDS[sn]
                    p["lat"], p["lng"] = coords[1], coords[0]
                    p["level"] = "兴趣点"
                    p["geocoded"] = True
                    if "geocode_status" in p:
                        del p["geocode_status"]
                    matched = True
                    break

        llm_candidates.append(p)

    # Step 2: LLM 内容过滤
    if llm_candidates:
        city = os.path.basename(gf).split("未来")[0].strip()
        kept = llm_filter(llm_candidates, city=city)
    else:
        kept = []

    combined = pre_keep + kept

    # Step 3: 去重
    seen = set()
    deduped = []
    for p in combined:
        key = (p["name"], p["type"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    # 重新编号
    counters = {}
    for p in deduped:
        t = p["type"]
        counters[t] = counters.get(t, 0) + 1
        p["id"] = f"{t}{counters[t]:03d}"

    return deduped


if __name__ == "__main__":
    total_before, total_after = 0, 0
    total_ok_before, total_ok_after = 0, 0

    for gf in sorted(glob.glob("D:/fireclaw/*.geo.json")):
        with open(gf, encoding="utf-8") as f:
            before = json.load(f)
        before_ok = sum(1 for p in before if p.get("geocoded"))
        before_count = len(before)

        cleaned = clean_geo(gf)
        after_ok = sum(1 for p in cleaned if p.get("geocoded"))
        after_count = len(cleaned)

        total_before += before_count
        total_after += after_count
        total_ok_before += before_ok
        total_ok_after += after_ok

        if before_count != after_count or before_ok != after_ok:
            with open(gf, "w", encoding="utf-8") as f:
                json.dump(cleaned, f, ensure_ascii=False, indent=2)
            name = os.path.basename(gf)
            print(f"✅ {name}")
            print(f"   数量: {before_count}→{after_count}, 编码: {before_ok}→{after_ok}")
        else:
            print(f"⏭️  {os.path.basename(gf)} — 无变化")

    print(f"\n=== 汇总 ===")
    print(f"总数: {total_before}→{total_after}")
    print(f"编码成功: {total_ok_before}→{total_ok_after}")

    for gf in sorted(glob.glob("D:/fireclaw/*.geo.json")):
        with open(gf, encoding="utf-8") as f:
            data = json.load(f)
        fail = sum(1 for p in data if not p.get("geocoded"))
        if fail > 0:
            names = [p["name"][:20] for p in data if not p.get("geocoded")]
            print(f'\n⚠️ {os.path.basename(gf)}: {fail} failed → {", ".join(names)}')
