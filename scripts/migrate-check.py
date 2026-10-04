#!/usr/bin/env python3
"""双写一致性检查：对比 Prometheus 与 VictoriaMetrics 在双写阶段的数据.

用法: python3 scripts/migrate-check.py [PROM_URL] [VM_URL]
默认: http://localhost:9090 http://localhost:8428
退出码 0=一致，1=有差异。
"""
import json
import sys
import urllib.parse
import urllib.request

PROM = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9090"
VM = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8428"

# up: 逐实例对比；count: 对比总数
QUERIES = ["up", "count(up)"]


def query(base, q):
    url = base + "/api/v1/query?" + urllib.parse.urlencode({"query": q})
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.load(r)
    if data.get("status") != "success":
        raise RuntimeError(f"{base} 查询失败: {data}")
    out = {}
    for item in data["data"]["result"]:
        key = tuple(sorted(item["metric"].items()))
        out[key] = item["value"][1]
    return out


def main():
    failed = False
    for q in QUERIES:
        try:
            a, b = query(PROM, q), query(VM, q)
        except Exception as e:  # noqa: BLE001
            print(f"[ERROR] {q}: {e}")
            failed = True
            continue
        only_prom = set(a) - set(b)
        only_vm = set(b) - set(a)
        diff_val = {k for k in set(a) & set(b) if a[k] != b[k]}
        if not only_prom and not only_vm and not diff_val:
            print(f"[OK] {q}: 双方一致（{len(a)} 条序列）")
        else:
            failed = True
            print(f"[DIFF] {q}: 仅Prometheus有 {len(only_prom)} 条，"
                  f"仅VM有 {len(only_vm)} 条，值不一致 {len(diff_val)} 条")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
