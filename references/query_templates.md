# 11 个调查方向的 Query 模板

> 用法:把 `{CITY}` 替换为目标城市(广州/上海/成都/北京...),把 `{MONTH}` 替换为目标月份(7月/8月...)。
> 文件名约定:`q{任务编号}{字母}.json`(query body)、`r_q{任务编号}{字母}.json`(response)。

---

## 调查方向与 query 总览

| 任务 | 调查方向 | query 文件 | freshness | 备注 |
|---|---|---|---|---|
| 1a | 小红书近期活动(主力) | q1a.json | oneMonth | 12 条 |
| 1b | 网红打卡 + 影视取景 | q1b.json | oneMonth | 补充 UGC 视角 |
| 1c | 演唱会 + 集市 + 球赛 | q1c.json | oneWeek | 最新一周文章 |
| 1d | 博物馆 + 5A 景区 | q1d.json | noLimit | 长期资源 |
| 2a | 优惠门票 | q2a.json | oneMonth | 不用 include |
| 3a | 喜茶门店 + 购物中心 | q3a.json | oneYear | 历史 + 现状 |
| 3b | 喜茶主题店盘点 | q3b.json | noLimit | LAB/DP/PINK |
| 4a | 美食街 | q4a.json | noLimit | 区域关键词 |
| 4b | city walk 路线 | q4b.json | noLimit | 路线视角 |
| 5a | 地铁路网总览 | q5a.json | noLimit | 全网级别 |
| 5b | 地铁出口细节 | q5b.json | noLimit | 关键站点 |

**总计 11 次调用**(可在 3 个批次内完成:4+4+3)。

---

## 任务 1:近期活动(4 次 query 对冲 freshness)

### q1a.json — 小红书近期城市活动(主力)

```json
{"query":"{CITY} 周末活动 展览 演出 市集 演唱会 {MONTH}","summary":true,"count":12,"freshness":"oneMonth"}
```

**示例**(目标=广州,月份=2026年7月):
```json
{"query":"广州 周末活动 展览 演出 市集 演唱会 2026年7月","summary":true,"count":12,"freshness":"oneMonth"}
```

### q1b.json — 网红打卡 + 影视取景

```json
{"query":"小红书 {CITY}拍照 网红 打卡 同城活动 暑期 夏日","summary":true,"count":10,"freshness":"oneMonth"}
```

**示例**:
```json
{"query":"小红书 广州拍照 网红 打卡 同城活动 暑期 7月","summary":true,"count":10,"freshness":"oneMonth"}
```

### q1c.json — 演唱会 + 集市 + 球赛(最新一周)

```json
{"query":"{CITY} {MONTH} 演唱会 集市 球赛 体育 比赛 周末去哪 2026 最新","summary":true,"count":12,"freshness":"oneWeek"}
```

**示例**:
```json
{"query":"广州 7月 演唱会 集市 球赛 体育 比赛 周末去哪 2026 最新","summary":true,"count":12,"freshness":"oneWeek"}
```

### q1d.json — 博物馆 + 5A 景区(长期资源)

```json
{"query":"{CITY} 博物馆 推荐 5A 景区 必去 打卡 2026","summary":true,"count":12}
```

**示例**:
```json
{"query":"广州 博物馆 推荐 5A 景区 必去 打卡 2026","summary":true,"count":12}
```

**说明**:博物馆和 5A 景区是长期资源,不依赖时效,用 noLimit。

---

## 任务 2:优惠门票(1 次 query,不用 include!)

### q2a.json — 暑期优惠门票

```json
{"query":"{CITY} 景区 门票 优惠 暑期 {MONTH} 学生 考生 特惠","summary":true,"count":12,"freshness":"oneMonth"}
```

**示例**:
```json
{"query":"广州 景区 门票 优惠 暑期 2026 长隆 广州塔 白云山","summary":true,"count":12,"freshness":"oneMonth"}
```

**关键提醒**:
- ❌ **不要用 `"include":"bendibao.com"`**:博查的 include 在不同城市表现不稳定,可能返回 0 条,也可能召回非目标城市数据
- ✅ **改用 query 加城市前缀 + 具体景区名**(如长隆/广州塔/白云山)
- ✅ 想要本地宝内容,query 里加 "本地宝" 关键词,让博查自然召回

