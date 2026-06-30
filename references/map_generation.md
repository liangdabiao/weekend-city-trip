# 地图面板生成工作流(Step 10 详解)

本文档详述 `weekend-city-trip` skill 的 **Step 10** —— 把 Markdown 调研报告转化为可交互的 HTML 地图面板。

详细命令与配色已写入 `SKILL.md` Step 10,本文档聚焦**实战要点**与**踩坑排查**。

---

## 0. 何时触发

| 用户话语 | 触发 |
|---|---|
| "生成地图" / "标在地图上" / "地图版" / "mark on map" / "给我一个有地图的版本" | ✅ |
| "生成 HTML" / "网页版" (无地图诉求) | ❌ 走 Step 9(`md_to_html.py`) |
| 同时要 Markdown 报告和地图 | ✅ 先完成 Step 7-8,再触发 Step 10 |

**前置条件**:Step 8 质量检查必须已通过。

---

## 1. 五步管线(2025-06-30 更新)

```
Markdown 报告(.md)
    ↓ Step 1: extract_places.py
places.json            (含 name/address/type/note,无坐标)
    ↓ Step 2: geocode.py
places.geo.json        (补全 lat/lng/level,GCJ-02 坐标系)
    ↓ Step 3: clean_geojson.py  (新增,bocha LLM API 过滤)
geo.json(已清理)        (移除食物/活动名等非地点,补充已知坐标)
    ↓ Step 4: inject.py
{城市}地图_博查版.html   (中心自动计算,统一命名)
    ↓ Step 5: validate_map.py  (新增,自动验证)
验证通过 ✅             (7 项检查)
```

**一键执行**:`bash $SKILL/scripts/build_map.sh 城市 "时间" -m 报告.md`

### 1.1 Step A:抽取地点

```bash
SKILL=D:/fireclaw/.claude/skills/weekend-city-trip
python "$SKILL/scripts/extract_places.py" \
  "D:/fireclaw/杭州7月4-5日调查报告_博查版.md"
```

**输出**:`杭州7月4-5日调查报告_博查版.places.json`

**期望产出**:30-70 个地点(城市规模相关)。如果 < 10,可能原因:
- Markdown 报告没用标准 10 节结构(章节标题不含"演唱会/集市/..."等关键词)
- 内容主要是段落而非表格

**修复**:查看脚本中 `SECTION_MAP`,手动加章节关键词;或在 Markdown 中把分散的地点列成表格。

### 1.2 Step B:服务端地理编码(关键)

```bash
python "$SKILL/scripts/geocode.py" \
  "D:/fireclaw/杭州7月4-5日调查报告_博查版.places.json" \
  杭州
```

**输出**:`杭州7月4-5日调查报告_博查版.places.geo.json`

**期望成功率**:**85-95%**。失败的通常是:
- 演出名称(如"王力宏「最好的地方II」世巡")—— 不是地点
- 线路编号(如"2 号线")—— 不是站点
- 抽象描述(如"核心景区日均客流")—— 不是地点

这些"失败"是合理的(不该出现在地图上)。

**常见错误**:

| 错误 | 原因 | 修复 |
|---|---|---|
| `USERKEY_PLAT_NOMATCH` | Key 不是 "Web 服务" 类型 | 高德控制台新建 Web 服务 Key,设环境变量 `AMAP_KEY=新Key` |
| `DAILY_QUERY_OVER_LIMIT` | 日配额耗尽(默认 3000/日) | 次日重试,或申请提升配额 |
| `ENGINE_RESPONSE_DATA_ERROR` | 名称太泛查不到 | 改 name(如演出名→场馆名) |
| `INVALID_USER_KEY` | Key 失效 | 检查 Key 是否过期/被删除 |

**手动补坐标**(失败的关键地点):
1. 浏览器打开 https://lbs.amap.com/tools/picker
2. 搜索/点击地点,复制"经度,纬度"(GCJ-02)
3. 编辑 `.places.geo.json` 中对应条目,填入 `lat` / `lng`,改 `"geocoded": true`
4. 重新跑 Step C

### 1.3 Step C:注入到 HTML

