# Hacker News "Show HN" draft

> Show HN guidelines: keep it factual, no marketing fluff, be present in the
> comments. Post from the user's own account on a weekday morning US time.

---

**Title:** Show HN: VictoriaMetrics monitoring stack — docker-compose, zero-downtime Prometheus migration guide

**Body (first comment):**

Hi HN. I maintain a few monitoring tools and kept answering the same questions
about moving from Prometheus to VictoriaMetrics, so I packaged the whole thing:
a single-node, production-leaning stack you start with one command.

What's in the box:
- vmagent → VictoriaMetrics (single-node) → vmalert → Alertmanager → Grafana,
  all pinned versions, all pre-wired
- Prometheus scrape configs and alert rules work as-is (vmagent/vmalert are
  compatible), so migration is config-level, not rewrite-level
- A 3-phase zero-downtime migration guide: dual-write, vmctl history import,
  Grafana cutover — each phase independently rollbackable
- Capacity planning cheat sheet (RAM/disk per million series) and the
  resource-saving levers that matter in practice
- SNMP device monitoring via snmp_exporter, paired with a visual MIB/OID
  picker I built separately (snmp-mib-ui)

Why single-node instead of cluster: upstream recommends it below ~1M
points/sec, and it's an order of magnitude simpler to operate. Most teams
that jump straight to cluster are over-engineering.

Repo: https://github.com/Oumu33/victoria-monitoring-stack (replace with real URL after creation)
Docs are bilingual (EN primary, 中文).

Genuinely curious: for those who migrated off Prometheus — what broke, and
what would you do differently?
