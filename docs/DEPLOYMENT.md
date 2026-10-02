# Railway Block Planner — Production Deployment Guide

This document outlines deployment procedures for production deployment within an Indian Railways Divisional Railway Manager (DRM) or Zonal Control Office infrastructure.

---

## 1. System Requirements

- **Operating System**: Enterprise Linux (RHEL 9 / Rocky Linux 9 / Ubuntu 24.04 LTS) or Windows Server 2022.
- **Python**: Version 3.11, 3.12, 3.13, or 3.14.
- **SQLite**: Version 3.35+ with Write-Ahead Logging (WAL) support.
- **Memory**: Minimum 4 GB RAM (8 GB recommended for dense corridors with >500 daily trains).
- **Storage**: Fast NVMe SSD recommended for SQLite WAL microsecond write performance.

---

## 2. Linux Systemd Service Setup

Create `/etc/systemd/system/railway-block-planner.service`:

```ini
[Unit]
Description=Indian Railways Block Planner Service
After=network.target

[Service]
Type=simple
User=railway
Group=railway
WorkingDirectory=/opt/railway-block-planner
EnvironmentFile=/opt/railway-block-planner/.env
ExecStart=/opt/railway-block-planner/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info
Restart=always
RestartSec=5s

# Security sandboxing
ProtectSystem=full
ProtectHome=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable railway-block-planner
sudo systemctl start railway-block-planner
sudo systemctl status railway-block-planner
```

---

## 3. Reverse Proxy & TLS Termination (Nginx)

Create `/etc/nginx/sites-available/railway-planner.conf`:

```nginx
server {
    listen 80;
    server_name railway-planner.division.internal;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name railway-planner.division.internal;

    ssl_certificate /etc/ssl/certs/railway_division.crt;
    ssl_certificate_key /etc/ssl/private/railway_division.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 90s;
    }
}
```

---

## 4. SQLite WAL Mode Maintenance & Hot Backups

SQLite WAL mode allows zero-downtime hot backups using the atomic `VACUUM INTO` command.

Create a nightly backup cron script `/usr/local/bin/backup-railway-state.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/railway_state"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

# Execute atomic SQLite hot copy
sqlite3 /opt/railway-block-planner/data/railway_state.db "VACUUM INTO '${BACKUP_DIR}/railway_state_${TIMESTAMP}.db';"

# Retain last 30 days of state snapshots
find "$BACKUP_DIR" -type f -name "railway_state_*.db" -mtime +30 -delete

echo "[$(date)] Backup completed: railway_state_${TIMESTAMP}.db"
```

Add to cron (`crontab -e`):
```cron
0 2 * * * /usr/local/bin/backup-railway-state.sh >> /var/log/railway_backup.log 2>&1
```

---

## 5. Health Check Monitoring

Monitor service liveness using the standardized health endpoint:
```bash
curl -f http://127.0.0.1:8000/api/v1/providers/health || exit 1
```

In automated monitoring tools (Prometheus / Zabbix / Nagios):
- HTTP status `200` $\implies$ Service operational.
- Status JSON `providers.rtis.circuit_breaker_open: true` $\implies$ External CRIS connection degraded.
