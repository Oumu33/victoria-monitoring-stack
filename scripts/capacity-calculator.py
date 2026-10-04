#!/usr/bin/env python3
"""容量计算器：输入指标规模，输出 VictoriaMetrics 单机版的机器配置建议.

用法: python3 scripts/capacity-calculator.py
"""
import math

def ask(prompt, default):
    raw = input(f"{prompt} [{default}]: ").strip()
    return type(default)(raw) if raw else default

def main():
    print("== VictoriaMetrics 容量计算器（单机版，估算值偏保守）==\n")
    series = ask("活跃时间序列数（万）", 100) * 10000
    ingest = ask("每秒写入数据点（万）", 10) * 10000
    retention_months = ask("保留时长（月）", 12)

    # 经验公式
    mem_gb = max(2, math.ceil(series * 1.2 / 1024 / 1024 / 1024))
    # 每天点数 * 1字节 * 天数 * 2(余量) -> GB
    disk_gb = max(20, math.ceil(ingest * 86400 * 1 * (retention_months * 30) * 2 / 1e9))
    cpu = max(2, math.ceil(ingest / 100000))

    print("\n-------- 建议配置 --------")
    print(f"内存: {mem_gb} GB")
    print(f"磁盘: {disk_gb} GB（{retention_months} 个月）")
    print(f"CPU : {cpu} 核")
    if series > 20_000_000 or ingest > 1_000_000:
        print("建议: 规模超出单机舒适区，考虑集群版（vminsert/vmstorage/vmselect）")
    else:
        print("建议: 单机版足够，定期 vmbackup 即可（见 scripts/backup.sh）")
    print("--------------------------")
    print("注：生产前请用 1-2 周真实数据验证，可用 vmui 查询")
    print("    sum(vm_cache_entries{type=\"storage/hour_metric_ids\"}) 核对 series 数")

if __name__ == "__main__":
    main()
