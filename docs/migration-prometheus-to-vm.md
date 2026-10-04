# Prometheus → VictoriaMetrics 双写迁移实战

目标：**业务零感知、可回滚**，把 Prometheus 的采集与存储平滑切到本栈。

## 总体思路（三步法）

```
阶段一：双写          阶段二：切换查询        阶段三：下线
┌──────────┐        ┌──────────────┐        ┌──────────────┐
│ vmagent  │        │ Grafana 数据源 │        │ 停 Prometheus │
│ 同时写    │───────▶│ 切到 VM      │───────▶│ 只留 VM       │
│ Prometheus│        │ 灰度验证     │        │               │
│ + VM      │        │              │        │               │
└──────────┘        └──────────────┘        └──────────────┘
   可随时回滚          发现问题切回           历史数据已迁完
```

## 阶段一：vmagent 双写

vmagent 原生支持把一份采集数据同时 remoteWrite 到多个后端。
在现有 Prometheus 旁边起一个 vmagent（或直接用本栈的），
`--remoteWrite.url` 传两个地址：

```bash
docker run -d --name vmagent-migrate \
  -v /path/to/scrape.yml:/etc/vmagent/scrape.yml:ro \
  victoriametrics/vmagent:v1.153.0 \
  --promscrape.config=/etc/vmagent/scrape.yml \
  --remoteWrite.url=http://prometheus:9090/api/v1/write \
  --remoteWrite.url=http://vm-single:8428/api/v1/write
```

> 注意：Prometheus 需开启 `--enable-feature=remote-write-receiver` 才能接收 remoteWrite。
> 更推荐的做法：让 vmagent 直接替代 Prometheus 做采集（抓取配置语法兼容），
> Prometheus 只作为双写目标之一保留。

验证双写正常：

```bash
# 两边查同一个指标，时间戳对齐即正常
curl 'http://prometheus:9090/api/v1/query?query=up'
curl 'http://vm-single:8428/api/v1/query?query=up'
```

## 阶段二：迁移历史数据（可选）

如果历史数据也要保留，用官方 `vmctl` 迁移：

```bash
# 先给 Prometheus 做快照
curl -XPOST http://prometheus:9090/api/v1/admin/tsdb/snapshot

# 用 vmctl 把快照导入 VM（按月份分批，避免一次打满）
./vmctl prometheus \
  --prom-snapshot=/prometheus/snapshots/<快照名> \
  --vm-addr=http://vm-single:8428 \
  --vm-concurrency=8 \
  --vm-batch-size=500000
```

> 数据量大时按时间分片、错峰迁移；迁移期间保持双写开启，
> 用 VM 的去重能力处理重叠时间段的数据。

## 阶段三：切换 Grafana 数据源

1. Grafana 里新增 VictoriaMetrics 数据源（URL 填 `http://vm-single:8428`，
   类型选 Prometheus，本栈已预置好）；
2. 逐个看板把数据源从 Prometheus 切换到 VictoriaMetrics，观察 1-2 天；
3. 确认无误后，把默认数据源切到 VM；
4. 告警规则：vmalert 兼容 Prometheus rule 语法，整份搬过去即可。

## 回滚预案

| 场景 | 回滚动作 |
|------|---------|
| 双写阶段发现数据不一致 | 停 vmagent 的 VM 那路 remoteWrite，Prometheus 不受影响 |
| 切换查询后看板异常 | Grafana 数据源一键切回 Prometheus（数据源保留不删） |
| VM 故障 | vmagent 双写保留 Prometheus 那路，查询切回即可 |

**原则：任何阶段，Prometheus 都保持可独立工作，直到你在 VM 上稳定跑满一个保留周期。**

## 参考案例

- Adsterra：10 亿样本、2 万亿历史数据点，零停机迁移，存储成本降 67%，查询延迟降 83%。
- 通用结论：迁移最大的成本不在工具，在**灰度节奏**——先边缘业务，再核心业务。
