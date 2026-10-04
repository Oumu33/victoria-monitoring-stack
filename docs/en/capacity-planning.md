# Capacity Planning Cheat Sheet

> Estimates based on official docs and community experience — conservative.
> Validate with 1–2 weeks of your own production data before scaling up.
> Upstream also provides [vmestimator](https://docs.victoriametrics.com/victoriametrics/vmestimator/)
> for precise calculations.

## Rules of thumb

- **RAM**: active time series × ~1KB (index overhead)
- **Disk**: data points written per day × ~1 byte/point × retention days × 2 (compression variance)
- **CPU**: ~1 core per 100k points/sec ingested; queries extra

## Quick table (single-node)

| Active series | Ingest (pts/sec) | RAM | Disk (12 months) | CPU | Fits |
|---------------|------------------|-----|------------------|-----|------|
| 100k | 10k | 2 GB | 100 GB | 2 cores | dozens of hosts + small K8s |
| 1M | 100k | 4–8 GB | 500 GB | 4 cores | mid-size company, full coverage |
| 5M | 500k | 16 GB | 2 TB | 8 cores | large K8s / multi-DC |
| 10M+ | 1M+ | 32 GB+ | 5 TB+ | 16 cores+ | consider cluster version |

## What are my numbers?

Run in vmui (`:8428/vmui`):

```metricsql
# current active time series
sum(vm_cache_entries{type="storage/hour_metric_ids"})

# ingestion rate
sum(rate(vm_rows_inserted_total[5m]))

# storage used
vm_data_size_bytes
```

Plug the three numbers into the table above to see if your box is enough
and how long a retention you can afford.

## Three levers to save resources

1. **Stream aggregation**: vmagent's `-remoteWrite.streamAggr` aggregates
   high-frequency metrics before storing — can halve series count.
2. **Control label cardinality**: labels with timestamps or random IDs are the
   #1 killer — drop them with `relabel_configs` in the scrape config.
3. **Tiered retention**: full precision for 30 days of hot data; VM's
   compression makes 12 months of history cheaper than you'd expect.

## When to go cluster?

- Sustained ingest above 1M pts/sec, or series above 20M;
- Need multi-replica HA (single-node relies on vmbackup for recovery, no live replicas).
- Until then, single-node + scheduled vmbackup is the best value shape.
