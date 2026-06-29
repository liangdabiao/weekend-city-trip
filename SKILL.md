---
name: weekend-city-trip
description: Comprehensive weekend city travel investigation skill for Chinese cities. Use this skill PROACTIVELY whenever the user wants to research a city for weekend or near-future (within 1 month) travel — including 小红书 activities, 演唱会/concerts, 集市/markets, 球赛/sports matches, 博物馆/museums, 优惠门票/discount tickets, 喜茶门店/Heytea locations, 美食街/food streets, city walk routes, 5A 景区/scenic areas, and 地铁路线/subway routes. Triggers on phrases like "调研XX城市"、"XX城市周末去哪"、"周末小旅游"、"XX城市旅游攻略"、"本周末/下周末去XX"、"XX城市近期活动"、"weekend trip to [city]"、"investigate [city]"、"城市调查". Based on Bocha WebSearch API (博查 API), generates image-rich Markdown reports. Always invoke this skill when the user mentions researching any Chinese city for short-term travel, even if they don't explicitly ask for a "skill" or "攻略".
---

# 周末城市旅游攻略调研 Skill

基于博查 WebSearch API 的标准化城市旅游调研工作流,支持任意中国城市的本周末 / 下周末 / 未来一个月深度调研。

覆盖 11 个调查方向:小红书近期活动、演唱会、集市、球赛、博物馆、优惠门票、喜茶门店、美食街、city walk、5A 景区、地铁路线。生成图文并茂的 Markdown 攻略,信源以权威媒体为主(腾讯新闻、网易、人民网、官方文旅、本地宝、行业媒体等)。

---

## 适用场景

✅ **适用**:
- "调研广州下周末有什么好玩"
- "上海本周末活动攻略"
- "成都未来一个月旅游调研"
- "北京周末小旅游"
- "我想下周末去杭州,帮我全面调查一下"

❌ **不适用**:
- 海外城市调研(博查以中文索引为主)
- 长期旅居 / 移民调研(超过 1 个月)
- 单一深度主题(如只查某场演唱会票价 → 直接 WebSearch 即可)

---

## 前置准备

执行前必须确认 3 项:

| 项 | 说明 | 默认 |
|---|---|---|
| **博查 API key** | 用户提供 `sk-xxx` | — |
| **目标城市** | 中文城市名(广州/上海/成都...) | — |
| **时间范围** | 本周末 / 下周末 / 未来一个月 / 具体日期 | 下周末 |
| 偏好(可选) | 亲子/情侣/独行/带娃 | 通用 |
| 是否图文版(可选) | thumbnailUrl 嵌入报告 | 是 |
| **输出格式**(可选) | markdown / html / both | markdown |

如果用户没说时间范围,**默认下周末**(本周可能来不及准备)。

---

## 工作流程(8 步法)

### Step 1: 时间锁定

算清楚用户的"本周末/下周末"对应的具体日期:
- 今天 = `{currentDate}`
- 本周末 = 即将到来的周六周日
- 下周末 = 下一个周六周日
- "未来一个月" = 今天起 30 天内

**关键洞察**:新闻文章发布时间 ≠ 活动举办时间。一篇 6/26 发布的文章可能在介绍 7/4 的活动,所以 freshness 必须用 `oneMonth` 拿"近期发布 + 介绍未来活动"的文章,而不是"近期举办"的活动。

### Step 2: 用户确认

如果用户消息里已经包含城市 + 时间,直接进入 Step 3。
否则用 AskUserQuestion 确认。

### Step 3: TaskCreate + 工作目录

```
D:/fireclaw/bocha_{城市拼音}/
```

TaskCreate 6 个任务(信息密度与执行效率的平衡点):
1. {城市}近期活动(活动/演唱会/集市/球赛/博物馆)
2. {城市}优惠门票(本地宝优惠 + 5A 景区)
3. {城市}喜茶热点(门店 + 购物中心)
4. {城市}美食街 + city walk
5. {城市}地铁路线(线网 + 关键站点出口)
6. 整合 {城市}图文报告

