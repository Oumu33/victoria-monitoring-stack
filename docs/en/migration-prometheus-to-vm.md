# Prometheus → VictoriaMetrics Zero-Downtime Migration

Goal: migrate collection and storage from Prometheus to this stack with
**zero business impact and a rollback plan**.

## The 3-phase approach

```
Phase 1: dual-write     Phase 2: switch queries     Phase 3: decommission
┌──────────┐           ┌──────────────┐            ┌──────────────┐
│ vmagent  │           │ Grafana       │            │ Stop         │
│ writes to│──────────▶│ datasource    │───────────▶│ Prometheus   │
│ Prometheus│           │ cut over,     │            │ VM only      │
│ + VM     │           │ verify        │            │              │
└──────────┘           └──────────────┘            └──────────────┘
  rollback anytime      switch back if needed       history migrated
```

## Phase 1: vmagent dual-write

vmagent natively supports remoteWriting the same scraped data to multiple backends.
Run vmagent next to your existing Prometheus (or just use this stack's),
passing two `--remoteWrite.url` flags:

```bash
docker run -d --name vmagent-migrate \
  -v /path/to/scrape.yml:/etc/vmagent/scrape.yml:ro \
  victoriametrics/vmagent:v1.153.0 \
  --promscrape.config=/etc/vmagent/scrape.yml \
  --remoteWrite.url=http://prometheus:9090/api/v1/write \
  --remoteWrite.url=http://vm-single:8428/api/v1/write
```

> Note: Prometheus must run with `--enable-feature=remote-write-receiver` to accept remoteWrite.
> Recommended: let vmagent replace Prometheus for scraping entirely (scrape config
> syntax is compatible) and keep Prometheus only as one of the dual-write targets.

Verify dual-write is healthy:

```bash
# same metric on both sides, timestamps aligned = healthy
curl 'http://prometheus:9090/api/v1/query?query=up'
curl 'http://vm-single:8428/api/v1/query?query=up'
```

## Phase 2: migrate history (optional)

To keep historical data, use the official `vmctl`:

```bash
# snapshot Prometheus first
curl -XPOST http://prometheus:9090/api/v1/admin/tsdb/snapshot

# import into VM in monthly batches to avoid saturation
./vmctl prometheus \
  --prom-snapshot=/prometheus/snapshots/<snapshot-name> \
  --vm-addr=http://vm-single:8428 \
  --vm-concurrency=8 \
  --vm-batch-size=500000
```

> For large datasets, migrate in time slices during off-peak hours.
> Keep dual-write on during migration; VM deduplicates overlapping ranges.

## Phase 3: switch Grafana datasources

1. Add a VictoriaMetrics datasource in Grafana (URL `http://vm-single:8428`,
   type Prometheus — already pre-provisioned in this stack);
2. Switch dashboards over one by one, observe for 1–2 days;
3. Flip the default datasource to VM;
4. Alert rules: vmalert is compatible with Prometheus rule syntax — copy them over as-is.

## Rollback plan

| Scenario | Rollback |
|----------|----------|
| Data mismatch during dual-write | Drop the VM remoteWrite URL on vmagent; Prometheus untouched |
| Dashboard issues after query cutover | Switch Grafana datasource back to Prometheus in one click (keep the datasource) |
| VM failure | Prometheus leg of dual-write is still there; switch queries back |

**Principle: at every phase, Prometheus keeps working standalone until you have
run stably on VM for a full retention period.**

## Reference cases

- Adsterra: 1B samples, 2T historical data points, zero-downtime migration,
  67% lower storage cost, 83% lower query latency.
- General lesson: the cost of migration is in the **rollout cadence**, not the tooling —
  edge services first, core services last.
