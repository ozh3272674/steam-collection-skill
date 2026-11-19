# -*- coding: utf-8 -*-
"""步骤4: 生成 Steam 收藏集 JSON。通用版: 类目定义来自 categories.json (不含任何预置类目)。

输入:
  step2/categories.json   类目定义数组: [{"code":"C06","name":"C06 模拟经营","group":"C",
                            "installedOnly":false,"exclusive":false}, ...] (由 agent 依 categories.md 生成)
  step2/preclassification.csv  分类表 (appid,name,installed,A_status,B_series,C_types,D_vendors,E_other,...)
输出:
  step4/steam_collections.json   -> 供 write_steam.py 写入
用法: python build_collections.py [--table 路径] [--defs 路径]
"""
import csv, json, os, base64, hashlib, time, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)

def P(*p): return os.path.join(ROOT, *p)

def arg_val(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv): return sys.argv[i + 1]
    return default

def make_id(code, salt):
    d = hashlib.sha1(("%s:%s" % (salt, code)).encode("utf-8")).digest()[:9]
    return "uc-" + base64.b64encode(d).decode("ascii")


def code_parts(code):
    """拆编号，兼容三种历史格式：
        'C-A05' -> ('C','A',5)   v4 字母分桶（桶字母参与排序）
        'C001'  -> ('C','',1)    v3 三位补零
        'D99'   -> ('D','',99)   v2 两位编号
    """
    g, body = code[0], code[1:]
    if body[:1] == "-":
        body = body[1:]
        return g, body[0], int(body[1:])
    return g, "", int(body)


def code_num(code):
    """取编号的数值部分（兼容 D9 / D99 / D099 / D100 / C-A05 各种格式）。"""
    try:
        return code_parts(code)[2]
    except ValueError:
        return 0


def fallback_codes(codes):
    """找出各大类的兜底类编号集合。

    依据 categories-guide.md 编号规范：**兜底类 = 大类内编号最大者**
    （两位编号时代写作 D99，因为当时 99 就是最大号）。

    ⚠️ 不能写成「编号以 99 开头」：编号改成三位补零后，C099 只是第 99 个
    **普通**类（实测为「厂商-indienova」7 款），真正的兜底类是最大号
    （实测 C167 厂商-中国厂商 146 款）。按 99 判定会把普通类错排到最后。

    带桶字母的 v4 格式（C-A05）先比桶再比号，兜底 C-Z99 因此恒在最后。

    类目定义里若显式写了 "fallback": true，以显式标记为准。
    """
    best, out = {}, set()
    for c in codes:
        g, b, n = code_parts(c)
        cur = (b, n)
        if g not in best or cur > best[g][0]:
            best[g] = (cur, c)
    for g, (n, c) in best.items():
        out.add(c)
    return out


def sort_key(codes, defs=None):
    """构造排序 key：大类字母 -> 非兜底优先 -> 桶字母 -> 编号数值序 -> 编码兜底。

    第四档用数值而非字符串，避免位数不一致时 C10 排到 C100 后面。
    """
    fb = resolve_fallbacks(codes, defs or [])

    def key(code):
        g, b, n = code_parts(code)
        return (g, 1 if code in fb else 0, b, n, code)

    return key


def resolve_fallbacks(codes, defs):
    """兜底集合：类目定义里的显式 fallback 标记优先，否则用「大类内最大号」。"""
    explicit = {d.get("code") for d in defs if d.get("fallback")}
    return explicit or fallback_codes(codes)

def main():
    salt = os.environ.get("COLLECTION_ID_SALT", "")
    cfgf = os.path.join(BASE, "local_config.json")
    if not salt and os.path.exists(cfgf):
        try: salt = json.load(open(cfgf, encoding="utf-8")).get("collection_id_salt", "")
        except Exception: pass
    assert salt, "缺少 collection_id_salt (local_config.json 或环境变量 COLLECTION_ID_SALT)"
    table = arg_val("--table", P("step2", "preclassification.csv"))
    defs_f = arg_val("--defs", P("step2", "categories.json"))
    rows = list(csv.DictReader(open(table, encoding="utf-8-sig")))
    defs = json.load(open(defs_f, encoding="utf-8"))
    by_appid = {r["appid"]: r for r in rows}
    FIELD = {"A": "A_status", "B": "B_series", "C": "C_types", "D": "D_vendors", "E": "E_other", "F": "F_tags"}
    order = [d["code"] for d in defs]
    # 兜底类强制排各大类最后（显式 fallback 标记优先，否则取大类内最大编号）
    order.sort(key=sort_key(order, defs))
    members = {c: [] for c in order}
    for r in rows:
        for c in order:
            if c in (r.get(FIELD[c[0]]) or "").split(";"):
                members[c].append(int(r["appid"]))
    ts = int(time.time())
    entries, out_defs, summary = [], [], []
    for c in order:
        mem = sorted(set(members[c]))
        if not mem: continue
        d = next(x for x in defs if x["code"] == c)
        cid = make_id(c, salt); key = "user-collections." + cid
        val = json.dumps({"id": cid, "name": d["name"], "added": mem, "removed": []},
                         ensure_ascii=False, separators=(",", ":"))
        entries.append([key, {"key": key, "timestamp": ts, "value": val, "version": "2658",
                              "conflictResolutionMethod": "custom", "strMethodId": "union-collections"}])
        out_defs.append({"id": cid, "code": c, "name": d["name"], "group": c[0], "count": len(mem),
                         "installedOnly": d.get("installedOnly", c[0] == "A"),
                         "exclusive": d.get("exclusive", c[0] == "A")})
        summary.append((d["name"], len(mem)))
    outd = P("step4"); os.makedirs(outd, exist_ok=True)
    json.dump(entries, open(os.path.join(outd, "steam_collections.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(out_defs, open(os.path.join(outd, "collection_definitions.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("收藏集: %d | 游戏表: %d 行" % (len(entries), len(rows)))
    for n, k in summary: print("  %-40s %4d" % (n, k))
    print("下一步: 向用户展示写前确认清单 (见 references/write-guide.md), 确认后运行 write_steam.py")

if __name__ == "__main__":
    main()