**踩坑降级**:如果响应 < 1KB(0 条结果),立即去掉任何过滤条件重试。

---

## 任务 3:喜茶热点(2 次 query)

### q3a.json — 旗舰店 + 购物中心历史

```json
{"query":"{CITY} 喜茶 旗舰店 打卡 购物中心 商场 黑金店 2026","summary":true,"count":10,"freshness":"oneYear"}
```

**示例**:
```json
{"query":"广州 喜茶 旗舰店 打卡 太古汇 天环广场 正佳 黑金店 2026","summary":true,"count":10,"freshness":"oneYear"}
```

**技巧**:query 里直接列出该城市的主要购物中心名(可先 WebSearch 一下"XX城市十大购物中心"),提高召回精度。

### q3b.json — 主题店盘点(LAB/DP/PINK)

```json
{"query":"{CITY} 喜茶 lab店 DP店 主题店 推荐","summary":true,"count":10}
```

**示例**:
```json
{"query":"广州 喜茶 lab店 DP店 主题店 推荐","summary":true,"count":10}
```

**说明**:
- LAB 店:产品实验室(蛋糕/茶饮创意)
- DP 店:Day Dreamer Project(空间设计概念店)
- PINK 店:粉色主题(女性向)
- 每个城市主题店类型不同,需要从 summary 字段里识别

---

## 任务 4:美食街 + city walk(2 次 query)

### q4a.json — 美食街

```json
{"query":"{CITY} 美食街 推荐 夜市 {区域1} {区域2} {区域3} {区域4} 2026","summary":true,"count":12}
```

**示例**:
```json
{"query":"广州 美食街 推荐 夜市 北京路 上下九 西关 体育西 2026","summary":true,"count":12}
```

**关键**:query 里必须列出该城市的主要美食区域(可先 WebSearch 一下"XX城市美食街区"),否则召回量会偏少。

各城市主要美食街区参考:
- 广州:北京路、上下九、西关、体育西、十三行
- 深圳:东门、华强北、上梅林、八卦岭、盐田、车公庙、皇岗村、水围村
- 上海:城隍庙、田子坊、新天地、云南南路、虹泉路、吴江路
- 北京:簋街、南锣鼓巷、王府井、护国寺、牛街
- 成都:锦里、宽窄巷子、玉林、华兴、奎星楼街

### q4b.json — city walk 路线

```json
{"query":"{CITY} city walk 路线 推荐 老城区 历史街区 拍照 2026","summary":true,"count":10}
```

**示例**:
```json
{"query":"广州 city walk 路线 推荐 老城区 历史街区 拍照 2026","summary":true,"count":10}
```

**说明**:city walk 关注"路线"而非单点,query 强调"路线 + 老城区"。

---

## 任务 5:地铁路线(2 次 query)

### q5a.json — 线网总览

```json
{"query":"{CITY} 地铁 线路图 2026 最新 {主要区域1} {主要区域2} {主要区域3}","summary":true,"count":10}
```

**示例**:
```json
{"query":"广州 地铁 线路图 2026 最新 天河 海珠 越秀 白云 番禺","summary":true,"count":10}
```

**目标信息**:
- 已开通线路数 + 运营里程
- 服务热线
- 主要换乘枢纽
- 在建 / 规划新线

### q5b.json — 关键站点出口细节

```json
{"query":"{CITY}地铁 站点 出口 {地标1} {地标2} {地标3} {地标4}","summary":true,"count":10}
```

**示例**:
```json
{"query":"广州地铁 站点 出口 长隆 广州塔 北京路 体育西 珠江新城","summary":true,"count":10}
```

**目标信息**:
- 主要景点 / 商场的具体出口编号(A/B/C/D)
- 出口直达的商场清单
- 换乘站结构

**说明**:出口编号数据可能偏旧,但出口编号基本不变,可放心使用。

---

## 完整执行批次

### 批次 1(4 路并行,任务 1+2+3+4 主力)

```bash
curl ... -d @q1a.json -o r_q1a.json &
curl ... -d @q3a.json -o r_q3a.json &
curl ... -d @q4a.json -o r_q4a.json &
curl ... -d @q5a.json -o r_q5a.json &
wait
```

