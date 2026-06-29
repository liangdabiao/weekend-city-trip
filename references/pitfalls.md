# 博查 API 踩坑清单 + 决策树

> 使用博查 WebSearch API 做城市调研时的常见踩坑与应对方案。
> 遇到任何异常,**先来这里查决策树**。

---

## Top 12 踩坑速查表

| # | 坑名 | 严重度 | 触发条件 | 应对 |
|---|---|---|---|---|
| 1 | Windows curl 单引号 JSON 失败 | ⭐⭐⭐⭐⭐ | `-d '{"k":"v"}'` | 必用 `-d @file.json` |
| 2 | 429 频率超限 | ⭐⭐⭐⭐ | 并行 ≥5 个 | 严格 4 路并行,触发等 60 秒 |
| 3 | include 域名过滤不稳定 | ⭐⭐⭐⭐⭐ | `include:"xxx.com"` | 不用 include,改 query 前缀 |
| 4 | freshness 太严返回空 | ⭐⭐⭐ | 冷门主题+短时段 | <5 条立刻降级 noLimit |
| 5 | summary 字段截断/为空 | ⭐⭐⭐ | 5-10% 概率 | python `summary or snippet` |
| 6 | 跨城市噪声 | ⭐⭐ | 文章偶然提及其他城市 | query 加城市前缀,人工筛选 |
| 7 | 图片 URL `//` 开头 | ⭐⭐ | 部分图片相对路径 | python 检测补 `https:` |
| 8 | 响应 < 1KB | ⭐⭐⭐⭐ | 踩坑早期信号 | 立即读取确认,降级重试 |
| 9 | totalEstimatedMatches = 10000000 | ⭐⭐ | 永远返回该值 | 完全忽略,只看 value 数组 |
| 10 | 冷门主题召回少 | ⭐⭐⭐ | 博查索引覆盖不均 | 接受现状,query 多加区域关键词 |
| 11 | 老数据(2018-2022) | ⭐⭐ | 出口编号等长尾信息 | 接受,出口编号基本不变 |
| 12 | Windows 路径 /tmp 失败 | ⭐⭐⭐ | Linux 习惯 | 用 `D:/fireclaw/` 或 `$TEMP` |

---

## 决策树(快速应对)

### 调用前的预防

```
要调用博查 API?
  ↓
确认是 Windows 环境?
  ├─ 是 → 必须用 heredoc + `-d @file.json`,不要 `-d '...'`
  └─ 否 → 也建议用文件,跨平台稳定
  
设计 query?
  ↓
有 include 参数?
  ├─ 是 → 删除!改用 query 加城市前缀
  └─ 否 → 继续
  
需要并行?
  ↓
路线数 > 4?
  ├─ 是 → 拆批次,每批最多 4 个
  └─ 否 → 继续
```

### 调用后的判断

```
收到响应
  ↓
响应 < 1KB?
  ├─ 是 → 踩坑预警!读取 JSON 确认
  │       ├─ value 数组空 → include 踩坑(坑 3)或 freshness 太严(坑 4)
  │       │                 → 降级:去 include / 改 noLimit
  │       └─ error 字段 → 看 code 字段查状态码表
  └─ 否 → 正常解析
          ↓
          value 数组长度 < 5?
          ├─ 是 → 召回不足(坑 10)
          │       ├─ 时效类任务 → 降级到 noLimit 重试
          │       └─ 长期类任务 → 接受现状,用 summary 重质不重量
          └─ 否 → 提取字段
                  
提取字段
  ↓
summary 为空?
  ├─ 是 → 用 snippet 兜底(坑 5)
  └─ 否 → 直接使用

图片 URL 以 // 开头?
  ├─ 是 → 补 https:(坑 7)
  └─ 否 → 直接使用
```

---

## 详细踩坑解析

### 坑 1:Windows curl 单引号 JSON body 失败 ⭐⭐⭐⭐⭐

**现象**:
```bash
curl -d '{"query":"深圳"}' https://api.bocha.cn/v1/web-search
# HTTP 500 Missing request body
```