### Step 4: 写 query JSON 文件

按 `references/query_templates.md` 为每个调查方向写 query body。
**必须用 heredoc + `-d @file.json`**,不要内联单引号 JSON(Windows curl 坑)。

```bash
cat > D:/fireclaw/bocha_{城市拼音}/q1a.json << 'EOF'
{"query":"广州 周末活动 展览 演出 市集 演唱会 2026年7月","summary":true,"count":12,"freshness":"oneMonth"}
EOF
```

### Step 5: 并行批次执行

**严格 4 路并行,不要 5 个**(429 临界值)。

批次 1(4 路独立):
```bash
API_KEY="sk-xxx"
API="https://api.bocha.cn/v1/web-search"
DIR="D:/fireclaw/bocha_{城市拼音}"

curl -s -X POST "$API" -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" -d @"$DIR/q1a.json" -o "$DIR/r_q1a.json" &
curl -s -X POST "$API" -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" -d @"$DIR/q2a.json" -o "$DIR/r_q2a.json" &
curl -s -X POST "$API" -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" -d @"$DIR/q3a.json" -o "$DIR/r_q3a.json" &
curl -s -X POST "$API" -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" -d @"$DIR/q4.json" -o "$DIR/r_q4.json" &
wait
```

批次 2 + 批次 3 同理,完整模板见 `references/query_templates.md`。

### Step 6: 解析响应

python 单行脚本提取关键字段:

```python
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

files = ['r_q1a.json','r_q1b.json','r_q1c.json','r_q2a.json',
         'r_q3a.json','r_q3b.json','r_q4.json','r_q5a.json','r_q5b.json']
for f in files:
    with open(f, encoding='utf-8') as fp:
        d = json.load(fp)
    vals = d.get('data',{}).get('webPages',{}).get('value',[])
    print(f'==={f} ({len(vals)} 条)===')
    for v in vals[:8]:
        name = v.get('name','')
        site = v.get('siteName','')
        date = (v.get('datePublished') or '')[:10]
        summ = (v.get('summary') or v.get('snippet') or '')[:150].replace('\n',' ')
        print(f'  [{site}|{date}] {name}')
        print(f'    {summ}')
```

**图片 URL 提取**(用于图文报告):
```python
for f in files:
    with open(f, encoding='utf-8') as fp:
        d = json.load(fp)
    imgs = (d.get('data',{}).get('images') or {}).get('value',[])
    for img in imgs[:5]:
        url = img.get('thumbnailUrl') or img.get('contentUrl') or ''
        if url.startswith('//'):
            url = 'https:' + url
        if url.startswith('http'):
            print(url)
```

### Step 7: 整合图文报告(初稿)

按 `references/report_template.md` 的 10 节标准结构整合,输出到:
```
D:/fireclaw/{城市}{时间}调查报告_博查版.md
```

**注意**:这只是初稿,**不等于任务完成**。必须经过 Step 8 质量检查与迭代优化才能交付。

---

### Step 8: 质量检查与迭代优化(必做)

**报告生成 ≠ 任务完成**。必须按 `references/quality_check.md` 的清单检查并修复。

#### 8.1 自动检查(2 分钟)

用 python 脚本扫描初稿,5 大维度:
- **完整性**:11 调查方向 + 10 节结构是否齐全
- **准确性**:时间/地点/价格是否真实(演出日期在未来,地铁站存在)
- **丰富度**:每节信息密度是否达标
- **可执行性**:周末路线时间是否冲突,地铁换乘是否合理
- **信源多样性**:是否多源验证(关键信息 ≥ 2 个信源)

脚本模板见 `references/quality_check.md` 第 8 节。

#### 8.2 各节最低信息密度

