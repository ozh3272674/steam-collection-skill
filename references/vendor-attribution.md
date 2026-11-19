# 厂商归属与国别判定

判定「某款游戏该归哪个厂商类」以及「该厂商属于哪个地区」，是分类里最容易出错、
也最难靠自动化解决的一环。本文沉淀三套可复用方法：**厂商抽取**、**国别判定**、
**集团口径统一**。

---

## 一、先抽「去重厂商」，不要逐款游戏查

厂商类往往成员多但厂商高度长尾。按游戏查很贵，按厂商查一次建表、终身复用，
增量新游戏直接查表。只对**判定不动的厂商**做联网核实。

厂商来源：元数据的 `developer` + `publisher`（去重后建表）。

> ⚠️ **本地元数据常只记主发行商，丢弃联合发行。**
> 涉及「厂商够格立集 vs 落 D 类」的边界判定时，必须查 Steam `appdetails` API 的
> `publishers` 数组，不能只信本地字段。

已验证的三例（都是同一家白标发行子公司）：

| 游戏 | 本地 publisher | 官方 publishers |
|---|---|---|
| Sifu | Sloclap | Sloclap + **Kepler Interactive** |
| En Garde! | Fireplace Games | Fireplace Games + **Kepler Ghost** |
| Eternights | Studio Sai | Studio Sai + **Kepler Ghost** |

`Kepler Ghost` 是 Kepler Interactive 创立的白标发行子公司，本地字段对不上集名。
→ 必须维护**子公司映射表**：`{"Kepler Ghost": "Kepler Interactive"}`。

```bash
# 低并发 + 退避，避开 HTTP 429 限流；缓存可断点续跑
python scripts/vendor_region.py fetch --appids <appid> <appid> <appid>
```

---

## 二、国别判定：三段记录，别只看名字

> **必须联网核实，严禁凭名字判断。**
> 很多中国团队用英文/拼音名（`AsicxArt`=四川成都、`Hunter Studio`=广州），
> 反而一些看着像中国的名字是海外的。`supported_languages` 字段也没用——
> 简体中文本地化太普遍，无法区分。

判定输出用序号（厂商名常含英文逗号，写名字会破坏 CSV）：

```
序号,地区,依据
```

- 地区码：`CN` / `JP` / `KR` / `EUUS`（欧美澳新）/ `OTHER`
- **`CN` = 中国大陆 + 港澳台**；中国团队/中国人创立、注册海外 → 仍 `CN`，依据注明
- 以**开发工作室来源**为准；发行商按其**公司来源**判
- 查不到 → `OTHER`，依据写 `【存疑】`
- 知名大厂凭常识；**疑似中国/亚洲独立小厂必须 WebSearch**（每个最多 1 次）

### 母子结构必须三段记录

跨国集团最容易判错。至少区分三个层：

```
母公司注册地  /  子公司注册地  /  实际开发地
```

四类高频结构：

| 结构 | 例子 | 判定要点 |
|---|---|---|
| 日本集团 + 美国发行子公司 | Bandai Namco → Bandai Namco **America** | 集团口径日本；**但看开发方**（Counterplay 是美国） |
| 日本集团 + 美国开发子公司 | GungHo → **GungHo America**（Volta-X） | 母公司日本，开发在美国 |
| 日本集团 + 欧洲发行子公司 | Marvelous → **Marvelous Europe** | 开发方是西班牙 Nao Games |
| 中国公司 + 海外子公司 | Yoozoo → **Yoozoo (Singapore)** | 母公司中国，海外子公司仍 CN |

**集团口径 vs 实际开发方冲突时，按你要回答的问题选层，并写清依据。**

### 精确匹配，不是子串匹配

集团排查必须用 publisher **全名精确匹配**：

> ⚠️ **THQ Nordic ≠ THQ**。前者属 Embracer，独立公司。
> 子串匹配 `thq` 会把 THQ Nordic 的 31 款全部误判进 Disney。

```python
# 错：if "thq" in publisher.lower()
# 对：
if publisher.strip() == "THQ Nordic AB" or publisher.strip() == "THQ"
```

同理 `nc` 会命中 `Inc.`、`snk` 会命中 `Snkl Studio`。**厂商名匹配一律用词边界**：

```python
JP_KR_RE = re.compile(r"(?<![\w&])(" + "|".join(map(re.escape, names)) + r")(?![\w])", re.I)
```

### 壳公司马甲与同名干扰

| 陷阱 | 真相 |
|---|---|
| `KAGAMI WORKs` | 实为**成都**爱相随科技，壳马甲 |
| `NekoNeko Soft` | 实为中国 **Nekoday**（中日合作） |
| `MOR Museum Inc.` | 加拿大温哥华 VR 平台，**与森美术馆无关** |
| `Bank of Innovation` | **日本**东证上市 4393，中文圈常误认韩国 |
| `Shiro Games` | **法国**波尔多，不是波兰 |
| `Somi` | 韩国釜山个人开发者 |

**判定地区要按「实际开发团队所在地」优先，而非法人壳公司。**

---

## 三、名厂独立成类

**阈值：成员 ≥2 且「全球知名」**（知名大厂不受 ≥3 限制）。**发行商也可独立成类。**

同一游戏开发与发行分属两家时可同时进两类（多值），例如 `D31 Rocksteady;D35 WB Games`。

```json
[
  {"code": "D23", "name": "厂商-Rockstar",     "pattern": "Rockstar"},
  {"code": "D24", "name": "厂商-Freebird Games", "pattern": "Freebird Games"}
]
```

## 四、集团口径统一

**子品牌集名统一改成集团名**，避免后续扫描持续报警「成员 publisher 与集名不符」。

判定：若厂商集的**成员全部**同属某集团，而集名是该集团的子品牌，则改名。

| 改前（子品牌） | 改后（集团） |
|---|---|
| WB Games | Warner Bros. |
| BANDAI NAMCO Entertainment | Bandai Namco |
| GSC World Publishing | GSC Game World |
| PlayStation Publishing LLC | PlayStation Publishing |

**编号永不动**——编号由名字首字母决定，这 4 个改名后桶字母不变（C-W/B/G/P）。
EA / Disney 无需改——本来就是集团名。

改名会引发两个写入期问题，见 `write-guide.md`：
**墓碑 key 重复**与**新旧名并存**。

## 五、厂商吸收规则

> 厂商 A 的成员被厂商 B 吃走大部分（占 A 在库总量多数），且 A 剩余零散成员
> 不足独立立集（≤3 款）时，可把这些成员归入 B 的收藏集。

前置条件（**4 条全满足**才可用）：

1. A **必须无**现有独立收藏集（有则走优先级链铁律，成员归 A 自己）
2. A 在库总量 ≥ 5 款（够格独立）
3. A 落到 D/E 的成员 ≤ 3 款
4. **B 必须唯一确定** —— 散落在多个厂商集则不适用，转人工裁决

典型案例：The Arcade Crew 无独立集，成员散落 Gamirror（15 款）与
Maple Whispering（11 款）→ 归入成员更多的 Gamirror。

**检测脚本要整组一次性统计**：边遍历边 `del` 会漏判兄弟成员（实测 4 款只拦下 1 款）。

```python
# 错：遍历中删除
for k in ks:
    if is_hollow(k): del members[k]
# 对：先收集，再整组处理
hollow = [k for k in ks if is_hollow(k)]
for k in hollow: members.pop(k, None)
```