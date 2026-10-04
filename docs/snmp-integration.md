# SNMP 网络设备接入

本栈的 vmagent 原生兼容 Prometheus 抓取配置，因此可以直接接入
`snmp_exporter`，把交换机、路由器、防火墙的指标也收进 VictoriaMetrics，
和主机、K8s 指标统一查询、统一告警。

## 联动 snmp-mib-ui

如果你用 [snmp-mib-ui](https://github.com/Oumu33/snmp-mib-ui)：

1. 在 snmp-mib-ui 里可视化浏览 MIB，勾选需要的 OID；
2. 选择引擎为 **SNMP Exporter**，一键生成 `snmp.yml`；
3. 把生成的 `snmp.yml` 放到 snmp_exporter 的配置目录，启动 snmp_exporter；
4. 在本栈 `config/vmagent/scrape.yml` 里取消 `snmp` job 的注释，
   把 target 改成你的设备 IP 即可。

```yaml
# config/vmagent/scrape.yml
- job_name: "snmp"
  static_configs:
    - targets: ["192.168.1.1", "192.168.1.2"]  # 你的设备 IP
  metrics_path: /snmp
  params:
    module: [cisco]   # 与 snmp.yml 中的 module 名对应
  relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - source_labels: [__param_target]
      target_label: instance
    - target_label: __address__
      replacement: "snmp-exporter:9116"
```

改完执行 `docker compose restart vmagent` 生效。

## 验证

在 vmui 里查：

```metricsql
# 设备是否在线
up{job="snmp"}

# 接口流量（示例，需按你的 module 调整指标名）
rate(ifHCInOctets[5m])
```

## 多厂商建议

- 按厂商拆 module（`cisco` / `huawei` / `h3c`），snmp-mib-ui 的品牌包管理正好对应；
- 不同厂商的接口指标名可能不同，Grafana 看板里用 `or` 兼容多种写法，
  或统一用 snmp-mib-ui 生成时的指标别名。
