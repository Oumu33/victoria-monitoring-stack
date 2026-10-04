#!/bin/bash
# VictoriaMetrics 单机版备份 / 恢复（vmbackup / vmrestore）
# 用法:
#   ./scripts/backup.sh backup [备份名]     # 备份到 ./backup/<备份名>
#   ./scripts/backup.sh restore <备份名>    # 从 ./backup/<备份名> 恢复（会停 vm-single）
set -euo pipefail

ACTION="${1:-backup}"
NAME="${2:-$(date +%Y%m%d)}"
BACKUP_DIR="$(pwd)/backup/$NAME"
VM_IMAGE="victoriametrics/vmbackup:v1.153.0"
VR_IMAGE="victoriametrics/vmrestore:v1.153.0"

backup() {
  mkdir -p "$BACKUP_DIR"
  echo "==> 创建快照…"
  curl -s "http://localhost:8428/snapshot/create" | head -c 200; echo
  echo "==> 备份到 $BACKUP_DIR"
  docker run --rm \
    --network vm-monitoring-stack_monitoring \
    -v vm-monitoring-stack_vm-data:/victoria-metrics-data:ro \
    -v "$BACKUP_DIR:/backup" \
    "$VM_IMAGE" \
    -storageDataPath=/victoria-metrics-data \
    -snapshot.createURL=http://victoria-metrics:8428/snapshot/create \
    -dst=fs:///backup
  echo "==> 备份完成"
}

restore() {
  [ -d "$BACKUP_DIR" ] || { echo "备份目录不存在: $BACKUP_DIR"; exit 1; }
  echo "==> 停止 victoria-metrics…"
  docker compose stop victoria-metrics
  echo "==> 从 $BACKUP_DIR 恢复（将清空现有数据）…"
  read -r -p "确认继续? [y/N] " ans
  [ "$ans" = "y" ] || exit 0
  docker run --rm \
    -v vm-monitoring-stack_vm-data:/victoria-metrics-data \
    -v "$BACKUP_DIR:/backup:ro" \
    "$VR_IMAGE" \
    -storageDataPath=/victoria-metrics-data \
    -src=fs:///backup
  docker compose start victoria-metrics
  echo "==> 恢复完成"
}

case "$ACTION" in
  backup) backup ;;
  restore) restore ;;
  *) echo "用法: $0 [backup|restore] [备份名]"; exit 1 ;;
esac
