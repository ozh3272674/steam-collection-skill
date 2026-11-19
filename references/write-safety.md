# 写入 Steam 云存储：两个致命坑与安全流程

写入 `cloud-storage-namespace-1.json` 是整个流程里**唯一不可逆**的步骤。
本文记录两个实测踩到的致命坑，以及必须遵守的安全流程。

---

## 一、安全流程（固定顺序，不可跳步）

1. **确认 Steam 完全退出**

   ```bash
   tasklist | findstr /i "steam.exe steamwebhelper steamservice"
   ```

   三个进程**必须全为 0**。任何一项非 0 就停下。

   > ⚠️ **Steam 运行中禁止写入。** 客户端退出时会用内存里的旧状态覆盖文件，
   > 你的改动会凭空消失。实测发生过两次「AI 说可以写了，但 Steam 没退」。

2. **双份备份**

   ```
   <你的项目目录>/写入前备份_<时间戳>/
   step4/backup/
   ```

3. `--dry-run` 预览载荷
4. 正式写入
5. 写入后核验（见下）
6. **重启 Steam 后再复查一次**，确认未被客户端覆写

---

## 二、坑 1：`is_deleted` 墓碑造成重复 key

live 文件里存在形如：

```json
{"key":"user-collections.uc-xxx","is_deleted":true,"version":"7363"}
```

的条目 —— **无 `value` 字段**，但 key 以 `user-collections` 开头。

若原样带上，某条墓碑的 key 会与本次新建集合的 id 撞车，
`write_steam.py` 抛 `AssertionError: 存在重复 key, 中止`（实测 C-Z97 撞了）。

→ 载荷生成器读 live 文件时必须有 `dropped_tombstones` 分支：

```python
def load_live(path):
    entries = json.load(open(path, encoding="utf-8"))
    dropped = 0
    for e in entries:
        if e.get("key","").startswith("user-collections") and "value" not in e:
            dropped += 1          # 墓碑，丢弃
            continue
        yield e
    log(f"丢弃墓碑 {dropped} 条")
```

---

## 三、坑 2：改名后旧名集合与新名并存

厂商集改名后，旧名在基线里已不存在 → 被「基线外 live 收藏集」逻辑当成**要保留**
→ 载荷里新旧名都在 → 客户端出现重复集。

→ 载荷生成器必须维护 `RENAMED` 显式映射，旧名不进载荷：

```python
RENAMED = {
    "C-W15 厂商-WB Games":                      "C-W15 厂商-Warner Bros.",
    "C-B15 厂商-BANDAI NAMCO Entertainment":    "C-B15 厂商-Bandai Namco",
    "C-G35 厂商-GSC World Publishing":          "C-G35 厂商-GSC Game World",
    "C-P25 厂商-PlayStation Publishing LLC":    "C-P25 厂商-PlayStation Publishing",
}
```

---

## 四、`cloud-storage-namespace-1.json` 结构

踩过的坑，逐条列出：

| 项 | 事实 |
|---|---|
| 顶层结构 | `[[key, value], ...]` —— **数组，不是 dict** |
| 遍历方式 | `items.items()` 会报 `AttributeError` |
| value 字段 | 里面的 `value` 是 **JSON 字符串**，需二次 `json.loads` |
| 成员键名 | 在 `added`（**不是** `apps`） |
| 收藏集 key | 以 `user-collections` 开头 |
| 系统收藏集 | 「收藏夹」「已隐藏」，**必须保留** |
| 无 value 条目 | key 以 user-collections 开头但无 value → 墓碑，丢弃 |

读取样板：

```python
import json
raw = json.load(open(LIVE, encoding="utf-8"))
for key, value in raw:                      # 顶层是数组，直接解包
    if not key.startswith("user-collections"):
        continue
    if value is None:
        continue                           # 墓碑
    data = json.loads(value["value"])       # 二次解析
    name = data.get("name")
    apps = data.get("added", [])            # 成员在 added
```

**Steam API 直连需绕过本机代理**：`urllib.request.ProxyHandler({})`。

---

## 五、写前校验器

生成载荷后、真正写入前，必须跑校验器。校验器要满足：

**1. 变更层的键名各不相同，必须列全**

各轮迁移条目键名不统一，漏一层就会把正常来源集全报成「意外」：

| 层 | 迁移条目键名 |
|---|---|
| v9 / v10 / v11 | `真命中` |
| v12 | `新建收藏集[].真命中` |
| v13 / v14 | `迁移计划` |
| v17 | `吸收迁移` |
| v18 | `迁移` |

**2. 短码 vs 全名必须统一后比较**

变更层存短码（`C-N25`），集合名是全名（`C-N25 厂商-New Reality Games`）。
比较时统一取短码：

```python
short = lambda n: n.split(" ", 1)[0]
# 错：if full_name.startswith(code)   # 方向会反
if short(full_name) == code:
```

**3. 改名必须识别**

改名 = 集合一增一删但成员不变。若不识别，会误报「移除了收藏集」。
→ 维护 `RENAME` 白名单，把改名对从「实质增删」中剔除。

---

## 六、写入后核验

必查项，缺一不可：

1. 系统收藏集「收藏夹」「已隐藏」**仍在**
2. **非收藏集数据条目零变化**（其余 ~1100 条不能被破坏）
3. 成员**逐款一致**（不是只比数量）
4. **无陈旧残留**：改名后的旧名集合必须已消失
5. 抽查关键集合与迁移 appid 的归属正确

---

## 七、备份文件清理的坑

清理「同轮备份」必须**按时间戳前缀把 json + csv 配对处理**。

```python
# 错：glob(prefix+'*') 按 mtime 排序后删 fs[1:]
#      两个文件 mtime 略有差异 → 误删 json 只留 csv
# 对：只 glob .json，删除时替换扩展名删配对
for f in glob.glob(prefix + "*.json"):
    os.remove(f)
    c = f.replace(".json", ".csv")
    if os.path.exists(c): os.remove(c)
```