```bash
python "$SKILL/scripts/inject.py" \
  "D:/fireclaw/杭州7月4-5日调查报告_博查版.places.geo.json" \
  "D:/fireclaw/杭州7月4-5日地图_博查版.html" \
  杭州 "2026/7/4-5"
```

**输出**:`杭州7月4-5日地图_博查版.html`(约 30-40KB)

**双击 HTML 即可在浏览器打开**(无需 HTTP 服务器)。所有预编码的 marker 立即可见。

---

## 2. 文件结构一览

```
D:/fireclaw/.claude/skills/weekend-city-trip/
├── SKILL.md                          # 主文档(Step 10 已写入)
├── templates/
│   └── map_panel.html                # 高德 JS API 2.0 模板
├── scripts/
│   ├── build_map.sh                  # 一键管线(新增,orchestrator)
│   ├── extract_places.py             # Markdown → places.json
│   ├── geocode.py                    # places.json → places.geo.json
│   ├── known_coords.json             # 134 条预存坐标(新增)
│   ├── clean_geojson.py              # LLM 内容过滤(新增)
│   ├── inject.py                     # geo.json → 最终 HTML
│   └── validate_map.py               # 地图质量验证(新增)
└── references/
    └── map_generation.md             # 本文档

调研工作目录(运行时):
D:/fireclaw/
├── {城市}{时间}调查报告_博查版.md               # 输入报告
├── {城市}{时间}调查报告_博查版.places.json      # Step 1 中间产物
├── {城市}{时间}调查报告_博查版.places.geo.json  # Step 2+3 中间产物
└── {城市}地图_博查版.html                       # 最终交付(统一命名)
```

---

## 3. 11 类配色(完整对照)

| type | 字母 | 颜色 | hex | 调查方向 | 章节关键词 |
|---|---|---|---|---|---|
| C | C | 红 | #d32f2f | 演唱会 | 演唱会/音乐会/演出 |
| S | S | 紫 | #7b1fa2 | 球赛 | 球赛/足球/篮球/赛区 |
| M | M | 黄 | #f9a825 | 集市 | 集市/市集/夜市 |
| U | U | 蓝 | #1565c0 | 博物馆 | 博物馆/展览/美术馆 |
| 5 | 5 | 橙 | #e65100 | 5A景区 | 5A/4A/景区/公园 |
| H | H | 粉 | #ec407a | 喜茶 | 喜茶/HEYTEA/茶饮 |
| F | F | 深红 | #ad1457 | 美食街 | 美食街/老字号/必吃 |
| W | W | 青 | #00838f | City Walk | city walk/citywalk/漫步 |
| L | L | 紫罗兰 | #4527a0 | 购物中心 | 购物中心/商场/万象城 |
| D | D | 灰 | #546e7a | 地铁站 | 地铁/线网/换乘 |
| T | T | 绿 | #2e7d32 | 优惠门票 | 优惠门票/折扣/免费门票 |

**修改配色**:编辑 `templates/map_panel.html` 的 `:root` CSS 变量 + `CATEGORIES` JS 对象(两处都改)。

---

## 4. 已实现的核心交互

### 4.1 分类筛选
- 顶部 pill 区有"全部"+ 各类别按钮(显示数量)
- 点击 pill 切换该类别显示/隐藏
- 状态:激活(深色)/ 静音(opacity 0.4)

### 4.2 搜索
- 实时过滤(150ms debounce)
- 搜索范围:name + address + note

### 4.3 双向联动
- **点卡片**:地图飞至 + 缩放到 15 级 + 打开 InfoWindow + 滚动卡片到可见区
- **点 marker**:高亮对应卡片 + 滚动到可见区
- **hover marker**:显示 label(类别色背景)

### 4.4 视野适配
- 启动 300ms 后自动 `setFitView` 包含所有可见标记
- 切换分类时不自动重置视野(避免打断)

### 4.5 响应式
- 桌面(>768px):左卡片 380px + 右地图
- 移动端:上卡片 40vh + 下地图

