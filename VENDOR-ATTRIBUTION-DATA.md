# 厂商归属参考（VENDOR-ATTRIBUTION-DATA）

本文件记录**厂商侧**的归属判定：集名形态、集团口径映射、发行代理制识别、以及规模分布。

> 数据来源：一次 3991 款游戏规模真实库，含 **181 个厂商集合、2264 款归厂商游戏**。
> **脱敏范围**：本文只保留方法、映射表与聚合统计。
> 不含 SteamID、本机路径、appid 清单或收藏集成员明细。
> 厂商名称与集团关系属公开商业事实，可安全公开；文中出现的游戏名均为公知商业作品。

---

## 一、厂商集的规模分布（决定分类策略）

| 规模档 | 集合数 | 占比 | 解读 |
|---|---|---|---|
| 50 款以上 | 3 | 1.7% | 超大厂商，成员数接近单类上限 |
| 30–49 款 | 16 | 8.8% | 大厂主力区间 |
| 20–29 款 | 13 | 7.2% | 中型厂商 |
| 10–19 款 | 41 | 22.7% | **最密集区间** |
| 5–9 款 | 70 | 38.7% | **最大区间**，长尾独立工作室 |
| 3–4 款 | 24 | 13.3% | 够格立集的临界区 |
| 1–2 款 | 14 | 7.7% | **应考虑合并的区间** |

**关键结论**：

1. **长尾极重** —— 5 款以下的小厂商集合占 60%，是分类工作量的主要来源
2. **厂商集天然适合步长 5 的编号** —— 成员数会随库增长而增加，编号必须留插队空间
3. **1–2 款的集合值得复核** —— 它们往往是「够不够格立集」的边界情况，
   应考虑是否并入更合适的集（见第五节吸收规则）

---

## 二、厂商集名的四种形态（编号桶字母的依据）

本技能的编号规则是**桶 = 集名首字母**（中文转拼音），但实测集名形态有 4 类，
其中一类会让「首字母」规则失效：

| 形态 | 数量 | 样例 | 编号处理 |
|---|---|---|---|
| 纯英文 | 158 | `Electronic Arts` | 首字母 → `C-E` |
| 英文含标点 | 17 | `100 Cozy Games`、`2K`、`11 bit studios` | 取首个**数字或字母** |
| 数字开头 | 6 | `2K`、`100 Cozy Games`、`101XP` | 数字无字母，**需人工指定桶** |
| 中文为主 | 0 | — | 转拼音首字母 |

⚠️ **数字开头的厂商是编号规则的真实边界情况**。实测有 6 个这类集合，
它们的桶字母无法从名字自动推导，必须人工分配并在映射表里固化，
否则每次重跑编号都会漂移。

---

## 三、集团口径映射表（必备）

**这是本文件最重要的一节。** 库里的 `publisher` 字段记的是**具体发行品牌**，
不是集团；而分组时希望按集团归拢。两者的对照关系：

| 集名（集团口径） | 库内实际出现的 publisher 变体 |
|---|---|
| `Electronic Arts` | `PopCap Games, Inc.`、`Codemasters` |
| `Disney` | `LucasArts` |
| `Xbox Game Studios` | `Double Fine Productions` |
| `Warner Bros.` | `WB Games` |
| `Bandai Namco` | `BANDAI NAMCO Entertainment` |
| `2K` | `Gearbox Publishing`（反向：被 2K 发行） |
| `GSC Game World` | `GSC World Publishing` |
| `PlayStation Publishing` | `PlayStation Publishing LLC` |

**实测影响面**：用朴素分词做「集名 vs publisher 字符串包含」校验时，
**211 / 2243 款（9.4%）会报「不符」** —— 其中绝大多数是上表这类子品牌关系，
不是真错误。

### 集团口径的判定原则

1. **子品牌集名统一改成集团名**。原因不只是好看 —— 后续每次扫描都会跑
   「成员 publisher 与集名是否相符」的校验，子品牌名会持续触发假报警
2. **改名后编号绝不动**。因为编号由名字首字母决定，
   改集团名后桶字母不变（如 `WB Games`→`Warner Bros.` 仍是 `C-W`）
3. **EA / Disney 原本已是集团名**，无需改动

---