| 章节 | 最低 | 优秀 |
|---|---|---|
| 演唱会/演出 | 3 场 | 5+ 场含时间/场馆/票价 |
| 博物馆 | 3 个 | 5+ 个含当前展览 |
| 5A 景区 | 2 个 | 4+ 个含票价/交通 |
| 优惠门票 | 3 个景区 | 5+ 个含原价/现价/规则 |
| 喜茶门店 | 2 家主题店 | 3+ 家含开业日期/产品 |
| 美食街 | 3 条 | 5+ 条含区域/代表店 |
| city walk | 1 条路线 | 2+ 条含节点/长度 |
| 地铁出口 | 2 个站点 | 4+ 站点含 A/B/C/D 编号 |
| 直达商场 | 5 个 | 10+ 个含地铁站 |

#### 8.3 错误识别与修复

| 问题类型 | 表现 | 修复方式 |
|---|---|---|
| **信息缺失** | 某节 < 最低要求 | 触发补查询(见 8.4) |
| **跨城市噪声** | 提到其他城市 | 删除条目,query 加城市前缀重查 |
| **过时数据** | 2018-2020 票价 | 标注"出行前请二次确认"或重查 |
| **虚假信息(summary 幻觉)** | 数字可疑、单源、与 snippet 矛盾 | 至少 2 个信源验证,否则删除 |
| **图片失效** | thumbnailUrl 404 或是 logo | 删除图片,保留文字说明 |
| **路线冲突** | 时间重叠/不可能换乘 | 重新设计路线 |

#### 8.4 补查询触发条件

**任一条件命中就触发补查询**(详见 `references/quality_check.md` 第 5 节):

🔴 **必补**(不补不能交付):
- 11 个调查方向有任何一个完全缺失
- 演唱会/演出章节 < 3 场
- 演出缺时间或场馆
- 优惠门票章节 < 3 个景区
- 跨城市噪声 > 30%

🟡 **建议补**(补了显著提升质量):
- 喜茶门店 < 2 家
- 美食街 < 3 条
- city walk 无具体路线
- 地铁出口细节 < 2 个站点
- 关键价格无信源支持

🟢 **可选**:
- 直达商场清单 < 5 个
- 图片 < 5 张(图文版)

#### 8.5 补查询执行

补查询也走 4 路并行,模板见 `references/quality_check.md` 第 6 节。常用模板:

```bash
# 演出不足
{"query":"{CITY} 演唱会 {MONTH} 排期 时间 场馆 票价 大麦","summary":true,"count":15,"freshness":"oneMonth"}

# 门票不足
{"query":"{CITY} 景区 门票 优惠 {具体景区名1} {具体景区名2} 学生 暑期","summary":true,"count":12,"freshness":"oneMonth"}

# 喜茶门店不足
{"query":"{CITY} 喜茶 门店 地址 营业 时间 推荐 {区域1} {区域2}","summary":true,"count":10}

# 跨城市噪声严重 → 加强城市前缀
{"query":"{CITY} {CITY} {CITY} {主题} 必去 本地 仅限 {CITY}","summary":true,"count":12}
```

#### 8.6 迭代控制

- **最多 2 轮补查询**(防止无限循环)
- 每轮 ≤ 4 次(1 个批次)
- 总 API 调用 ≤ 15 次(初始 11 + 补救 4),仍在 50 次预算内
- 第 3 轮触发条件仍命中 → 标注"信息有限"交付,并在报告中说明

#### 8.7 二次检查

修复后**必须再次扫描**,确认所有 🔴 必补触发条件已解除。如仍有问题,进入第 2 轮迭代。

#### 8.8 修复优先级

1. **删除跨城市噪声条目**(错误信息会误导用户)
2. **删除过时数据**(2020 年前的票价/已闭店)
3. **补充缺失章节**(必补触发)
4. **补充低密度章节**(建议补触发)
5. **替换失效图片**
6. **加二次确认安全声明**(无法验证的信息)

#### 8.9 交付

所有 🔴 必补触发条件解除后,告知用户:
- 文件路径
- 核心亮点
- API 调用统计(初始 N 次 + 补救 M 次 = 总 N+M 次)
- 已知限制(如有,如"地铁出口信息偏旧,建议二次确认")

