import os, re, sys

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

DEFAULT_DIR = os.environ.get("BOCHA_OUTPUT_DIR", "D:/fireclaw")
REPORT_SUFFIX = "调查报告_博查版.html"
MAP_SUFFIX = "地图_博查版.html"


def extract_city(filename):
    """从报告文件名中提取城市名，通用策略：取开头到第一个日期/时间关键词之前"""
    base = filename.replace(REPORT_SUFFIX, "")

    date_patterns = [
        r'未来一个月', r'下周末', r'本周末', r'近期', r'中秋', r'国庆', r'春节',
        r'\d+月\d+[-\~]\d+日', r'\d+月', r'\d+月\d+日', r'第\d+周',
    ]
    pattern = '|'.join(date_patterns)
    m = re.search(pattern, base)
    if m:
        city = base[:m.start()]
    else:
        city = base

    for suffix in ['下周末', '本周末', '近期', '未来']:
        if city.endswith(suffix):
            city = city[:-len(suffix)]
            break

    return city.strip()


def get_priority(filename):
    if '未来一个月' in filename:
        return 5
    elif '中秋' in filename:
        return 4
    elif '下周末' in filename:
        return 3
    elif '月' in filename and '日' in filename:
        return 2
    elif '近期' in filename:
        return 1
    return 0


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(data_dir, 'index.html')

    if not os.path.isdir(data_dir):
        print(f"❌ 目录不存在: {data_dir}")
        sys.exit(1)

    reports = []
    map_files = {}

    for f in os.listdir(data_dir):
        if f.endswith(MAP_SUFFIX):
            map_files[f] = True

    for f in sorted(os.listdir(data_dir)):
        if not f.endswith(REPORT_SUFFIX):
            continue
        city = extract_city(f)

        map_file = ''
        for mf in map_files:
            if mf.startswith(city):
                map_file = mf
                break

        priority = get_priority(f)

        reports.append({
            'city': city,
            'report': f,
            'map': map_file,
            'priority': priority
        })

    seen = {}
    for r in reports:
        base = r['city']
        for suffix in ['下周末', '本周末', '近期']:
            if base.endswith(suffix):
                base = base[:-len(suffix)]
                break
        if base not in seen or r['priority'] > seen[base]['priority']:
            r['city'] = base
            seen[base] = r
        elif r['priority'] == seen[base]['priority']:
            if r['map'] and not seen[base]['map']:
                seen[base] = r
    reports = list(seen.values())

    regions = {
        '华东': ['上海', '南京', '苏州', '无锡', '常州', '宁波', '杭州', '温州', '嘉兴', '金华', '绍兴', '合肥', '济南', '青岛', '徐州', '烟台', '南通', '泉州', '厦门', '福州'],
        '华南': ['深圳', '广州', '东莞', '佛山', '中山', '珠海', '海口', '南宁', '江门'],
        '华北': ['北京', '天津', '石家庄', '太原', '呼和浩特', '沈阳', '大连'],
        '华中': ['武汉', '长沙'],
        '西南': ['成都', '重庆', '昆明', '贵阳'],
        '西北': ['西安', '兰州'],
    }

    def get_region(city):
        for r, cities in regions.items():
            for c in cities:
                if city.startswith(c):
                    return r
        return '其他'

    region_order = ['华东', '华南', '华北', '华中', '西南', '西北', '其他']

    province_map = {
        '华东': '华东（上海·江苏·浙江·安徽·福建·江西·山东）',
        '华南': '华南（广东·广西·海南）',
        '华北': '华北（北京·天津·河北·山西·内蒙古·辽宁）',
        '华中': '华中（湖北·湖南）',
        '西南': '西南（四川·重庆·云南·贵州）',
        '西北': '西北（陕西·甘肃）',
        '其他': '其他地区',
    }

    grouped = {}
    for r in reports:
        region = get_region(r['city'])
        if region not in grouped:
            grouped[region] = []
        grouped[region].append(r)

    for region in grouped:
        grouped[region].sort(key=lambda x: x['city'])

    cards_html = ''
    for region in region_order:
        if region not in grouped:
            continue
        items = grouped[region]
        prov = province_map.get(region, region)
        cards_html += f'<div class="section" data-region="{region}">'
        cards_html += f'<div class="section-title">{region} <span class="tag">{prov}</span></div>'
        cards_html += '<div class="grid">'
        for r in items:
            map_link = ''
            if r['map']:
                map_link = f'<a href="{r["map"]}" class="map" target="_blank">🗺️ 地图</a>'
            else:
                map_link = '<span class="map map-na">🗺️ 地图</span>'
            cards_html += f'''<div class="card" data-city="{r['city']}">
          <div class="city-name">{r['city']}</div>
          <div class="links">
            <a href="{r['report']}" class="report" target="_blank">📄 报告</a>
            {map_link}
          </div>
        </div>'''
        cards_html += '</div></div>'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>中国城市旅游攻略 - 博查版</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
  background: #f5f7fa;
  color: #333;
  min-height: 100vh;
}}
.header {{
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 48px 24px 36px;
  text-align: center;
}}
.header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; letter-spacing: 2px; }}
.header p {{ font-size: 14px; opacity: 0.85; }}
.header .count {{ margin-top: 12px; font-size: 13px; opacity: 0.7; }}
.search-bar {{
  max-width: 600px;
  margin: -22px auto 0;
  padding: 0 16px;
  position: relative;
  z-index: 10;
}}
.search-bar input {{
  width: 100%;
  padding: 14px 20px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  background: white;
  box-shadow: 0 4px 20px rgba(0,0,0,0.12);
  outline: none;
  transition: box-shadow 0.2s;
}}
.search-bar input:focus {{ box-shadow: 0 4px 28px rgba(102,126,234,0.3); }}
.container {{ max-width: 1200px; margin: 28px auto 60px; padding: 0 16px; }}
.section {{ margin-bottom: 32px; }}
.section-title {{
  font-size: 18px; font-weight: 600; color: #444;
  padding-bottom: 12px; margin-bottom: 16px;
  border-bottom: 2px solid #e8ecf1;
  display: flex; align-items: center; gap: 8px;
}}
.section-title .tag {{ font-size: 12px; color: #999; font-weight: 400; }}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}}
.card {{
  background: white;
  border-radius: 12px;
  padding: 16px;
  text-decoration: none;
  color: inherit;
  transition: transform 0.15s, box-shadow 0.15s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border: 1px solid transparent;
  display: flex;
  flex-direction: column;
}}
.card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0,0,0,0.1);
  border-color: #667eea;
}}
.card .city-name {{ font-size: 18px; font-weight: 600; color: #222; margin-bottom: 6px; }}
.card .links {{ display: flex; gap: 8px; margin-top: 10px; }}
.card .links a {{
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  text-decoration: none;
  transition: all 0.15s;
}}
.card .links a.report {{ background: #667eea; color: white; }}
.card .links a.report:hover {{ background: #5a6fd6; }}
.card .links a.map {{ background: #f0f2f5; color: #666; }}
.card .links a.map:hover {{ background: #e8ecf1; color: #333; }}
.card .links .map-na {{ background: #f5f5f5; color: #ccc; cursor: not-allowed; }}
.no-result {{ text-align: center; padding: 60px 20px; color: #999; display: none; }}
.hidden {{ display: none !important; }}
.footer {{
  text-align: center; padding: 24px; color: #bbb; font-size: 12px;
}}
@media (max-width: 600px) {{
  .header {{ padding: 32px 16px 28px; }}
  .header h1 {{ font-size: 22px; }}
  .grid {{ grid-template-columns: repeat(2, 1fr); gap: 10px; }}
  .card {{ padding: 14px; }}
  .card .city-name {{ font-size: 16px; }}
}}
</style>
</head>
<body>

<div class="header">
  <h1>&#127758; 中国城市旅游攻略</h1>
  <p>主要城市 2026 年暑期深度游玩调研报告</p>
  <div class="count">共 {len(reports)} 个城市地区 · 每周持续更新</div>
</div>

<div class="search-bar">
  <input type="text" id="search" placeholder="&#x1F50D; 搜索城市名称..." oninput="filterCities(this.value)">
</div>

<div class="container" id="container">
{cards_html}
</div>

<div class="no-result" id="noResult">&#x1F615; 没有找到匹配的城市</div>

<div class="footer">数据来源: 博查 WebSearch API · 地图: 高德 AMAP</div>

<script>
function filterCities(query) {{
  const q = query.trim().toLowerCase();
  const cards = document.querySelectorAll('.card');
  const sections = document.querySelectorAll('.section');
  let anyVisible = false;
  cards.forEach(card => {{
    const city = card.dataset.city.toLowerCase();
    const match = !q || city.includes(q);
    card.classList.toggle('hidden', !match);
    if (match) anyVisible = true;
  }});
  sections.forEach(sec => {{
    const visibleCards = sec.querySelectorAll('.card:not(.hidden)');
    sec.classList.toggle('hidden', visibleCards.length === 0);
  }});
  document.getElementById('noResult').style.display = anyVisible ? 'none' : 'block';
}}
</script>

</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'✅ index.html generated with {len(reports)} cities')
    print(f'   数据目录: {data_dir}')
    print(f'   输出文件: {output_path}')

    grouped_print = {}
    for r in reports:
        region = get_region(r['city'])
        if region not in grouped_print:
            grouped_print[region] = []
        grouped_print[region].append(r['city'])
    for region in region_order:
        if region in grouped_print:
            print(f'  {region}: {", ".join(grouped_print[region])}')


if __name__ == '__main__':
    main()
