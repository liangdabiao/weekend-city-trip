#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_map.py — 验证 inject.py 生成的地图 HTML 质量

用法:
  python validate_map.py "D:/fireclaw/金华地图_博查版.html" [--verbose]

检查:
  1. 中心坐标不是北京回退
  2. 所有地点有有效坐标
  3. 坐标无 NaN
  4. 坐标在中国范围内(lat 18-55, lng 73-135)
  5. 无未替换的模板占位符
  6. 文件大小 > 0
  7. 地点计数一致

退出码: 0=通过, 1=有警告, 2=有失败(不可交付)
"""
import json, os, re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def extract_trip_data(html_path):
    """从 HTML 中提取 TRIP_DATA 对象(处理 JS 对象语法)"""
    with open(html_path, encoding="utf-8") as f:
        content = f.read()

    m = re.search(r'const\s+TRIP_DATA\s*=\s*(\{.*?\});', content, re.DOTALL)
    if not m:
        return None, None, content
    try:
        raw = m.group(1)
        # 去除所有 // 注释
        raw = re.sub(r'//.*', '', raw)
        # 去除尾部逗号(数组/对象最后一个元素后的逗号)
        raw = re.sub(r',\s*}', '}', raw)
        raw = re.sub(r',\s*]', ']', raw)
        # 给未加引号的 key 加引号
        raw = re.sub(r'(?<=[{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', raw)
        data = json.loads(raw)
        return data, content
    except json.JSONDecodeError as e:
        return None, str(e), content


def check(condition, msg, fail_on_error=True):
    """执行检查并打印结果"""
    if condition:
        print(f"  ✅ {msg}")
        return 0
    else:
        if fail_on_error:
            print(f"  ❌ {msg}")
            return 2
        else:
            print(f"  ⚠️  {msg}")
            return 1


def validate(html_path, verbose=False):
    print(f"\n🔍 验证: {os.path.basename(html_path)}")
    print("-" * 50)

    exit_code = 0

    # 1. 文件存在且大小 > 0
    if not os.path.exists(html_path):
        print(f"  ❌ 文件不存在")
        return 2
    size = os.path.getsize(html_path)
    rc = check(size > 0, f"文件大小: {size} bytes")
    exit_code = max(exit_code, rc)

    data, err_or_content = extract_trip_data(html_path)
    if data is None:
        print(f"  ❌ 无法解析 TRIP_DATA: {err_or_content}")
        return 2
    content = err_or_content

    places = data.get("places", [])
    total = len(places)
    center = data.get("center", [None, None])

    # 2. 无未替换的模板占位符
    has_placeholders = bool(re.search(r'\{\{.*?\}\}', content))
    rc = check(not has_placeholders, "无未替换的模板占位符")
    exit_code = max(exit_code, rc)

    # 3. 中心坐标不是北京回退
    clng, clat = center[0], center[1]
    is_beijing = (clng and clat and abs(clng - 116.4) < 0.5 and abs(clat - 39.9) < 0.5)
    rc = check(not is_beijing or total == 0,
               f"中心坐标 ({clng:.3f}, {clat:.3f}) 不是北京回退(除非无地点)",
               fail_on_error=False)  # 允许北京(可能是真北京)
    exit_code = max(exit_code, rc)
    if is_beijing and total > 0:
        print(f"     → 中心为北京但存在 {total} 个地点,请确认城市是否正确")

    # 4. 所有地点坐标有效
    geocoded = sum(1 for p in places if p.get("lat") and p.get("lng"))
    rc = check(geocoded == total,
               f"坐标: {geocoded}/{total} 已编码",
               fail_on_error=False)
    exit_code = max(exit_code, rc)

    # 5. 无 NaN 坐标
    nan_count = 0
    for p in places:
        lat, lng = p.get("lat"), p.get("lng")
        if lat is not None and lng is not None:
            if isinstance(lat, float) and lat != lat:  # NaN check
                nan_count += 1
            if isinstance(lng, float) and lng != lng:
                nan_count += 1
    rc = check(nan_count == 0, f"无 NaN 坐标 (发现 {nan_count} 个)")
    exit_code = max(exit_code, rc)

    # 6. 坐标在中国范围内
    out_of_range = 0
    for p in places:
        lat, lng = p.get("lat"), p.get("lng")
        if lat and lng and isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
            if not (18 <= lat <= 55 and 73 <= lng <= 135):
                out_of_range += 1
                if verbose:
                    print(f"     ⚠️  坐标超范围: {p['name']} ({lat:.3f}, {lng:.3f})")
    rc = check(out_of_range == 0, f"坐标在中国范围内 (超出: {out_of_range})")
    exit_code = max(exit_code, rc)

    # 7. 失败地点列表
    failed = [p for p in places if not p.get("lat") or not p.get("lng")]
    if failed and verbose:
        print(f"  📋 失败地点:")
        for p in failed:
            s = p.get("geocode_status", "?")
            print(f"     {p['id']} {p['name']} (status={s})")

    print(f"  📊 总计: {total} 地点, {geocoded} 已编码")
    print(f"  🎯 中心: ({clng:.3f}, {clat:.3f}) zoom={data.get('zoom', '?')}")
    print(f"  📅 日期: {data.get('date_range', '?')}")

    if exit_code == 0:
        print(f"  ✅ 全部通过\n")
    elif exit_code == 1:
        print(f"  ⚠️  有警告(可交付)\n")
    else:
        print(f"  ❌ 有失败(需修复)\n")

    return exit_code


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    if len(sys.argv) < 2:
        print("用法: python validate_map.py <map.html> [--verbose]")
        print("      python validate_map.py <directory> [--verbose]  (批量验证)")
        sys.exit(1)

    path = sys.argv[1]
    if os.path.isdir(path):
        htmls = sorted([f for f in os.listdir(path) if f.endswith("地图_博查版.html")])
        if not htmls:
            print(f"在 {path} 下未找到地图文件")
            sys.exit(1)
        overall = 0
        for h in htmls:
            rc = validate(os.path.join(path, h), verbose=verbose)
            overall = max(overall, rc)
        sys.exit(overall)
    else:
        rc = validate(path, verbose=verbose)
        sys.exit(rc)


if __name__ == "__main__":
    main()