---

### Step 9: HTML 输出(可选,条件触发)

**触发条件**:用户明确要求 HTML 格式(如"生成 html"、"给我网页版"、"输出 html 报告")。

**前置条件**:Step 8 质量检查必须已通过,Markdown 报告为最终交付版。

#### 9.1 检查 Python 依赖

```bash
python -c "import markdown" 2>&1 || pip install markdown pymdown-extensions
```

如不愿安装,脚本会自动降级到 `markdown2`,再降级到内置极简转换器(无需任何外部库)。

#### 9.2 执行转换

```bash
python D:/fireclaw/.claude/skills/weekend-city-trip/scripts/md_to_html.py \
  "D:/fireclaw/{城市}{时间}调查报告_博查版.md"
# 默认输出同名 .html 文件,也可指定第二参数:
# python md_to_html.py input.md output.html
```

#### 9.3 HTML 特性

- **GFM 完整支持**:表格、代码块、引用块、有序/无序列表
- **中文字体优化**:苹方 / 微软雅黑 / 思源黑体 fallback
- **响应式布局**:手机 / 平板 / 桌面自适应
- **内嵌 CSS**:单文件可分享,无外部依赖
- **图片 lazy loading**:首屏加载快
- **自动提取首屏 H1** 作为页面标题
- **打印友好**:`@media print` 样式,可直接浏览器打印为 PDF

#### 9.4 交付

告知用户:
- Markdown 源文件路径
- HTML 文件路径(本次新增)
- 推荐查看方式:浏览器打开,或打印为 PDF 分享

---

## 调查的 11 个方向

详细 query 模板见 `references/query_templates.md`。

| # | 方向 | query 数 | freshness | 关键字段 |
|---|---|---|---|---|
| 1 | 小红书近期活动 | 1-2 | oneWeek 或 oneMonth | summary |
| 2 | 演唱会 | 1 | oneMonth | datePublished + summary |
| 3 | 集市 / 市集 | 1 | oneMonth | summary |
| 4 | 球赛 | 1 | oneMonth | summary |
| 5 | 博物馆 | 1 | noLimit | summary |
| 6 | 优惠门票(本地宝) | 1 | oneMonth | summary(不用 include!) |
| 7 | 喜茶门店 + 购物中心 | 2 | oneYear + noLimit | summary |
| 8 | 美食街 | 1 | noLimit | summary |
| 9 | city walk 路线 | 1 | noLimit | summary |
| 10 | 5A 景区 | 1 | noLimit | summary |
| 11 | 地铁路线 | 2 | noLimit | summary |

**总计 11-13 次 API 调用**(预算 50,余量 70%+)。

---

## 博查 API 用法速查

### 端点
```
POST https://api.bocha.cn/v1/web-search
Headers:
  Authorization: Bearer sk-xxxxxxxxxxxx
  Content-Type: application/json
```

### 必选/可选参数

| 参数 | 必选 | 推荐值 |
|---|---|---|
| `query` | ✅ | 中文长尾,4 要素:地点+主题+时效+品类 |
| `summary` | 推荐 | `true`(AI 摘要,核心字段) |
| `count` | 可选 | 10-15 |
| `freshness` | 可选 | noLimit/oneDay/oneWeek/oneMonth/oneYear |
| `include`/`exclude` | 可选 | **不推荐用**(见踩坑) |

### 响应结构
```json
{
  "data": {
    "webPages": {
      "totalEstimatedMatches": 10000000,
      "value": [
        {"name":"...","url":"...","summary":"...","snippet":"...",
         "siteName":"...","datePublished":"2026-06-26T10:00:00"}
      ]
    },
    "images": {
      "value": [{"thumbnailUrl":"...","name":"..."}]
    }
  }
}
```

### 字段优先级
- `summary`(AI 摘要,**核心**)> `snippet`(搜索引擎摘要)> `name`(标题)

---

## 关键踩坑(Top 8)