## 四、⚠️ 三类必须人工确认的归属（自动化无法可靠判定）

实测中以下三类会产生「看起来不合理但其实合理」的错位，**任何自动规则都会误判**。

### 4.1 发行代理制（最容易误判，占不符项的大头）

有些「厂商集」其实是**发行代理 / 发行品牌**，聚合了大量不同开发者的游戏。
实测每集成员来自多少个不同 publisher，可作为识别依据：

| 集合 | 成员款数 / 不同 publisher 数 | 说明 |
|---|---|---|
| `WhisperGames` | 10 款 / 9 个 | 几乎一款一个开发者，典型代理制 |
| `PLAYISM` | 8 款 / 6 个 | 多国分区域发行 |
| `Untold Tales` | 41 款 / 7 个 | 大集合高度聚合 |
| `Dear Villagers` | 33 款 / 4 个 | 高度聚合 |
| `Raw Fury` | 37 款 / 3 个 | **仅 3 个开发者**，聚合度最高 |
| `Gamirror Games` | — / — | 中文发行商 |
| `Gamera Games` | 7 款 / 7 个 | 一款一个开发者 |
| `GrabTheGames` | 24 款 / 6 个 | 中文发行商 |

**判定建议**：这类集子的成员 publisher 天生与集名不符，
**不要把它们当错误去修正**，应在校验规则里加入白名单。

**自动化识别规则**：成员来自 **3 个以上互不相关的开发者**、
且这些开发者在库内均无独立集合 → 大概率是发行代理而非开发商。
实测符合此特征的集合占「不符项」的大头。

```python
def is_publisher_aggregator(collection, meta, min_devs=3):
    devs = {(meta.get(a) or {}).get("publisher") or "?" for a in collection["成员"]}
    return len(devs) >= min_devs
```

### 4.2 集团内子品牌被单独立集

`Double Fine Productions` 已并入 Xbox Game Studios、`LucasArts` 已并入 Disney。
若散落出独立集合，属于口径不统一，应合并。

### 4.3 MOD 与社区内容（实测 12 款）

Valve 集内有 12 款 MOD / 社区内容（如 Half-Life 2 的 VR Mod、MMOD），
publisher 分别是 `Flat2VR Studios`、`Gunship_Mark_II` 等独立开发者。

**这是用户明确决定保留的**（不剔除、不拆分）—— 因为它们在库中就是真实存在的条目。
处理原则：**尊重用户对 MOD 的处置决定**，不要自作主张清理。

---

## 五、厂商吸收规则（当小厂商被其他集掏空时）

### 触发条件（4 条全满足才可用）

厂商 A 的成员被厂商 B 吃走大部分（占 A 在库总量多数），且 A 剩余成员零散、
不足独立立集（**≤ 3 款**）时，可把这些成员归入 B 的收藏集。

1. **A 必须没有**现有独立收藏集（有则走铁律，成员归 A 自己）
2. **A 在库总量 ≥ 5 款**（够格独立）
3. **A 落到 D/E 类的成员 ≤ 3 款**
4. **B 必须唯一确定** —— 成员散落在多个厂商集时不适用，转人工裁决

### 实测应用记录

| 被吸收方 | 成员数 | 归入 | 依据 |
|---|---|---|---|
| `Yogscast Games` | 3 | Gamersky Games | 无独立集 + 规模达标 + 接收方唯一 |
| `Freebird Games` | 3 | Serenity Forge | 同上 |
| `The Arcade Crew` | 2 | Gamirror | **两方都有集时比规模**：15 款 > 11 款 |
| `Crytek`（Crysis 3 款） | 3 | Electronic Arts | 全系列发行商均为 EA |

### 反例：不要滥用

`Far Cry` 系列虽然由 Crytek 开发，但**发行商是 Ubisoft**，
按本技能口径（发行商优先）**不迁移** —— 开发与发行的口径差异是这类规则最容易出错的地方。

---

## 六、厂商归属的三个高频错误

### 6.1 子串匹配把厂商判错

```
thq    → 命中 "THQ Nordic"（31 款全部误判进 Disney）
         但 THQ Nordic 属 Embracer，与美泰 THQ 是两家公司
nc     → 命中 "Inc."（几乎每条都中）
snk    → 命中 "Snkl Studio"
```