### 4.6 坐标保护
- 无坐标的地点:点击卡片显示 banner 提示,不再触发 `setZoomAndCenter`
- 顶部标题栏显示进度:`{日期} · {OK}/{TOTAL} 已定位 · 博查调研`

---

## 5. Key 与安全密钥配置(重要)

**Skill 不内置任何 Key**。所有 Key 由用户提供,通过环境变量注入。

### 5.1 必需的环境变量

| 环境变量 | 用途 | Key 类型 | 申请入口 |
|---|---|---|---|
| `AMAP_JS_KEY` | 浏览器加载地图底图 | Web 端(JS API) | 高德控制台 → 应用类型选「Web 端(JS API)」 |
| `AMAP_SECURITY` | JS API 安全密钥 | 与 JS API Key 配套 | 同上,Key 详情页可见 |
| `AMAP_KEY` | Python 服务端地理编码 | Web 服务 | 高德控制台 → 应用类型选「Web 服务」 |

**两类 Key 不能互通**。JS API Key 调 REST 会报 `USERKEY_PLAT_NOMATCH`,Web 服务 Key 在浏览器加载会拒绝。

### 5.2 配置方式

```bash
# bash / git-bash(推荐持久化到 ~/.bashrc 或 ~/.zshrc)
export AMAP_JS_KEY="你的JS_API_Key"
export AMAP_SECURITY="你的安全密钥"
export AMAP_KEY="你的Web服务Key"

# Windows PowerShell
$env:AMAP_JS_KEY="..."
$env:AMAP_SECURITY="..."
$env:AMAP_KEY="..."
```

### 5.3 注入机制

- **JS API Key + 安全密钥**:`inject.py` 读取环境变量,替换 `templates/map_panel.html` 中的 `{{AMAP_JS_KEY}}` 和 `{{AMAP_SECURITY}}` 占位符
- **Web 服务 Key**:`geocode.py` 直接读取 `AMAP_KEY` 环境变量

### 5.4 安全密钥的前端暴露问题

JS API 安全密钥会出现在最终 HTML 里(这是高德的常规用法,无法避免)。生产环境可通过**代理服务器转发**(`/amap/security` 端点动态返回)隐藏,本 skill 用于个人调研,直接内置即可。

### 5.5 Key 缺失时的行为

- `geocode.py`:打印帮助信息 + 退出码 2
- `inject.py`:打印帮助信息 + 退出码 2

两者都会提示用户到 https://console.amap.com/dev/key/app 申请并配置环境变量。

---

## 6. 坐标系注意

| 来源 | 坐标系 | 直接用? |
|---|---|---|
| 高德地理编码 API | GCJ-02 | ✅ |
| 高德拾取坐标工具 | GCJ-02 | ✅ |
| 百度地图 API | BD-09 | ❌ 需转换 |
| Google Maps | WGS-84 | ❌ 需转换 |
| OpenStreetMap | WGS-84 | ❌ 需转换 |

**用错坐标系会导致标记偏移 100-500 米**(国内特色"火星坐标"问题)。本 skill 全程使用 GCJ-02,**不要混入其他来源坐标**。

如需从其他来源转换,用高德官方接口:
```
GET https://restapi.amap.com/v3/assistant/coordinate/convert
  ?locations=lng,lat
  &coordsys=gps|baidu
  &key=AMAP_KEY
```

---

## 7. 性能与限额

### 高德 Web 服务地理编码 API 限额
- 个人开发者:**3000 次/日**(免费,无需绑定信用卡)
- 单次批量地图生成:**30-70 地点**(城市调研规模)
- 一次调研消耗 = 1 次配额,**配额充裕**

### 高德 JS API 加载性能
- 库大小:~300KB(gzip)
- 首次加载约 1-2 秒(取决于网络)
- 国内 CDN 加速,稳定

### 标记数量上限
- 200 个 marker 内:**流畅**(无需聚合)
- 200-500:建议加 MarkerCluster
- 500+:**必须**用聚合,否则卡顿

本 skill 单城市 30-70 地点,**无需聚合**。

---

## 8. 常见问题排查

