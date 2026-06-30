#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geocode.py — 批量调用高德地理编码 API,为 places.json 中每个地点补充
经纬度(lat/lng,GCJ-02 坐标系),输出同名 .geo.json。

改进:
  - known_coords.json 回退:知名地点直接写入,省 API 配额
  - query 清洗:去 emoji/括号说明再查(提高命中率)
  - QPS 自适应:遇到 CUQPS_HAS_EXCEEDED_THE_LIMIT 自动降速重试

输入:places.json 路径(extract_places.py 生成)
输出:同名 .geo.json

使用:
  python geocode.py "D:/fireclaw/杭州7月4-5日调查报告_博查版.places.json" 杭州

环境变量:
  AMAP_KEY=你的高德 Web 服务 Key(必填)
"""
import json, os, sys, io, time, re
import urllib.parse, urllib.request

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

AMAP_KEY = os.environ.get("AMAP_KEY", "").strip()
GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
QPS_DELAY = 0.15  # ~7 QPS,留余量
TIMEOUT = 8
RETRY = 3

# 加载已知坐标(单源)
with open(COORDS_PATH, encoding="utf-8") as f:
    KNOWN_COORDS = json.load(f)  # {name: [lng, lat]}

# 多城市共有的地名 — known_coords 命中时需跳过(否则可能返回错误城市坐标)
AMBIGUOUS_NAMES = frozenset({
    "开元寺", "西湖", "东山湖", "中山公园", "人民公园",
    "古城", "博物馆", "老街", "步行街", "百花洲",
    "东湖", "南湖", "北海", "西山", "南山",
})


def clean_query(name):
    """清洗名称:去 emoji、括号说明、多余空格"""
    name = re.sub(r'[🏆⭐🌟✨💥🔴🟠🟡🟢🔵🟣🟤❤️🔥]', '', name)
    name = re.sub(r'[\U0001F300-\U0001FAFF\u2600-\u27BF]', '', name)
    name = re.sub(r'\(\d+\)$', '', name)
    name = re.sub(r'\(\d+h车程\)$', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def lookup_known(name, city=""):
    """
    检查已知坐标,返回 (lat, lng, level) 或 None
    当 city 参数传入且 name 在多城市共有列表中时,跳过 known_coords 匹配,
    强制走 AMAP 查询(避免返回错误城市的坐标)。
    KNOWN_COORDS 存储格式是 [lng, lat],这里返回 (lat, lng)
    """
    def _is_ambiguous(n):
        return bool(city and n in AMBIGUOUS_NAMES)

    if name in KNOWN_COORDS and not _is_ambiguous(name):
        c = KNOWN_COORDS[name]
        return c[1], c[0], '兴趣点'
    base = name.split('(')[0].strip()
    if base != name and base in KNOWN_COORDS and not _is_ambiguous(base):
        c = KNOWN_COORDS[base]
        return c[1], c[0], '兴趣点'
    return None


def _amap_request(params):
    """发送 AMAP 请求,返回 (geocodes_list, status_str) 或 (None, info_str) 出错。"""
    url = GEOCODE_URL + "?" + urllib.parse.urlencode(params)
    for attempt in range(RETRY + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") != "1":
                info = data.get("info", "")
                if "QPS" in info.upper() and attempt < RETRY:
                    time.sleep(2.0 * (attempt + 1))
                    continue
                if attempt < RETRY:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                return None, info
            return (data.get("geocodes") or []), "ok"
        except Exception as e:
            if attempt < RETRY:
                time.sleep(0.5 * (attempt + 1))
                continue
            return None, f"err:{e}"
    return None, "retry_exhausted"


def _city_matches(returned_city, target_city):
    """检查 AMAP 返回的城市是否匹配目标城市"""
    if not target_city or not returned_city:
        return True
    if target_city in returned_city or returned_city in target_city:
        return True
    r = returned_city.replace("市", "")
    t = target_city.replace("市", "")
    return r == t


def _coords_in_china(lat, lng):
    """粗略检查坐标是否在中国范围内"""
    return 18 <= lat <= 55 and 73 <= lng <= 135


def geocode_one(name, city=""):
    """
    调用高德地理编码 API,返回 (lat, lng, level, status)

    Layer A: lookup_known 跳过多城市共有的地名
    Layer B: AMAP 响应 city 字段验证
    Layer C: 坐标范围合理性检查
    """

    # Layer A: known_coords 检查(带城市过滤)
    known = lookup_known(name, city=city)
    if known:
        return *known, "known_coords"

    clean_name = clean_query(name)
    if not clean_name:
        clean_name = name

    # 第一次查询 - 标准 query
    params = {
        "key": AMAP_KEY,
        "address": clean_name,
        "output": "JSON",
    }
    if city:
        params["city"] = city

    geocodes, status = _amap_request(params)
    if geocodes is None:
        return None, None, None, status

    if geocodes:
        g = geocodes[0]
        location = g.get("location", "")
        returned_city = g.get("city", "") or ""
        returned_district = g.get("district", "") or ""

        # Layer B: 验证返回的城市是否匹配目标城市
        if city and returned_city and not _city_matches(returned_city, city):
            # 城市不匹配 → 用更具体的 query 重试(城市名 + 区 + 名称)
            specific_query = clean_name
            if returned_district and returned_district not in specific_query:
                specific_query = f"{city}{returned_district}{clean_name}"
            else:
                specific_query = f"{city}{clean_name}"

            params2 = {
                "key": AMAP_KEY,
                "address": specific_query,
                "output": "JSON",
            }
            if city:
                params2["city"] = city

            geocodes2, status2 = _amap_request(params2)
            if geocodes2 is not None and geocodes2:
                g2 = geocodes2[0]
                location2 = g2.get("location", "")
                returned_city2 = g2.get("city", "") or ""
                if _city_matches(returned_city2, city) and "," in location2:
                    lng2, lat2 = location2.split(",")
                    lat_f = float(lat2)
                    lng_f = float(lng2)
                    if _coords_in_china(lat_f, lng_f):
                        return lat_f, lng_f, g2.get("level", ""), "ok"

            # 重试仍不匹配 → 拒绝
            return None, None, None, f"city_mismatch:{returned_city}"

        if "," not in location:
            return None, None, None, "no_location"
        lng, lat = location.split(",")
        lat_f = float(lat)
        lng_f = float(lng)

        # Layer C: 坐标范围检查
        if not _coords_in_china(lat_f, lng_f):
            return None, None, None, f"out_of_range:{lat_f},{lng_f}"

        return lat_f, lng_f, g.get("level", ""), "ok"

    return None, None, None, "no_match"


def main():
    if not AMAP_KEY:
        print("❌ 未配置 AMAP_KEY 环境变量")
        print("申请: https://console.amap.com/dev/key/app (类型选「Web 服务」)")
        print('  export AMAP_KEY="sk-..."')
        sys.exit(2)

    if len(sys.argv) < 2:
        print("用法: python geocode.py <places.json> [城市名]")
        sys.exit(1)

    in_path = sys.argv[1]
    if not os.path.exists(in_path):
        print(f"错误: 文件不存在 {in_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        city = sys.argv[2]
    else:
        base = os.path.basename(in_path)
        m = ""
        for ch in base:
            if "\u4e00" <= ch <= "\u9fff":
                m += ch
            elif m:
                break
        city = m[:6] if m else ""

    with open(in_path, encoding="utf-8") as fp:
        places = json.load(fp)

    print(f"📍 城市: {city or '(未指定)'}")
    print(f"📦 地点总数: {len(places)}")
    if os.environ.get("VERBOSE", "").lower() in ("1", "true", "yes"):
        print(f"🔑 Key: {AMAP_KEY[:8]}...{AMAP_KEY[-4:]}")
    print(f"⏱️  预计耗时: {len(places) * QPS_DELAY:.1f}s")
    print("-" * 60)

    ok, fail, known_hit = 0, 0, 0
    for i, p in enumerate(places, 1):
        known = lookup_known(p["name"], city=city)
        if known:
            p["lat"], p["lng"], p["level"] = known
            p["geocoded"] = True
            known_hit += 1
            ok += 1
            print(f"[{i:>3}/{len(places)}] 📖 {p['type']}-{p['name'][:18]:<18} → known_coords")
            continue

        query = p.get("address") or p["name"]
        query = clean_query(query)
        if city and city not in query:
            query = f"{city}{query}"

        lat, lng, level, status = geocode_one(query, city=city)

        if lat is not None:
            p["lat"] = lat
            p["lng"] = lng
            p["level"] = level
            p["geocoded"] = True
            ok += 1
            mark = "✅"
        else:
            p["lat"] = None
            p["lng"] = None
            p["level"] = ""
            p["geocoded"] = False
            p["geocode_status"] = status
            fail += 1
            mark = "❌"

        coord_str = f"{lat:.4f}, {lng:.4f}" if lat else status
        print(f"[{i:>3}/{len(places)}] {mark} {p['type']}-{p['name'][:18]:<18} → {coord_str}")

        if i < len(places):
            time.sleep(QPS_DELAY)

    base, _ = os.path.splitext(in_path)
    out_path = base + ".geo.json"
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(places, fp, ensure_ascii=False, indent=2)

    print("-" * 60)
    print(f"✅ 编码成功: {ok} 个(含已知坐标 {known_hit} 个)")
    print(f"❌ 编码失败: {fail} 个")
    print(f"📁 输出: {out_path}")

    if fail > 0:
        print("\n⚠️ 失败地点:")
        for p in places:
            if not p.get("geocoded"):
                print(f"   {p['id']} {p['name']} (status={p.get('geocode_status','?')})")


if __name__ == "__main__":
    main()