**正解**：一律用**词边界**匹配，并优先精确匹配 publisher 全名。

```python
re.compile(r"(?<![\w&])thq(?![\w])", re.I)
```

**实测收益**：修正后候选从 152 降到 76 —— **一半是误报**。

### 6.2 本地元数据只记主发行商，丢弃联合发行

`library_tags.json` 的 `publisher` 字段只保留第一个发行商。实测三例：

| 游戏 | 本地记录 | Steam 官方 publishers |
|---|---|---|
| Sifu | Sloclap | `['Sloclap', 'Kepler Interactive']` |
| En Garde! | Fireplace Games | `['Fireplace Games', 'Kepler Ghost']` |
| Eternights | Studio Sai | `['Studio Sai', 'Kepler Ghost']` |

**影响**：涉及「厂商够格立集 vs 落 D 类」的边界判定时，
仅凭本地字段会把本该进厂商集的游戏错分到 D 类。

**正解**：这类边界判定**必须查 Steam appdetails API 的 `publishers` 数组**，
并维护子公司映射表（本地名字对不上集名时用）：

```
Kepler Ghost → Kepler Interactive
（Kepler Ghost 是 2023 年 Kepler Interactive 创立的白标发行子公司）
```

实测扫描 594 个 appid，找到 31 个联合发行条目。

### 6.3 壳公司马甲

厂商名不等于实际开发团队所在地。实测：

| 厂商名 | 实际 |
|---|---|
| `KAGAMI WORKs` | 中国成都公司 |
| `NekoNeko Soft` | 中国 Nekoday |
| `MOR Museum Inc.` | 加拿大温哥华 VR 平台（与东京森美术馆无关） |
| `Shiro Games` | 法国波尔多（常被误认为波兰） |

**正解**：按「实际开发团队所在地」判断，不按法人壳公司注册地。
拿不准时**标注存疑，不要猜**。

> 地区判定（厂商国别）的完整方法见 `references/vendor-attribution.md`
> 与 `references/region-classes.md`。

---

## 七、厂商分类的自动化校验脚本

```python
import json, re, collections

ALIAS = {
    "Electronic Arts": ["PopCap Games", "Codemasters", "Electronic Arts"],
    "Disney":          ["LucasArts", "Disney"],
    "Xbox Game Studios":["Double Fine", "Xbox Game Studios"],
    # ... 按第三节的映射表补全
}
# 发行代理白名单：成员 publisher 天生与集名不符
PUBLISHER_AGGREGATORS = {"WhisperGames", "PLAYISM", "Untold Tales", "Dear Villagers",
                         "Raw Fury", "Gamirror Games", "Gamera Games", "GrabTheGames"}

def check_vendor(baseline, meta):
    """返回 (正常, 需人工确认, 白名单豁免) 三个计数"""
    ok = review = exempt = 0
    for c in baseline["类目定义"]:
        if not c["code"].startswith("C-") or c["code"].startswith("C-Z"):
            continue
        name = c["name"].split("厂商-", 1)[-1]
        if name in PUBLISHER_AGGREGATORS:
            exempt += len(c["成员"]); continue
        variants = ALIAS.get(name, [name])
        for appid in c["成员"]:
            pub = (meta.get(appid) or {}).get("publisher") or ""
            if not any(v.lower() in pub.lower() for v in variants):
                review += 1
            else:
                ok += 1
    return ok, review, exempt
```

**使用要点**：`review` 计数不应直接当错误处理。
实测 211 项不符里，真正需要行动的只有个位数，其余是子品牌与发行代理。

---

## 八、编号规则（厂商侧）

详见 `references/numbering.md`，厂商侧三条要点：

1. 编码格式 `C-{桶字母}{编号} 厂商-{公司名}`，例：`C-E10 厂商-Electronic Arts`
2. **桶 = 名字首字母**（中文转拼音）；数字开头的厂商人工指定桶
3. **编号写入映射表后永不重排**。桶内从 05 起、步长 5 —— 每个厂商有 4 个空位，
   给同系列新品插队用（实测已有 `C-A05` 与 `C-A10` 同厂商的情况）
4. 保留位 96/97/98；兜底类固定 99