**原因**:Windows 自带 curl(以及部分 Git Bash 的 curl)对单引号包裹的 JSON body 处理有问题,会把整段当单个参数解析失败。

**正确做法**:**永远用 `-d @file.json`**
```bash
cat > D:/fireclaw/bocha_gz/q1a.json << 'EOF'
{"query":"广州 周末活动","summary":true,"count":10,"freshness":"oneMonth"}
EOF
curl -s -X POST https://api.bocha.cn/v1/web-search \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d @D:/fireclaw/bocha_gz/q1a.json \
  -o D:/fireclaw/bocha_gz/r_q1a.json
```

**副收益**:每个 query 的 JSON 文件留存,方便审计和复用。

---

### 坑 2:429 频率超限 ⭐⭐⭐⭐

**现象**:并行 5-6 个 curl,前 4-5 个 200 OK,第 5/6 个开始返回 429。

**实测临界值**:
- 4 个并行:**稳定**,0 次 429
- 5 个并行:**临界**,偶发 429
- 6 个并行:**必触发** 429

**应对**:
- **严格 4 路并行**,留 1-2 个 slot 给重试
- 串行调用间隔 >1 秒
- 收到 429 后 `sleep 60` 重试,基本都能过

**批次设计**:11 次调用拆成 **4+4+3** 三个批次。

---

### 坑 3:include 域名过滤不稳定 ⭐⭐⭐⭐⭐

**现象**:
- 在某些城市/某些域名,`include:"xxx.com"` 返回 **0 条结果**
- 在另一些情况,include 匹配主域名,但召回的是子域名甚至非目标城市数据

**原因**:
- 博查的 include 算法是「域名匹配 + 索引存在」双重过滤
- 主域名索引较少(内容多在子域名)
- 子域名可能未被博查完全收录

**应对(优先级排序)**:
1. **最佳**:不用 include,在 query 里加城市前缀 + 具体景区名
   ```json
   {"query":"广州 景区 门票 优惠 暑期 2026 长隆 广州塔 白云山"}
   ```
2. **次选**:在 query 里加 "本地宝" 关键词,让博查自然召回
3. **不要用**:`include:"bendibao.com"` 或 `include:"gz.bendibao.com"`

**新规则**:**include 是降级选项,不是首选**。

---

### 坑 4:freshness 太严返回空 ⭐⭐⭐

**博查官方文档原话**:
> 推荐使用 noLimit。搜索算法会自动进行时间范围的改写,效果更佳。如果指定时间范围,很有可能出现时间范围内没有相关网页的情况,导致找不到搜索结果。

**实测策略**:

| 任务类型 | 推荐 freshness | 备选 |
|---|---|---|
| 热门主题(近期活动) | oneWeek 或 oneMonth | noLimit |
| 历史品牌(喜茶门店) | oneYear | noLimit |
| 长期资源(博物馆/5A) | noLimit | — |
| 冷门主题 | noLimit | oneYear |

**降级规则**:
- 任何 freshness=X 返回 < 5 条 → 立刻改 freshness=noLimit 重试
- 不要为了"时效性"硬用 oneWeek,有时 noLimit 召回更好

---

### 坑 5:summary 字段截断/为空 ⭐⭐⭐

**现象**:约 5%-10% 的结果 `summary` 字段为空字符串或截断到一半。

**应对**:python 降级链
```python
text = item.get('summary') or item.get('snippet') or item.get('name', '')
```

**字段优先级**:
- `summary`(AI 摘要,核心)
- `snippet`(搜索引擎摘要,备用)
- `name`(标题,兜底)

---

### 坑 6:跨城市噪声 ⭐⭐

**现象**:query=`广州 活动推荐` 偶尔返回 1-2 条北京/上海的文章(因为偶然提到"对标广州")。

**应对**:
- query **强制以城市名开头**
- 必要时重复 2-3 次("广州 周末活动 广州打卡 广州展览")
- 解析时筛选:`if '广州' not in name+summary: skip`
- 1-2 条噪声正常,人工筛选即可

---

### 坑 7:图片 URL `//` 开头 ⭐⭐

