# Reddit r/selfhosted post draft

> Subreddit rules: no spam, be a community member first. Post from the user's
> own account. Best time: weekday UTC morning.

---

**Title:** I replaced Prometheus with VictoriaMetrics for my homelab monitoring — 7x less disk, one docker-compose file

**Body:**

Long-time Prometheus user here. My setup kept hitting the same walls: 15-day
retention because the disk couldn't keep up, memory spikes on high-cardinality
metrics, and Thanos/Cortex felt like a second full-time job for a homelab.

I switched to VictoriaMetrics single-node and packaged everything I learned
into a one-command stack:

- **vmagent** for scraping (Prometheus scrape configs work as-is)
- **VictoriaMetrics** single-node for storage (12-month retention on the same disk that held 15 days of Prometheus)
- **vmalert + Alertmanager** for alerting (Prometheus rule syntax compatible)
- **Grafana** pre-provisioned with the VM datasource and an overview dashboard

`docker compose up -d` and you have data in 5 minutes — a demo node-exporter
is included so the whole pipeline is verifiable immediately.

What I think is actually useful beyond "another compose file":

1. **A zero-downtime migration guide** (docs/en/migration-prometheus-to-vm.md) —
   vmagent dual-write → vmctl history import → Grafana datasource cutover,
   with a rollback plan for each phase.
2. **A capacity planning cheat sheet** — how much RAM/disk per million active
   series, and the three levers that actually save resources (stream
   aggregation, label cardinality control, tiered retention).
3. **SNMP integration** — vmagent scrapes snmp_exporter directly, so switches
   and routers land in the same TSDB. I pair it with my MIB visualizer
   (snmp-mib-ui) to pick OIDs without hand-writing configs.

Repo: https://github.com/Oumu33/victoria-monitoring-stack (replace with real URL after creation)

Happy to answer questions — especially from anyone who's done the
Prometheus → VM migration and has war stories about cardinality explosions.
