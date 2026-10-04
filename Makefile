.PHONY: up down restart logs ps clean

up:           ## 启动全栈
	docker compose up -d

down:         ## 停止全栈（保留数据）
	docker compose down

restart:      ## 重启全栈（改完抓取配置/告警规则后用）
	docker compose restart

logs:         ## 查看所有日志
	docker compose logs -f

ps:           ## 查看容器状态
	docker compose ps

clean:        ## 停止并删除所有数据卷（慎用！会清空监控数据）
	docker compose down -v
