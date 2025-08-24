# 🚀 Production Deployment Guide

## AQI Forecasting System - Production Deployment

This guide covers the complete production deployment of the AQI Forecasting System, including security, monitoring, and scalability considerations.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Security Configuration](#security-configuration)
4. [Deployment Options](#deployment-options)
5. [Monitoring & Observability](#monitoring--observability)
6. [Backup & Recovery](#backup--recovery)
7. [Scaling & Performance](#scaling--performance)
8. [Maintenance & Updates](#maintenance--updates)

---

## 🔧 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Python**: 3.9+ with virtual environment
- **Memory**: Minimum 8GB RAM (16GB+ recommended)
- **Storage**: Minimum 50GB free space
- **CPU**: 4+ cores recommended
- **Network**: Stable internet connection for data collection

### Software Dependencies
- **Web Server**: Nginx (recommended) or Apache
- **Process Manager**: Systemd or Supervisor
- **Cache**: Redis (optional, for performance)
- **Database**: SQLite (built-in) or PostgreSQL (optional)
- **Monitoring**: Prometheus + Grafana (optional)

---

## 🌍 Environment Setup

### 1. Production Environment File

Create `.env.production` in your project root:

```bash
# Production Environment Configuration
PROD_HOST=0.0.0.0
PROD_PORT=8000
PROD_WORKERS=4

# Security
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
API_KEYS_ENABLED=true
SECRET_KEY=your-super-secret-key-here

# Logging
LOG_LEVEL=INFO
SYSLOG_ENABLED=true
SYSLOG_HOST=localhost
SYSLOG_PORT=514

# Monitoring
ALERTING_ENABLED=true
ALERT_WEBHOOK_URL=https://your-webhook-url.com/alerts

# Data Management
BACKUP_ENABLED=true
BACKUP_INTERVAL_HOURS=24
BACKUP_RETENTION_DAYS=30
MAX_CONCURRENT_JOBS=5
JOB_TIMEOUT=7200

# OpenWeather API
OPENWEATHER_API_KEY=your-api-key-here

# Redis (Optional)
REDIS_URL=redis://localhost:6379
```

### 2. Install Production Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install production requirements
pip install -r app/requirements-production.txt
```

---

## 🔒 Security Configuration

### 1. API Key Authentication

Enable API key authentication for production:

```python
# In your FastAPI app
from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != "your-production-api-key":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

### 2. CORS Configuration

Restrict CORS to production domains:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 3. Rate Limiting

Implement rate limiting to prevent abuse:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/data/current")
@limiter.limit("100/minute")
async def get_current_data(request: Request):
    # Your endpoint logic
    pass
```

---

## 🚀 Deployment Options

### Option 1: Traditional Server Deployment

#### 1.1 Systemd Service

Create `/etc/systemd/system/aqi-forecasting.service`:

```ini
[Unit]
Description=AQI Forecasting System Backend
After=network.target

[Service]
Type=exec
User=aqi-user
WorkingDirectory=/opt/aqi-forecasting
Environment=PATH=/opt/aqi-forecasting/venv/bin
ExecStart=/opt/aqi-forecasting/venv/bin/python -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 1.2 Nginx Configuration

Create `/etc/nginx/sites-available/aqi-forecasting`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Frontend
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

#### 1.3 Start Services

```bash
# Enable and start systemd service
sudo systemctl enable aqi-forecasting
sudo systemctl start aqi-forecasting

# Enable nginx site
sudo ln -s /etc/nginx/sites-available/aqi-forecasting /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option 2: Docker Deployment

#### 2.1 Build and Run

```bash
# Build Docker image
docker build -f app/deploy/Dockerfile -t aqi-forecasting:latest .

# Run with Docker Compose
cd app/deploy
docker-compose up -d
```

#### 2.2 Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart specific service
docker-compose restart aqi-backend
```

---

## 📊 Monitoring & Observability

### 1. System Metrics

The system automatically collects:
- CPU usage
- Memory usage
- Disk usage
- Network I/O
- Process count
- System uptime

### 2. Application Metrics

Track application performance:
- Request count and response times
- Error rates
- Cache hit rates
- Job queue status
- Active connections

### 3. Prometheus + Grafana Setup

#### 3.1 Prometheus Configuration

Create `app/deploy/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'aqi-forecasting'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

#### 3.2 Grafana Dashboard

Import the provided Grafana dashboard configuration for:
- System resource monitoring
- Application performance metrics
- Custom AQI forecasting alerts

### 4. Log Management

#### 4.1 Log Rotation

Configure logrotate in `/etc/logrotate.d/aqi-forecasting`:

```
/var/log/aqi-forecasting/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 aqi-user aqi-user
    postrotate
        systemctl reload aqi-forecasting
    endscript
}
```

#### 4.2 Centralized Logging

For production environments, consider:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Fluentd
- Graylog

---

## 💾 Backup & Recovery

### 1. Automated Backups

#### 1.1 Data Backup Script

Create `app/deploy/backup.py`:

```python
#!/usr/bin/env python3
"""
Automated backup script for AQI Forecasting System
"""
import os
import shutil
import tarfile
from datetime import datetime
from pathlib import Path

def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("/var/backups/aqi-forecasting")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Create backup archive
    backup_file = backup_dir / f"aqi-backup_{timestamp}.tar.gz"
    
    with tarfile.open(backup_file, "w:gz") as tar:
        # Backup data repositories
        tar.add("data_repositories", arcname="data_repositories")
        
        # Backup saved models
        tar.add("saved_models", arcname="saved_models")
        
        # Backup configuration
        tar.add(".env.production", arcname=".env.production")
    
    print(f"Backup created: {backup_file}")
    return backup_file

if __name__ == "__main__":
    create_backup()
```

#### 1.2 Cron Job Setup

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /opt/aqi-forecasting/venv/bin/python /opt/aqi-forecasting/app/deploy/backup.py

# Cleanup old backups (keep last 30 days)
0 3 * * * find /var/backups/aqi-forecasting -name "*.tar.gz" -mtime +30 -delete
```

### 2. Recovery Procedures

#### 2.1 Data Recovery

```bash
# Stop services
sudo systemctl stop aqi-forecasting

# Restore from backup
cd /opt/aqi-forecasting
tar -xzf /var/backups/aqi-forecasting/aqi-backup_YYYYMMDD_HHMMSS.tar.gz

# Restart services
sudo systemctl start aqi-forecasting
```

#### 2.2 Configuration Recovery

```bash
# Restore environment configuration
cp .env.production.backup .env.production

# Restart services to apply changes
sudo systemctl restart aqi-forecasting
```

---

## 📈 Scaling & Performance

### 1. Horizontal Scaling

#### 1.1 Load Balancer Configuration

Use Nginx as a load balancer:

```nginx
upstream aqi_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    location /api/ {
        proxy_pass http://aqi_backend;
        # ... other proxy settings
    }
}
```

#### 1.2 Multiple Worker Processes

Increase worker processes in systemd service:

```ini
ExecStart=/opt/aqi-forecasting/venv/bin/python -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --workers 8
```

### 2. Performance Optimization

#### 2.1 Redis Caching

Enable Redis caching for frequently accessed data:

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_data(key: str):
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None

def set_cached_data(key: str, data: dict, ttl: int = 300):
    redis_client.setex(key, ttl, json.dumps(data))
```

#### 2.2 Database Optimization

For SQLite databases:
- Regular VACUUM operations
- Proper indexing
- Connection pooling

#### 2.3 Static File Serving

Serve static files through Nginx:

```nginx
location /static/ {
    alias /opt/aqi-forecasting/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## 🔧 Maintenance & Updates

### 1. Regular Maintenance Tasks

#### 1.1 Daily Tasks
- Check system health
- Monitor error logs
- Verify backup completion

#### 1.2 Weekly Tasks
- Review performance metrics
- Clean up old log files
- Update system packages

#### 1.3 Monthly Tasks
- Review security settings
- Performance optimization
- Capacity planning

### 2. Update Procedures

#### 2.1 Code Updates

```bash
# Stop services
sudo systemctl stop aqi-forecasting

# Backup current version
cp -r /opt/aqi-forecasting /opt/aqi-forecasting.backup.$(date +%Y%m%d)

# Update code
cd /opt/aqi-forecasting
git pull origin main

# Install new dependencies
source venv/bin/activate
pip install -r app/requirements-production.txt

# Run migrations (if any)
python app/deploy/migrate.py

# Restart services
sudo systemctl start aqi-forecasting

# Verify deployment
curl -f http://localhost:8000/health
```

#### 2.2 Rollback Procedures

```bash
# Stop services
sudo systemctl stop aqi-forecasting

# Rollback to previous version
rm -rf /opt/aqi-forecasting
cp -r /opt/aqi-forecasting.backup.YYYYMMDD /opt/aqi-forecasting

# Restart services
sudo systemctl start aqi-forecasting
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check service status
sudo systemctl status aqi-forecasting

# View logs
sudo journalctl -u aqi-forecasting -f

# Check configuration
sudo nginx -t
```

#### 2. High Resource Usage
```bash
# Check system resources
htop
df -h
free -h

# Check specific process
ps aux | grep aqi-forecasting
```

#### 3. Network Issues
```bash
# Check port availability
netstat -tlnp | grep :8000
netstat -tlnp | grep :8501

# Test connectivity
curl -v http://localhost:8000/health
```

---

## 📞 Support & Maintenance

### Contact Information
- **Technical Support**: [your-email@domain.com]
- **Emergency Contact**: [emergency-phone]
- **Documentation**: [your-docs-url]

### Maintenance Windows
- **Regular Maintenance**: Sundays 2:00 AM - 4:00 AM UTC
- **Emergency Maintenance**: As needed with 2-hour notice

---

## 🎯 Next Steps

After successful deployment:

1. **Monitor Performance**: Use the provided monitoring tools
2. **Set Up Alerts**: Configure alerting for critical issues
3. **Performance Tuning**: Optimize based on usage patterns
4. **Security Auditing**: Regular security reviews
5. **Capacity Planning**: Monitor growth and plan scaling

---

**🎉 Congratulations! Your AQI Forecasting System is now production-ready!**

For additional support or questions, refer to the troubleshooting section or contact the support team.
