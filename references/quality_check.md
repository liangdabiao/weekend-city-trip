# 质量检查与迭代优化

> 报告生成 ≠ 任务完成。本文件定义 5 大质量维度、各节最低信息密度、检查清单、常见错误识别、补查询触发条件、补查询模板、迭代优化流程。
>
> **核心原则**:**任何不达标的章节,必须触发补查询 + 修复**,不能交付有缺陷的报告。

---

## 目录

1. [5 大质量维度](#1-5-大质量维度)
2. [各节最低信息密度要求](#2-各节最低信息密度要求)
3. [检查清单(Checklist)](#3-检查清单checklist)
4. [常见错误识别](#4-常见错误识别)
5. [补查询触发条件](#5-补查询触发条件)
6. [补查询模板](#6-补查询模板)
7. [迭代优化流程](#7-迭代优化流程)
8. [自动检查脚本](#8-自动检查脚本)

---

## 1. 5 大质量维度

### 1.1 完整性(Completeness)

**定义**:11 个调查方向是否全部覆盖,10 节标准结构是否齐全。

**检查方式**:
- 扫描生成的 Markdown 是否有 11 个调查方向的内容
- 检查 10 节标题是否齐全(〇-十)
- 每节是否有实质内容(不是空表格或单行文字)

**不达标示例**:
- 缺失"5A 景区"章节
- 有"美食街"标题但只有一句话
- "地铁"章节只有线网总览,没有出口细节

### 1.2 准确性(Accuracy)

**定义**:时间、地点、价格、地铁等关键信息是否真实准确。

**检查方式**:
- 时间合理性(演出日期在未来,不是过去)
- 地铁站名真实存在(查地铁线路图)
- 价格信息有信源支持(不是凭空捏造)
- 营业时间合理(不是凌晨 3 点开门)

**不达标示例**:
- 演出日期是 2024 年的(过时)
- 地铁站名拼错或不存在
- 价格明显异常(如"长隆门票 5 元")
- 演唱会场馆不真实

### 1.3 丰富度(Richness)

**定义**:每节是否有足够的细节、表格、图片,信息密度足够。

**检查方式**:
- 每节字数 > 200 字
- 关键章节(活动/门票/喜茶)有表格
- 图文版每节至少 1 张代表图
- 多个具体名称(店名/站名/票价)

**不达标示例**:
- 活动章节只有 2 条
- 门票没有具体价格
- 喜茶门店没说主题是什么
- 整节是纯散文,没有表格

### 1.4 可执行性(Actionability)

**定义**:用户能否直接按报告执行?路线是否能走通?

**检查方式**:
- 周末组合路线时间不重叠( dinners 不在两个城市)
- 地铁换乘合理(不是不可能的换乘)
- 时间表有缓冲(不是 10 分钟跨城)
- 关键操作有说明(购票、入场、退票)

**不达标示例**:
- 路线 A 上午在城南,下午在城北,中间只有 30 分钟
- 演出 19:00 开始,路线写 18:30 从对面城区出发
- 没有说怎么买票

### 1.5 信源多样性(Source Diversity)

**定义**:信息是否多源验证,避免单一来源偏差。

**检查方式**:
- 关键信息(票价/演出)至少 2 个信源
- 信源至少来自 3 类(官媒/文旅/行业媒体/UGC)
- 避免完全依赖单一站点(如全是本地宝)

**不达标示例**:
- 所有信息都来自同一个网站
- 门票信息只有用户评论,没有官方公告
- 演出信息只有大麦,没有场馆公告

---

## 2. 各节最低信息密度要求

| 章节 | 最低要求 | 优秀标准 |
|---|---|---|
| 〇 一图速览 | 8 个类别 | 10 个类别全覆盖 |
| 1.1 演唱会/演出 | 3 场演出 | 5+ 场含时间/场馆/票价 |
| 1.2 集市 | 2 个集市 | 4+ 个含特色/时段 |
| 1.3 球赛 | 1 场比赛(如有) | 3+ 场含球队/联赛 |
| 1.4 博物馆 | 3 个博物馆 | 5+ 个含当前展览 |
| 1.6 影视/网红 | 3 个打卡点 | 5+ 个含亮点/地铁 |
| 1.7 5A 景区 | 2 个景区 | 4+ 个含票价/交通 |
| 2 优惠门票 | 3 个景区 | 5+ 个含原价/现价/规则 |
| 3 喜茶门店 | 2 家主题店 | 3+ 家含开业日期/产品 |
| 4 美食街 | 3 条美食街 | 5+ 条含区域/代表店 |
| 5 city walk | 1 条路线 | 2+ 条含节点/长度 |
| 6 地铁线网 | 总线路数 + 里程 | 含换乘枢纽/服务热线 |
| 6 地铁出口 | 2 个站点出口 | 4+ 站点含 A/B/C/D 编号 |
| 6 直达商场 | 5 个商场 | 10+ 个含地铁站 |
| 7 周末路线 | 2 条主题路线 | 3 条含时间表/总花费 |

**任一项低于最低要求 → 触发补查询**(详见第 5 节)。

---

## 3. 检查清单(Checklist)

报告生成后,**逐项打勾**:

### 完整性
- [ ] 报告头含 6 个字段(调查日期/覆盖时段/调查方式/API 次数/信源)
- [ ] 〇 一图速览存在,且 ≥ 8 个类别
- [ ] 11 个调查方向全部有内容
- [ ] 十节结构完整(〇-十)
- [ ] 每节有 H2/H3 标题

### 准确性
- [ ] 所有演出日期都在未来(不是过去)
- [ ] 所有地铁站名真实存在
- [ ] 所有价格都合理(不是 0 元或异常高)
- [ ] 所有营业时间合理
- [ ] 关键信息有信源支持(底部的引用源章节)

### 丰富度
- [ ] 关键章节(1/2/3/4/6)有表格
- [ ] 图文版每节至少 1 张图
- [ ] 每节字数 > 200 字
- [ ] 有具体的店名/站名/票价(不是泛泛而谈)

### 可执行性
- [ ] 周末路线时间不重叠
- [ ] 路线节点之间地铁可达
- [ ] 关键操作有说明(购票/入场)
- [ ] 时效可靠性章节存在

### 信源多样性
- [ ] 引用源章节存在
- [ ] 信源 ≥ 5 个不同站点
- [ ] 关键信息 ≥ 2 个信源验证
- [ ] 信源涵盖 ≥ 3 类(官媒/文旅/行业/UGC)

---

## 4. 常见错误识别

### 4.1 跨城市噪声

**症状**:
- 报告里出现其他城市的信息
- 例如:广州报告里有"北京路...北京"

**识别方法**:
```python
import re

# 城市关键词检测
other_cities = ['北京', '上海', '深圳', '成都', '杭州', '武汉', '西安']
target_city = '广州'  # 当前任务的目标城市

for section in report_sections:
    for other in other_cities:
        if other == target_city:
            continue
        # 如果段落频繁提到其他城市,可能是噪声
        if section.count(other) > 3 and target_city not in section:
            print(f'疑似跨城市噪声: {section[:100]}')
```

**修复**:
- 删除该条目
- 在 query 加城市前缀重查

### 4.2 过时数据

**症状**:
- 票价是 2018-2020 年的
- 已关闭的店仍在推荐
- 已结束的活动当作"近期"

**识别方法**:
- 检查 datePublished 字段,标注 2022 年前的数据为"待验证"
- 演出日期早于今天 = 过时
- 喜茶门店开业日期早于 2020 年 = 不是"热点"

**修复**:
- 标注"出行前请二次确认"
- 或重新查询 freshness=oneMonth 拿最新数据

### 4.3 虚假信息(博查 summary 幻觉)

**症状**:
- summary 字段给出的"事实"在原文找不到
- 数字精确但可疑(如"占地 1234.56 平方米")
- 多个看似具体但矛盾的细节

**识别方法**:
- 关键信息至少 2 个信源验证
- 价格/时间等数字字段必须可追溯
- summary 与 snippet 严重不一致时,信 snippet

**修复**:
- 删除无法验证的信息
- 标注"未验证"
- 用更精准的 query 重查

### 4.4 图片失效

**症状**:
- thumbnailUrl 返回 404
- 图片明显是 logo/icon(不是内容图)
- 图片与上下文不相关

**识别方法**:
```python
import requests

def check_image(url, timeout=5):
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code == 200 and 'image' in r.headers.get('content-type', '')
    except:
        return False
```

**修复**:
- 删除失效图片
- 保留文字说明(每张图下应有粗体说明)
- 用其他响应里的图片替代

### 4.5 信息密度不足

**症状**:
- 某节只有 1-2 条
- 表格只有标题行
- 关键字段(时间/价格)空缺

**修复**:
- 见第 5 节"补查询触发条件"

---

## 5. 补查询触发条件

**任一条件命中,必须触发补查询**:

| # | 触发条件 | 优先级 |
|---|---|---|
| 1 | 11 个调查方向有任何一个完全缺失 | 🔴 必补 |
| 2 | 演唱会/演出章节 < 3 场 | 🔴 必补 |
| 3 | 演出/演唱会缺时间或场馆 | 🔴 必补 |
| 4 | 优惠门票章节 < 3 个景区 | 🔴 必补 |
| 5 | 喜茶门店 < 2 家 | 🟡 建议补 |
| 6 | 美食街 < 3 条 | 🟡 建议补 |
| 7 | city walk 章节无具体路线 | 🟡 建议补 |
| 8 | 地铁出口细节 < 2 个站点 | 🟡 建议补 |
| 9 | 直达商场清单 < 5 个 | 🟢 可选 |
| 10 | 跨城市噪声 > 30% | 🔴 必补 |
| 11 | 关键价格无法找到信源 | 🟡 建议补 |
| 12 | 图片 < 5 张(图文版) | 🟢 可选 |

**优先级说明**:
- 🔴 必补:不补不能交付
- 🟡 建议补:补了显著提升质量
- 🟢 可选:时间充裕再补

---

## 6. 补查询模板

### 6.1 演出/演唱会不足

```json
// fix_concerts.json
{"query":"{CITY} 演唱会 {MONTH} 排期 时间 场馆 票价 大麦","summary":true,"count":15,"freshness":"oneMonth"}
```

### 6.2 优惠门票不足

```json
// fix_tickets.json
{"query":"{CITY} 景区 门票 优惠 {具体景区名1} {具体景区名2} 学生 暑期","summary":true,"count":12,"freshness":"oneMonth"}
```

### 6.3 喜茶门店不足

```json
// fix_heytea.json
{"query":"{CITY} 喜茶 门店 地址 营业 时间 推荐 {区域1} {区域2}","summary":true,"count":10}
```

### 6.4 美食街不足

```json
// fix_food.json
{"query":"{CITY} 美食街 老字号 推荐 {区域1} {区域2} {区域3} 必吃","summary":true,"count":15}
```

### 6.5 city walk 不足

```json
// fix_citywalk.json
{"query":"{CITY} city walk 路线 打卡 拍照 老城区 文艺 2026","summary":true,"count":10}
```

### 6.6 地铁出口细节不足

```json
// fix_subway_exit.json
{"query":"{CITY} 地铁 {地标站1} 出口 编号 通向 商场","summary":true,"count":10}
```

### 6.7 跨城市噪声严重

→ 改写 query,加强城市前缀:

```json
// fix_noise.json
{"query":"{CITY} {CITY} {CITY} {主题} 必去 本地 仅限 {CITY}","summary":true,"count":12}
```

### 6.8 补查询批次执行

```bash
# 最多 4 路并行
curl ... -d @fix_concerts.json -o r_fix_concerts.json &
curl ... -d @fix_tickets.json -o r_fix_tickets.json &
curl ... -d @fix_heytea.json -o r_fix_heytea.json &
curl ... -d @fix_food.json -o r_fix_food.json &
wait
```

**预算控制**:补查询通常 2-4 次,加上初始 11 次,总计 13-15 次,仍在 50 次预算内。

---

## 7. 迭代优化流程

```
Step 7 报告整合完成
       ↓
Step 8.1 自动检查(python 扫描报告)
       ↓
Step 8.2 错误识别(跨城市噪声/过时/幻觉/图片失效)
       ↓
Step 8.3 触发条件评估(第 5 节 12 项)
       ↓
   有触发?
   ├─ 是 → Step 8.4 补查询批次(第 6 节模板)
   │       ↓
   │       Step 8.5 修复报告(整合新数据 + 删除错误)
   │       ↓
   │       Step 8.6 二次检查(回到 Step 8.1)
   │       ↓
   │       (最多 2 轮迭代,避免无限循环)
   │
   └─ 否 → Step 8.7 交付报告
```

### 迭代控制

- **最多 2 轮补查询**(防止无限循环)
- 每轮补查询 ≤ 4 次(1 个批次)
- 总 API 调用 ≤ 15 次(初始 11 + 补救 4)
- 第 3 轮触发条件仍命中 → 标注"信息有限"交付

### 修复动作优先级

| 优先级 | 动作 |
|---|---|
| 1 | 删除跨城市噪声条目 |
| 2 | 删除过时数据(2020 年前的票价/已闭店) |
| 3 | 补充缺失章节(必补触发) |
| 4 | 补充低密度章节(建议补触发) |
| 5 | 替换失效图片 |
| 6 | 加二次确认安全声明 |

---

## 8. 自动检查脚本

### 8.1 报告结构检查

```python
import re
from pathlib import Path

def check_report_structure(report_path):
    """检查报告的 10 节结构是否齐全"""
    content = Path(report_path).read_text(encoding='utf-8')
    
    required_sections = [
        (r'^## 〇、一图速览', '一图速览缺失'),
        (r'^## 一、.*活动', '活动章节缺失'),
        (r'^## 二、.*门票', '门票章节缺失'),
        (r'^## 三、.*喜茶', '喜茶章节缺失'),
        (r'^## 四、.*美食街', '美食街章节缺失'),
        (r'^## 五、.*city walk', 'city walk 章节缺失'),
        (r'^## 六、.*地铁', '地铁章节缺失'),
        (r'^## 七、.*路线', '周末路线章节缺失'),
        (r'^## 八、.*时效|可靠性', '时效说明缺失'),
        (r'^## 九、.*API|统计', 'API 统计缺失'),
        (r'^## 十、.*引用|信源', '引用源缺失'),
    ]
    
    issues = []
    for pattern, msg in required_sections:
        if not re.search(pattern, content, re.MULTILINE):
            issues.append(msg)
    
    return issues

# 用法
issues = check_report_structure('广州下周末调查报告_博查版.md')
if issues:
    print('报告结构问题:')
    for i in issues:
        print(f'  - {i}')
else:
    print('结构完整 ✓')
```

### 8.2 表格行数检查

```python
def check_section_density(report_path):
    """检查各关键章节的表格行数(信息密度)"""
    content = Path(report_path).read_text(encoding='utf-8')
    
    # 找各章节
    sections = re.split(r'^## ', content, flags=re.MULTILINE)
    
    density = {}
    for sec in sections:
        if not sec.strip():
            continue
        title = sec.split('\n')[0][:30]
        # 数表格行(| 开头,但不是表头/分隔)
        table_rows = [l for l in sec.split('\n') 
                      if l.strip().startswith('|') and '---' not in l]
        # 数图片
        images = len(re.findall(r'!\[.*?\]\(.*?\)', sec))
        density[title] = {
            'table_rows': len(table_rows),
            'images': images,
            'chars': len(sec)
        }
    
    return density

# 输出后人工判断是否达标(参考第 2 节最低要求)
```

### 8.3 跨城市噪声检测

```python
def detect_cross_city_noise(report_path, target_city):
    """检测报告中是否有其他城市的过度提及"""
    content = Path(report_path).read_text(encoding='utf-8')
    
    other_cities = ['北京', '上海', '深圳', '广州', '成都', 
                    '杭州', '武汉', '西安', '重庆', '南京']
    other_cities = [c for c in other_cities if c != target_city]
    
    # 按段落分割
    paragraphs = re.split(r'\n\s*\n', content)
    
    noise_paragraphs = []
    for i, p in enumerate(paragraphs):
        if len(p) < 50:
            continue
        for other in other_cities:
            if other in p and target_city not in p:
                noise_paragraphs.append((i, other, p[:100]))
                break
    
    return noise_paragraphs
```

### 8.4 图片可用性检查

```python
import requests
import re
from pathlib import Path

def check_images(report_path, timeout=5):
    """检查报告中的图片 URL 是否可用"""
    content = Path(report_path).read_text(encoding='utf-8')
    urls = re.findall(r'!\[.*?\]\((http.*?)\)', content)
    
    results = []
    for url in urls:
        try:
            r = requests.head(url, timeout=timeout, allow_redirects=True)
            ok = r.status_code == 200 and 'image' in r.headers.get('content-type', '')
            results.append((url, ok, r.status_code))
        except Exception as e:
            results.append((url, False, str(e)))
    
    failed = [r for r in results if not r[1]]
    return results, failed
```

### 8.5 一键综合检查

```python
def full_check(report_path, target_city):
    """综合检查:结构 + 密度 + 噪声 + 图片"""
    print(f'=== 检查 {report_path} ===\n')
    
    # 1. 结构
    issues = check_report_structure(report_path)
    print(f'结构检查: {"通过 ✓" if not issues else "问题:"}')
    for i in issues:
        print(f'  - {i}')
    
    # 2. 密度
    density = check_section_density(report_path)
    print(f'\n信息密度(各节表格行数):')
    for title, d in density.items():
        flag = '⚠️' if d['table_rows'] < 3 else '✓'
        print(f'  {flag} {title}: {d["table_rows"]} 行, {d["images"]} 图, {d["chars"]} 字')
    
    # 3. 噪声
    noise = detect_cross_city_noise(report_path, target_city)
    print(f'\n跨城市噪声段落: {len(noise)} 个')
    for i, city, snippet in noise[:3]:
        print(f'  - 段 {i} 提到 "{city}": {snippet}...')
    
    # 4. 图片(可选,慢)
    # results, failed = check_images(report_path)
    # print(f'\n图片失效: {len(failed)}/{len(results)}')
    
    print('\n=== 检查完成 ===')
```

---

## 一句话总结

**报告生成后必须执行 5 大维度检查 + 12 项触发条件评估 + 必要时 1-2 轮补查询迭代,确保交付质量达标**。

核心 3 条:
1. **不达标不交付**(必补触发条件不能跳过)
2. **最多 2 轮迭代**(防止无限循环浪费 credits)
3. **删除错误 > 补充缺失**(优先级,错误信息会误导用户)
