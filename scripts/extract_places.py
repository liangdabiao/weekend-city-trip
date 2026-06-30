#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_places.py — LLM only 版

直接把完整 Markdown 报告发给 LLM，由 LLM 提取地点。
没有任何规则解析。

LLM: bocha DeepSeek-V4 Flash API
环境变量: BOCHA_API_KEY

使用:
  python extract_places.py "D:/fireclaw/杭州7月4-5日调查报告_博查版.md"
"""
import json, os, sys, io, re, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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

BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY", "").strip()
LLM_URL = "https://api.bocha.cn/v1/chat/completions"
LLM_MODEL = "deepseek-v4-flash"


def extract_places(md_path):
    with open(md_path, encoding="utf-8") as fp:
        content = fp.read()

    # 从文件名推断城市名
    city = os.path.basename(md_path).split("未来")[0].split("7月")[0].split("调查报告")[0].strip()
    if not city:
        city = os.path.basename(md_path).split("_")[0].strip()

    system_prompt = (
        "你是城市旅游地点提取助手。从完整的Markdown调研报告中提取所有可以在地图上标注的地点。\n\n"
        "11种类型代码:\n"
        "C=演唱会, S=球赛, M=集市, U=博物馆/展览, 5=景区/公园/景点,\n"
        "H=喜茶门店, F=美食街/餐厅, W=City Walk/步行路线节点,\n"
        "L=购物中心/商场, D=地铁站/公交站/火车站/机场, T=优惠门票\n\n"
        "提取规则:\n"
        "1. 报告中表格的行都要提取，但注意:\n"
        "   - 如果首列是活动名(如'2026大连啤酒嘉年华'、'东北超足球联赛')，"
        "取实际场地(如'星海湾'、'大连梭鱼湾足球场')作为地点名\n"
        "   - 活动信息放入 note\n"
        "2. name = 实际地点名(可在地图上搜索到的)\n"
        "3. address = 地址信息(用于地理编码)，无则空字符串\n"
        "4. note = 活动时间、价格、推荐理由等描述信息\n"
        "5. skip = true 排除: 纯食物名('海胆''铁板鱿鱼')、纯城市名('大连')、"
        "统计数据、路线描述(含→)、广告文案\n\n"
        "以JSON数组格式回答(不要markdown代码块标记):\n"
        '[{"name":"...","type":"5","address":"...","note":"...","section":"...","skip":false}]'
    )

    user_content = f"城市: {city}\n\n完整报告内容:\n```markdown\n{content}\n```"

    body = json.dumps({
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.0,
        "max_tokens": 8192,
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        LLM_URL, data=body,
        headers={
            "Authorization": f"Bearer {BOCHA_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        reply = result["choices"][0]["message"]["content"]
        reply = re.sub(r'^```(?:json)?\s*', '', reply)
        reply = re.sub(r'\s*```$', '', reply)
        places = json.loads(reply)
    except Exception as e:
        print(f"❌ LLM 调用失败: {e}")
        sys.exit(1)

    # 过滤 skip=true
    places = [p for p in places if not p.get("skip", False)]

    # 去重 (name+type)
    seen = set()
    deduped = []
    counters = {}
    for p in places:
        name = p.get("name", "").strip()
        if not name:
            continue
        p_type = p.get("type", "5")
        key = (name, p_type)
        if key in seen:
            continue
        seen.add(key)
        counters[p_type] = counters.get(p_type, 0) + 1
        deduped.append({
            "id": f"{p_type}{counters[p_type]:03d}",
            "name": name,
            "type": p_type,
            "address": p.get("address", "").strip(),
            "note": (p.get("note", "") or "").strip()[:200],
            "section": p.get("section", ""),
        })

    return deduped


def main():
    if len(sys.argv) < 2:
        print("用法: python extract_places.py <markdown_report.md> [output.json]")
        sys.exit(1)

    md_path = sys.argv[1]
    if not os.path.exists(md_path):
        print(f"错误: 文件不存在 {md_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        out_path = sys.argv[2]
    else:
        base, _ = os.path.splitext(md_path)
        out_path = base + ".places.json"

    if not BOCHA_API_KEY:
        print("❌ 必须设置环境变量 BOCHA_API_KEY")
        sys.exit(1)

    print(f"📖 读取: {md_path}")
    print(f"🤖 LLM: {LLM_MODEL} (全文提取)")

    places = extract_places(md_path)

    stats = {}
    for p in places:
        stats[p["type"]] = stats.get(p["type"], 0) + 1

    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(places, fp, ensure_ascii=False, indent=2)

    print(f"\n✅ 抽取完成: {len(places)} 个地点")
    print(f"📁 输出: {out_path}")
    print("📊 分类统计:")
    type_names = {
        "C": "演唱会", "S": "球赛", "M": "集市", "U": "博物馆",
        "5": "5A景区", "H": "喜茶", "F": "美食街", "W": "City Walk",
        "L": "购物中心", "D": "地铁站", "T": "优惠门票"
    }
    for code in ["C", "S", "M", "U", "5", "H", "F", "W", "L", "D", "T"]:
        if code in stats:
            print(f"   {type_names[code]:8s} ({code}): {stats[code]} 个")


if __name__ == "__main__":
    import re
    main()
