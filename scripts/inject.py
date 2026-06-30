#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject.py — 把 geo.json 注入 map_panel.html 模板,生成最终地图 HTML。

用法:
  python inject.py <geo.json> <output.html> <城市> [日期范围]

示例:
  python inject.py "D:/fireclaw/杭州7月4-5日调查报告_博查版.places.geo.json" \
                   "D:/fireclaw/杭州7月4-5日地图_博查版.html" \
                   杭州 "2026/7/4-5"

环境变量(必填):
  AMAP_JS_KEY    高德「Web 端 JS API」类型的 Key(用于浏览器加载地图底图)
  AMAP_SECURITY  对应的安全密钥(2021-12-02 后申请的 Key 必须配置)

模板中的占位符会被替换:
  {{CITY}} {{DATE_RANGE}} {{TOTAL}}
  {{CENTER_LNG}} {{CENTER_LAT}} {{ZOOM}}
  {{PLACES_JSON}} {{AMAP_JS_KEY}} {{AMAP_SECURITY}}
"""
import json, os, sys, io, re, math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(SKILL_DIR, "templates", "map_panel.html")


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

# 城市中心坐标回退(仅当地点全无坐标时使用)
FALLBACK_CENTERS = {
    "北京": (116.4074, 39.9042, 11), "上海": (121.4737, 31.2304, 12),
    "广州": (113.2644, 23.1291, 12), "深圳": (114.0579, 22.5431, 12),
    "杭州": (120.1551, 30.2741, 12), "成都": (104.0657, 30.5723, 12),
    "重庆": (106.5516, 29.5630, 11), "武汉": (114.3055, 30.5928, 12),
    "西安": (108.9398, 34.3416, 12), "南京": (118.7969, 32.0603, 12),
    "苏州": (120.5853, 31.2989, 12), "天津": (117.1901, 39.1252, 11),
    "青岛": (120.3826, 36.0671, 12), "长沙": (112.9388, 28.2282, 12),
    "厦门": (118.0894, 24.4798, 12), "昆明": (102.8329, 24.8801, 12),
    "郑州": (113.6253, 34.7466, 12), "宁波": (121.5440, 29.8683, 12),
    "无锡": (120.3119, 31.4912, 12), "佛山": (113.1226, 23.0288, 12),
    "东莞": (113.7468, 23.0466, 12), "珠海": (113.5767, 22.2710, 12),
    "中山": (113.3927, 22.5176, 12), "惠州": (114.4153, 23.1115, 12),
    "汕头": (116.6822, 23.3535, 12), "江门": (113.0823, 22.5790, 12),
    "湛江": (110.3582, 21.2706, 12), "肇庆": (112.4658, 23.0469, 12),
    "阳江": (111.9821, 21.8579, 12), "茂名": (110.9192, 21.6630, 12),
    "清远": (113.0510, 23.6857, 11), "韶关": (113.5915, 24.8014, 11),
    "梅州": (116.1175, 24.2992, 11), "潮州": (116.6320, 23.6618, 12),
    "揭阳": (116.3729, 23.5497, 12), "云浮": (112.0444, 22.9151, 11),
    "河源": (114.6978, 23.7432, 11), "汕尾": (115.3759, 22.7868, 11),
    "南宁": (108.3669, 22.8170, 12), "桂林": (110.2902, 25.2736, 12),
    "柳州": (109.4282, 24.3260, 12), "北海": (109.1197, 21.4733, 12),
    "海口": (110.3312, 20.0317, 12), "三亚": (109.5083, 18.2473, 12),
    "贵阳": (106.7135, 26.5783, 12), "兰州": (103.8343, 36.0613, 12),
    "沈阳": (123.4290, 41.7968, 11), "哈尔滨": (126.5358, 45.8023, 11),
    "长春": (125.3235, 43.8171, 11), "太原": (112.5489, 37.8706, 12),
    "石家庄": (114.5149, 38.0428, 12), "济南": (117.0004, 36.6753, 12),
    "合肥": (117.2272, 31.8206, 12), "南昌": (115.8581, 28.6832, 12),
    "福州": (119.2965, 26.0745, 12), "拉萨": (91.1322, 29.6604, 12),
    "乌鲁木齐": (87.6168, 43.8256, 11), "银川": (106.2308, 38.4872, 12),
    "西宁": (101.7782, 36.6171, 12), "呼和浩特": (111.7510, 40.8414, 11),
    "金华": (119.6523, 29.1057, 12),
}


def _trimmed_midpoint(values, trim=0.1):
    """去除两端 trim 比例的离群值后取中点"""
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    k = max(1, int(n * trim))
    trimmed = s[k:-k] if k < n - k else s  # 保留至少2个
    return (trimmed[0] + trimmed[-1]) / 2


def _span(values):
    """坐标跨度(去除两端离群值后)"""
    if not values or len(values) < 3:
        return max(values) - min(values) if values else 0
    s = sorted(values)
    n = len(s)
    k = max(1, int(n * 0.1))
    trimmed = s[k:-k]
    return max(trimmed) - min(trimmed)


def compute_center(places, city):
    """从地点坐标自动计算地图中心(使用修剪中点,抗离群值),失败时回退到 FALLBACK_CENTERS"""
    lats = [p["lat"] for p in places if p.get("lat") and isinstance(p["lat"], (int, float))
            and 18 <= p["lat"] <= 55]
    lngs = [p["lng"] for p in places if p.get("lng") and isinstance(p["lng"], (int, float))
            and 73 <= p["lng"] <= 135]

    if lats and lngs:
        lat = _trimmed_midpoint(lats)
        lng = _trimmed_midpoint(lngs)
        # 根据坐标跨度(修剪后)自动缩放:跨度大 zoom 小,跨度小 zoom 大
        span = max(_span(lats), _span(lngs))
        if span < 0.05:
            zoom = 14
        elif span < 0.2:
            zoom = 13
        elif span < 0.5:
            zoom = 12
        elif span < 1.5:
            zoom = 11
        else:
            zoom = 10
        return lng, lat, zoom, "auto"
    else:
        # 回退到预置中心
        fallback = FALLBACK_CENTERS.get(city)
        if fallback:
            lng, lat, zoom = fallback
            print(f"   ⚠️  地点无坐标,使用预设中心 {city}: {lng},{lat}")
            return lng, lat, zoom, "fallback"
        else:
            # 真回退:北京
            print(f"   ⚠️  城市「{city}」无预设中心且地点无坐标,临时用北京中心")
            return 116.4074, 39.9042, 11, "default"


def main():
    if len(sys.argv) < 4:
        print("用法: python inject.py <geo.json> <output.html> <城市> [日期范围]")
        print('示例: python inject.py report.geo.html map.html 杭州 "2026/7/4-5"')
        sys.exit(1)

    geo_path = sys.argv[1]
    out_path = sys.argv[2]
    city = sys.argv[3]
    date = sys.argv[4] if len(sys.argv) > 4 else ""

    js_key = os.environ.get("AMAP_JS_KEY", "").strip()
    security = os.environ.get("AMAP_SECURITY", "").strip()
    if not js_key or not security:
        print("❌ 未配置 AMAP_JS_KEY / AMAP_SECURITY 环境变量")
        print()
        print("inject.py 需要高德「Web 端 JS API」Key + 对应的安全密钥。")
        print("申请地址:https://console.amap.com/dev/key/app(应用类型选「Web 端(JS API)」)")
        print("安全密钥:与 JS API Key 配套生成,在 Key 详情页可见")
        print()
        print("配置方式(bash/git-bash):")
        print('  export AMAP_JS_KEY="你的JS_API_Key"')
        print('  export AMAP_SECURITY="你的安全密钥"')
        print("配置方式(Windows PowerShell):")
        print('  $env:AMAP_JS_KEY="你的JS_API_Key"')
        print('  $env:AMAP_SECURITY="你的安全密钥"')
        sys.exit(2)

    if not os.path.exists(geo_path):
        print(f"错误: 文件不存在 {geo_path}")
        sys.exit(1)
    if not os.path.exists(TPL):
        print(f"错误: 模板不存在 {TPL}")
        sys.exit(1)

    with open(TPL, encoding="utf-8") as fp:
        html = fp.read()
    with open(geo_path, encoding="utf-8") as fp:
        places = json.load(fp)

    lng, lat, zoom, center_source = compute_center(places, city)

    # 防御性过滤:标记坐标偏离城市中心 >3° 的点为未编码(避免错误城市坐标显示在地图上)
    outlier_count = 0
    for p in places:
        if p.get("geocoded") and isinstance(p.get("lat"), (int, float)) and isinstance(p.get("lng"), (int, float)):
            if abs(p["lat"] - lat) > 3 or abs(p["lng"] - lng) > 3:
                p["geocoded"] = False
                p["geocode_status"] = f"outlier:{p['lat']:.4f},{p['lng']:.4f}"
                outlier_count += 1

    total = len(places)
    geocoded = sum(1 for p in places if p.get("lat") and p.get("lng")
                   and not (isinstance(p.get("lat"), float) and math.isnan(p["lat"])))

    html = html.replace("{{CITY}}", city)
    html = html.replace("{{DATE_RANGE}}", date)
    html = html.replace("{{TOTAL}}", f"{geocoded}/{total}")
    html = html.replace("{{CENTER_LNG}}", str(lng))
    html = html.replace("{{CENTER_LAT}}", str(lat))
    html = html.replace("{{ZOOM}}", str(zoom))
    html = html.replace("{{PLACES_JSON}}", json.dumps(places, ensure_ascii=False))
    html = html.replace("{{AMAP_JS_KEY}}", js_key)
    html = html.replace("{{AMAP_SECURITY}}", security)

    # 检查是否有未替换的模板占位符
    remaining = re.findall(r'\{\{.*?\}\}', html)
    if remaining:
        print(f"   ⚠️  发现未替换的模板占位符: {remaining}")

    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write(html)

    print(f"✅ {out_path}")
    print(f"   地点: {total} 个 (预编码成功: {geocoded})")
    if outlier_count:
        print(f"   ⚠️  偏离中心移除: {outlier_count} 个")
    print(f"   城市: {city} 中心: {lng:.4f},{lat:.4f} zoom={zoom} (来源: {center_source})")
    if total - geocoded > 0:
        print(f"   ⚠️  {total - geocoded} 个无坐标(在地图上会隐藏)")


if __name__ == "__main__":
    main()