详细版 + 决策树见 `references/pitfalls.md`。

1. **Windows curl 必须用 `-d @file.json`**:不能 `-d '{"k":"v"}'`,会返回 500 Missing request body
2. **并行不超过 4 个**:5 个开始有 429 风险,4 个稳定
3. **不要用 `include` 做域名过滤**:在某些城市返回 0 条,在某些城市返回非目标城市数据。**改用 query 加城市前缀**
4. **freshness 选对**:热门 oneWeek/oneMonth,冷门 noLimit,<5 条立刻降级到 noLimit
5. **summary 缺失降级 snippet**:用 python `item.get('summary') or item.get('snippet')`
6. **图片 URL `//` 开头要补 `https:`**:用 python 检测
7. **响应 < 1KB 立刻怀疑踩坑**:读取确认后立即降级重试
8. **totalEstimatedMatches 永远是 10000000**:完全忽略,只看 value 数组

---

## 报告结构(10 节标准)

详细模板见 `references/report_template.md`。

```
〇、一图速览(表格)
一、下周末 + 月度活动清单(演唱会/集市/球赛/漫展/博物馆/5A)
二、优惠门票(本地宝 + 5A 景区)
三、喜茶门店热点(LAB/DP/PINK 等主题店)
四、美食街
五、city walk 路线
六、地铁路线(含 5A 景区 + 商场直达)
七、周末组合路线(A/B/C 三条主题路线)
八、时效可靠性说明
九、API 调用统计
十、引用源
```

每节配 1-2 张代表图,图下必带粗体文字说明(避免图失效)。

---

## 跨城市差异预警

不同城市的博查索引覆盖存在差异,需要在设计 query 时留余量:

| 维度 | 可能现象 | 应对 |
|---|---|---|
| 域名过滤(`include`) | 在某些城市返回 0 条,在某些城市返回非目标城市数据 | **不用 include**,改用 query 加城市前缀 |
| 美食街/小众主题召回量 | 因城市而异(5-15 条波动) | 接受现状,query 多加区域关键词 |
| 喜茶主题店类型 | 各城市定位不同(LAB/DP/PINK/Cake Lab) | 从 summary 字段里识别 |
| 地铁出口数据新旧 | 长尾信息文章可能偏旧 | 接受(出口编号基本不变)+ 报告加二次确认提示 |

**核心原则**:**召回数量不是质量指标**,5-7 条高质量 summary 优于 15 条低质量。不要为追求召回量重试浪费 credits。

---

## 失败状态码

| HTTP | 原因 | 对策 |
|---|---|---|
| 200 | 成功 | — |
| 400 | 缺 query / 缺 Authorization | 检查 body 和 header |
| 401 | API KEY 无效 | 换 key |
| 403 | "You do not have enough money" 余额不足 | 提醒用户充值 |
| 429 | 频率超限 | 等 60 秒重试 |
| 500 | body 没传过去 | 确认用 `-d @file.json` |

---

## 参考文件指引

何时读哪个 reference:

- **写 query 时** → 读 `references/query_templates.md`(11 个方向的 query body 模板)
- **整合报告时** → 读 `references/report_template.md`(10 节结构 + 表格示例)
- **遇到踩坑时** → 读 `references/pitfalls.md`(完整踩坑清单 + 决策树)
- **报告写完后** → 读 `references/quality_check.md`(质量检查 + 补查询迭代,**必做**)
- **用户要 HTML 时** → 用 `scripts/md_to_html.py`(三档优先级转换,内嵌 CSS,响应式)

---

## 一句话总结

**博查 API + summary 字段 + 任务间数据复用 + 4+4+1 批次 + 跨城市标准化 SOP + 质量检查迭代 = 11-15 次调用产出 20KB+ 高质量图文报告,覆盖 11 个调查方向。**

记住 5 个关键节点:**先算时间 → 设计 query → 4 路并行 → 按模板整合 → 质量检查迭代**(Step 8 不可跳过)→ **HTML 输出**(Step 9 条件触发)。