**现象**:部分 thumbnailUrl 返回相对路径(以 `//` 开头)。

**应对**:python 检测
```python
url = img.get('thumbnailUrl', '')
if url.startswith('//'):
    url = 'https:' + url
if not url.startswith('http'):
    continue  # 跳过
```

**额外过滤**:跳过 icon/logo 类图片
```python
if 'icon' in url.lower() or 'logo' in url.lower():
    continue
```

---

### 坑 8:响应 < 1KB(踩坑早期信号) ⭐⭐⭐⭐

**现象**:正常响应通常 17-30KB,踩坑响应 < 1KB。

**判断脚本**:
```bash
ls -la D:/fireclaw/bocha_*/r_*.json | awk '{print $5, $9}'
# < 1000 字节的立刻读 JSON 确认
```

**新规则**:**任何响应 < 1KB 立刻怀疑踩坑**,不要继续等。

---

### 坑 9:totalEstimatedMatches 永远是 10000000 ⭐⭐

**现象**:无论 query 多冷门,`data.webPages.totalEstimatedMatches` 都返回 10000000。

**应对**:**完全忽略该字段**,只看 `data.webPages.value[]` 数组长度和内容。

---

### 坑 10:冷门主题召回少 ⭐⭐⭐

**现象**:不同城市同主题召回量差异显著(可能在 5-15 条之间波动)。

**原因**:博查索引覆盖不均。

**应对**:
- **不要重试**(浪费调用)
- 接受现状,用 summary 重质不重量
- 提前在 query 里多写几个区域关键词提高召回

**新规则**:**召回数量不是质量指标**,5-7 条高质量 summary > 15 条低质量。

---

### 坑 11:老数据(2018-2022 年文章) ⭐⭐

**现象**:地铁出口、地标等长尾信息召回的文章偏旧。

**应对**:
- **接受历史数据**(出口编号、地标位置基本不变)
- 配合 query 加 `{当前年份}` 关键词尽量拿新数据
- 写报告时加「请出行前二次确认」安全声明

---

### 坑 12:Windows 路径 /tmp 失败 ⭐⭐⭐

**现象**:用 `/tmp/xxx.json` 报 FileNotFoundError。

**应对**:
- 用 `D:/fireclaw/` 或 `$TEMP`
- Windows 自带 curl 接受正斜杠 `D:/fireclaw/xxx.json`

---

## 失败状态码表

| HTTP | 原因 | 对策 |
|---|---|---|
| 200 | 成功 | — |
| 400 | 缺 query / 缺 Authorization | 检查 body 和 header |
| 401 | API KEY 无效 | 换 key |
| 403 | "You do not have enough money" 余额不足 | 提醒用户充值 |
| 429 | 频率超限 | 等 60 秒重试 |
| 500 | body 没传过去 | **确认用 `-d @file.json`** |

---

## 博查 API 的局限

记下博查的短板,避免在不合适的场景硬用:

| 局限 | 说明 | 应对 |
|---|---|---|
| ❌ 不支持全文 scrape | summary 是 AI 摘要 | 需要全文用专门 scrape 工具 |
| ❌ 不支持结构化 JSON | 无法自定义 schema | 用专门的结构化提取工具 |
| ❌ 不支持 JS 渲染 | summary 依赖静态 HTML | 复杂 SPA 用浏览器渲染工具 |
| ❌ 视频搜索未开放 | query 涉及视频时召回一般 | 用图文替代 |
| ⚠️ include 不分子域名 | 主域名过滤不可靠 | 用 query 前缀 |
| ⚠️ summary 偶截断 | 5-10% 概率 | snippet 兜底 |
| ⚠️ 老数据混入 | 长尾信息文章偏旧 | 接受 + 二次确认 |

---

## 一句话总结

**12 个坑 + 决策树 + 状态码表 = 遇到任何异常 30 秒内定位 + 应对**。

记住核心 3 条:
1. **Windows curl 用 `-d @file.json`**
2. **并行 4 路,不要 5 个**
3. **响应 < 1KB 立刻降级**