### 批次 2(4 路并行,补充查询)

```bash
curl ... -d @q1b.json -o r_q1b.json &
curl ... -d @q1c.json -o r_q1c.json &
curl ... -d @q3b.json -o r_q3b.json &
curl ... -d @q4b.json -o r_q4b.json &
wait
```

### 批次 3(3 路并行,收尾)

```bash
curl ... -d @q1d.json -o r_q1d.json &
curl ... -d @q2a.json -o r_q2a.json &
curl ... -d @q5b.json -o r_q5b.json &
wait
```

**总计 11 次调用,3 个批次,预计 30-60 秒完成**。

---

## 城市关键词速查表

### 主要城市的热门地标(填入 query 提高召回)

| 城市 | 购物中心 | 美食区 | 地标 | 5A 景区 |
|---|---|---|---|---|
| **广州** | 太古汇、正佳、天河城、天环、K11、东方宝泰、广百、万菱汇、igc、花城汇 | 北京路、上下九、西关、体育西 | 广州塔、白云山、珠江夜游 | 长隆、白云山、西樵山(近) |
| **深圳** | 万象天地、海岸城、壹方城、海雅缤纷城、深业上城、卓悦中心、欢乐港湾 | 东门、华强北、上梅林、八卦岭、盐田、车公庙、皇岗村 | 世界之窗、欢乐谷、平安金融中心 | 世界之窗、欢乐谷、东部华侨城、观澜湖 |
| **上海** | 南京路、淮海路、新天地、静安寺、徐家汇、五角场 | 城隍庙、田子坊、云南南路、吴江路、虹泉路 | 外滩、东方明珠、迪士尼 | 迪士尼、东方明珠、上海野生动物园 |
| **北京** | 三里屯、王府井、西单、SKP、国贸 | 簋街、南锣鼓巷、王府井、护国寺、牛街 | 故宫、长城、天坛 | 故宫、长城、颐和园、天坛 |
| **成都** | 太古里、IFS、万象城、银泰中心 | 锦里、宽窄巷子、玉林、华兴 | 大熊猫基地、宽窄巷子 | 大熊猫基地、青城山、都江堰 |

---

## query 设计的 4 要素法则

每个 query 必须包含:

1. **地点**:城市名(强制开头,可重复 2-3 次)
2. **主题**:活动/门票/喜茶/美食街/地铁/city walk/博物馆/5A 等
3. **时效**:本周末 / 下周末 / 7月 / 暑期 / 2026
4. **品类**:演唱会/展览/市集 / 旗舰店/LAB/DP / 北京路/上下九

**反例**:
- ❌ `广州 活动`(太宽泛,召回杂)
- ❌ `周末活动`(缺地点,召回全国)
- ❌ `广州`(只一个词,无法定位主题)

**正例**:
- ✅ `广州 周末活动 展览 演出 市集 演唱会 2026年7月`(全要素)
- ✅ `广州 喜茶 lab店 DP店 主题店 推荐`(主题明确)
- ✅ `广州 博物馆 推荐 5A 景区 必去 打卡 2026`(品类清晰)

---

## 高级技巧

### 多角度对冲(对时效性强的任务)

活动类任务建议 3 次 query:
- oneMonth:拿"近期发布 + 介绍未来活动"的文章
- oneWeek:拿最新一周的预告
- noLimit:兜底

### 数据复用(任务间)

任务 1(活动)的 summary 里通常已包含 60-70% 的门票信息,**任务 2 可以直接复用任务 1 的数据**,只在缺口处追加 1 次 query。

### 失败立即降级

任何响应 < 1KB 立刻怀疑踩坑,读取确认后:
- 去掉 include
- 改 freshness 到 noLimit
- 简化 query(去掉品类关键词)

### 图片提取

图文版报告必须从 `data.images.value[].thumbnailUrl` 提取图片,每节选 1-2 张代表图。

```python
# 检测 // 开头补 https:
url = img.get('thumbnailUrl', '')
if url.startswith('//'):
    url = 'https:' + url
```

---

## 一句话总结

**11 个调查方向 → 11 次 API 调用 → 4+4+3 三批次并行 → 30-60 秒完成数据采集 → 按 10 节模板整合图文报告**。
