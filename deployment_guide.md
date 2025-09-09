# 🚀 Machinecraft Inventory Slack Bot - Deployment Guide

## 📋 Prerequisites

### 1. Server Requirements
- **OS**: Ubuntu 20.04+ or CentOS 8+ (recommended)
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: 10GB+ free space
- **Python**: 3.8+ with pip
- **Database**: SQLite (included with Python)

### 2. Slack App Configuration
- Bot token: `your-slack-bot-token-here`
- Signing secret: Get from Slack App settings
- Event subscriptions enabled
- Bot permissions configured

## 🔧 Deployment Options

### Option 1: Quick Deploy (Local/Development)
```bash
# 1. Set environment variables
export SLACK_BOT_TOKEN="your-slack-bot-token-here"
export SLACK_SIGNING_SECRET="your-signing-secret-here"

# 2. Install dependencies
pip3 install -r requirements_slack.txt
pip3 install flask

# 3. Run the bot
python3 deploy_slack_bot.py
```

### Option 2: Production Deploy (Server)
```bash
# 1. Clone/setup on server
git clone <your-repo> /opt/machinecraft-bot
cd /opt/machinecraft-bot

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements_slack.txt
pip install flask gunicorn

# 4. Set environment variables
echo 'export SLACK_BOT_TOKEN="your-slack-bot-token-here"' >> ~/.bashrc
echo 'export SLACK_SIGNING_SECRET="your-signing-secret-here"' >> ~/.bashrc
source ~/.bashrc

# 5. Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 deploy_slack_bot:app
```

### Option 3: Docker Deploy
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements_slack.txt .
RUN pip install -r requirements_slack.txt
RUN pip install flask gunicorn

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "deploy_slack_bot:app"]
```

## 🌐 Slack Events API Setup

### 1. Configure Event Subscriptions
1. Go to your Slack App → "Event Subscriptions"
2. Enable Events
3. Set Request URL: `https://your-server.com/slack/events`
4. Subscribe to these events:
   - `message.channels`
   - `message.groups`
   - `message.im`

### 2. Verify URL
- Slack will send a verification request
- Your server must respond with the challenge token
- The bot handles this automatically

## 🔒 Security Configuration

### 1. Environment Variables
```bash
# Required
export SLACK_BOT_TOKEN="your-slack-bot-token-here"
export SLACK_SIGNING_SECRET="your-signing-secret-here"

# Optional
export FLASK_ENV="production"
export DATABASE_PATH="/opt/machinecraft-bot/machinecraft_inventory_pipeline.db"
```

### 2. Firewall Rules
```bash
# Allow HTTP/HTTPS traffic
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 5000  # For testing
```

### 3. SSL Certificate (Recommended)
```bash
# Using Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

## 📊 Monitoring & Logs

### 1. Health Check Endpoints
- `GET /health` - Basic health check
- `GET /test` - Detailed system status

### 2. Logging
```bash
# View logs
tail -f /var/log/machinecraft-bot.log

# Or with systemd
journalctl -u machinecraft-bot -f
```

### 3. Database Monitoring
```bash
# Check database size
ls -lh machinecraft_inventory_pipeline.db

# Check item count
sqlite3 machinecraft_inventory_pipeline.db "SELECT COUNT(*) FROM silver_inventory_items;"
```

## 🚀 Systemd Service (Recommended)

### 1. Create Service File
```bash
sudo nano /etc/systemd/system/machinecraft-bot.service
```

### 2. Service Configuration
```ini
[Unit]
Description=Machinecraft Inventory Slack Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/machinecraft-bot
Environment=SLACK_BOT_TOKEN=your-slack-bot-token-here
Environment=SLACK_SIGNING_SECRET=your-signing-secret-here
ExecStart=/opt/machinecraft-bot/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 deploy_slack_bot:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Enable Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable machinecraft-bot
sudo systemctl start machinecraft-bot
sudo systemctl status machinecraft-bot
```

## 🔄 Updates & Maintenance

### 1. Update Bot
```bash
cd /opt/machinecraft-bot
git pull
sudo systemctl restart machinecraft-bot
```

### 2. Database Backup
```bash
# Daily backup
cp machinecraft_inventory_pipeline.db backup_$(date +%Y%m%d).db
```

### 3. Log Rotation
```bash
# Add to /etc/logrotate.d/machinecraft-bot
/var/log/machinecraft-bot.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## 🧪 Testing

### 1. Local Testing
```bash
# Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/test
```

### 2. Slack Testing
1. Add bot to a test channel
2. Send test messages:
   - `inventory summary`
   - `inventory servo motors`
   - `inventory mitsubishi`

### 3. Load Testing
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test with 100 requests
ab -n 100 -c 10 http://localhost:5000/health
```

## 🆘 Troubleshooting

### Common Issues

#### Bot Not Responding
- Check if service is running: `sudo systemctl status machinecraft-bot`
- Check logs: `journalctl -u machinecraft-bot -f`
- Verify bot token is correct
- Check if bot is added to channel

#### Database Errors
- Verify database file exists and is readable
- Check file permissions
- Run database integrity check: `sqlite3 machinecraft_inventory_pipeline.db "PRAGMA integrity_check;"`

#### Slack API Errors
- Verify bot token is valid
- Check bot permissions in Slack App settings
- Ensure Event Subscriptions are properly configured

### Debug Commands
```bash
# Check service status
sudo systemctl status machinecraft-bot

# View recent logs
journalctl -u machinecraft-bot --since "1 hour ago"

# Test database connection
sqlite3 machinecraft_inventory_pipeline.db "SELECT COUNT(*) FROM silver_inventory_items;"

# Test Slack API
curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" https://slack.com/api/auth.test
```

## 📈 Performance Optimization

### 1. Database Optimization
```sql
-- Create indexes for faster searches
CREATE INDEX idx_brand ON silver_inventory_items(brand);
CREATE INDEX idx_category ON silver_inventory_items(category);
CREATE INDEX idx_price ON silver_inventory_items(unit_price_inr);
CREATE INDEX idx_stock ON silver_inventory_items(quantity);
```

### 2. Caching
- Consider Redis for frequently accessed data
- Cache search results for common queries
- Implement response caching

### 3. Scaling
- Use load balancer for multiple instances
- Implement database connection pooling
- Consider PostgreSQL for larger datasets

## 🎯 Success Metrics

### Key Performance Indicators
- **Response Time**: < 2 seconds for searches
- **Uptime**: 99.9% availability
- **Search Accuracy**: > 95% relevant results
- **User Adoption**: Track daily active users

### Monitoring Dashboard
- Real-time search queries
- Response times
- Error rates
- Database performance
- User engagement metrics

---

## 🚀 Quick Start Commands

```bash
# 1. Deploy to server
scp -r . user@your-server:/opt/machinecraft-bot/

# 2. SSH to server
ssh user@your-server

# 3. Setup and run
cd /opt/machinecraft-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_slack.txt flask gunicorn
export SLACK_BOT_TOKEN="your-slack-bot-token-here"
export SLACK_SIGNING_SECRET="your-signing-secret-here"
gunicorn -w 4 -b 0.0.0.0:5000 deploy_slack_bot:app
```

**Your Machinecraft Inventory Slack Bot is now ready for production! 🎉**