### Q1:打开 HTML 白屏
- 浏览器 F12 控制台看错误
- 常见:`AMap is not defined` → Key 无效或网络不通
- 修复:换 Key,或换网络环境

### Q2:地图加载,但 marker 全部不显示
**首要检查**:打开 `places.geo.json`,确认 `lat`/`lng` 字段存在且为数字。

```bash
python -c "import json; d=json.load(open('杭州7月4-5日调查报告_博查版.places.geo.json',encoding='utf-8')); ok=sum(1 for p in d if p.get('lat') and p.get('lng')); print(f'{ok}/{len(d)} 已编码')"
```

**若 0/N 已编码**:Step B 没成功跑,或 Key 类型错误:
- 高德控制台 https://console.amap.com/dev/key/app
- 新建 Key,应用类型选 **「Web 服务」**
- 用环境变量覆盖:`AMAP_KEY=新Key python geocode.py ...`

**若部分编码**:正常,失败的通常是演出名/线路编号等非地点条目。

### Q3:点击卡片报错 `Pixel(NaN, NaN)`
**已修复**(2025-06-30):selectPlace 已对未编码地点做保护。
若仍报错,说明 HTML 是旧版,需用 `inject.py` 重新生成。

### Q4:部分 marker 不显示
- 该地点名称太泛(如"老字号")高德查不到 → 手动改 address 后重跑 Step B/C
- 在 F12 控制台搜索 `[geocode failed]` 看具体失败原因

### Q5:marker 偏移
- 坐标系错误(用了百度/Google 坐标)
- 修复:用高德拾取坐标工具重新获取

### Q6:InfoWindow 中文乱码
- HTML 文件编码必须是 UTF-8(BOM 与无 BOM 都可)
- 编辑器(如 Notepad)默认 ANSI,需手动转 UTF-8

### Q7:筛选后地图空了
- 所有类别都被关闭(顶部"全部"按钮可一键恢复)
- 或所有地点都没编码成功(检查顶部进度条)

### Q8:卡片太多找不到
- 用顶部搜索框过滤(支持名称/地址/备注)

### Q9:USERKEY_PLAT_NOMATCH 错误
**这是最常见的错误**。说明你用了 **Web 端 JS API** 类型的 Key 去调 Web 服务 REST。
- JS API Key → 只能用于浏览器端 JS SDK
- Web 服务 Key → 用于 Python/服务端 REST 调用
- 两者是**不同的 Key**,在高德控制台分别申请

---

## 9. 测试 checklist

生成地图后,依次验证:

- [ ] `places.geo.json` 中 ≥ 60% 地点有 lat/lng
- [ ] 浏览器打开 HTML,地图加载(无白屏)
- [ ] 默认显示所有有坐标的 marker + 自动 fitView
- [ ] 顶部 11 类 pill 显示(只显示有内容的类别)
- [ ] 点击 pill 切换显示/隐藏
- [ ] 搜索框输入关键词,卡片过滤
- [ ] 点击卡片 → 地图飞至 + InfoWindow 弹出
- [ ] 点击 marker → 卡片高亮 + 滚动可见
- [ ] 右下角图例完整(11 类配色)
- [ ] 缩放至手机宽度(<768px)切换纵向布局
- [ ] F12 控制台无报错

---

## 10. 交付话术

```
✅ 地图已生成:
- 文件:D:/fireclaw/{城市}{时间}_map.html
- 地点:{成功}/{总} 个已编码(如 62/69)
- 11 类配色 × 分类筛选 × 搜索 × 双向联动
- 直接双击 HTML 即可在浏览器查看(无需 HTTP 服务)

⚠️ 失败地点(如有):[列出 3 个]
通常是演出名/线路编号等非地点条目,正常。
若需补全,打开 https://lbs.amap.com/tools/picker 手动查询坐标,
编辑 .places.geo.json 对应条目,重跑 inject.py 即可。

💡 推荐查看方式:
- 桌面:浏览器全屏,左侧筛选 + 右侧地图
- 移动:手机浏览器,上滑卡片 / 下滑地图
- 分享:HTML 文件可直接发给别人,无需任何依赖
```
