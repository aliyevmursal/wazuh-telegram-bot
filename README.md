# 🚀 Enhanced Wazuh Telegram Integration

**Advanced security alert notification system for Wazuh SIEM**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Wazuh](https://img.shields.io/badge/Wazuh-4.0+-green.svg)](https://wazuh.com/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API-blue.svg)](https://core.telegram.org/bots/api)

> 🛡️ **Professional-grade Wazuh security alerts delivered straight to your Telegram**  
> Author: **[Mursal Aliyev](https://github.com/aliyevmursal)** with ❤️

---

## ✨ Features

### 🎨 **Rich Visual Experience**
- **Emoji-coded severity levels** with color indicators (🔴🟠🟡🟢)
- **HTML formatting** for professional message layout
- **Structured information display** with clear sections
- **Customizable message templates** for branding

### ⚙️ **Advanced Configuration**
- **JSON-based configuration** for easy management
- **Multi-level filtering system** (rules, agents, severity)
- **Rate limiting protection** against spam
- **Comprehensive error handling** with retry logic

### 📊 **Comprehensive Alert Data**
- **Timestamp formatting** in human-readable format
- **Network information** (source/destination IPs)
- **User and program details** for context
- **Log excerpts** for quick analysis
- **Rule group categorization** for better organization

---

## 🔧 Quick Start

### Installation
```bash
# One-command installation
curl -sSL https://raw.githubusercontent.com/aliyevmursal/wazuh-telegram-bot/main/install.sh | sudo bash
```

### Configuration
```bash
# 1. Configure your Telegram chat ID
sudo nano /var/ossec/integrations/telegram_config.json

# 2. Add integration to Wazuh config
sudo nano /var/ossec/etc/ossec.conf
```

### Wazuh Integration Block
```xml
<integration>
    <name>custom-telegram</name>
    <level>8</level>
    <hook_url>https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage</hook_url>
    <alert_format>json</alert_format>
</integration>
```

### Restart Services
```bash
sudo systemctl restart wazuh-manager
sudo systemctl status wazuh-manager
```

---

## 📊 Sample Alert Message

```
🚨 Wazuh Security Alert 🔴

🎯 Severity: CRITICAL (Level 12)
📋 Rule: Multiple authentication failures detected
🔢 Rule ID: 31151
📅 Time: 2025-07-21 14:30:45 UTC

🖥️ Agent: web-server-01 (192.168.1.100)
📍 Location: /var/log/auth.log
🌐 Source IP: 192.168.1.200
👤 User: admin
⚙️ Program: sshd
🏷️ Groups: authentication_failed, authentication_failures

📝 Log:
Failed password for admin from 192.168.1.200 port 22 ssh2

🔧 Enhanced Wazuh Telegram Integration v2.2.0
```

---

## 📋 Requirements

### System Requirements
- **Wazuh Server 4.0+** (fully configured and operational)
- **Python 3.6+** with pip
- **Internet connectivity** for Telegram API access
- **Linux/Unix environment** (tested on Ubuntu, CentOS, RHEL)

### Telegram Prerequisites
- **Telegram Bot** created via [@BotFather](https://t.me/botfather)
- **Bot API Token** (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
- **Chat ID** of target chat/group

---

## ⚙️ Configuration

### Basic Configuration
Edit `/var/ossec/integrations/telegram_config.json`:

```json
{
  "chat_id": "-1001234567890",
  "hook_url": "",
  "message_thread_id": null,
  "parse_mode": "HTML",
  "disable_notification": false,
  "rate_limit_seconds": 1,
  "max_message_length": 4096,
  "severity_levels": {
    "low": [0, 1, 2],
    "medium": [3, 4, 5, 6, 7],
    "high": [8, 9, 10, 11],
    "critical": [12, 13, 14, 15]
  },
  "custom_filters": {
    "exclude_rules": [5402],
    "include_only_rules": [],
    "exclude_agents": ["test-vm"],
    "include_only_agents": []
  },
  "message_templates": {
    "custom_header": "<b>🏢 ACME SOC</b>",
    "custom_footer": ""
  }
}
```

| Option | Description |
|---|---|
| `chat_id` | Target chat/group/channel ID (or `@channelname`). Can also be set with `TELEGRAM_CHAT_ID` env var or `<api_key>` in `ossec.conf` |
| `hook_url` | Used only if `<hook_url>` is not set in `ossec.conf` (or `TELEGRAM_HOOK_URL` env var) |
| `message_thread_id` | Topic ID for forum supergroups (optional) |
| `custom_filters` | Exclude / allow-list by rule ID and agent name |
| `message_templates` | Optional HTML header / footer (empty footer = default) |

All alert values are HTML-escaped, so logs containing `<`, `>` or `&` are delivered correctly. If Telegram still rejects the formatting, the alert is re-sent as plain text. The bot token is never written to the log file.

### Multiple Alert Levels
Add multiple integration blocks to `/var/ossec/etc/ossec.conf`:

```xml
<!-- Critical Alerts -->
<integration>
    <name>custom-telegram</name>
    <level>12</level>
    <hook_url>https://api.telegram.org/botYOUR_TOKEN/sendMessage</hook_url>
    <alert_format>json</alert_format>
</integration>

<!-- Authentication Failures -->
<integration>
    <name>custom-telegram</name>
    <group>authentication_failed</group>
    <hook_url>https://api.telegram.org/botYOUR_TOKEN/sendMessage</hook_url>
    <alert_format>json</alert_format>
</integration>

<!-- System Integrity -->
<integration>
    <name>custom-telegram</name>
    <group>rootcheck,syscheck</group>
    <hook_url>https://api.telegram.org/botYOUR_TOKEN/sendMessage</hook_url>
    <alert_format>json</alert_format>
</integration>
```

---

## 🧪 Testing

### Test Integration
```bash
# Test with your bot token
sudo python3 /var/ossec/integrations/test_integration.py YOUR_BOT_TOKEN
```

### Expected Output
```
Enhanced Wazuh Telegram Integration - Test Script
==================================================
🤖 Testing with bot token: 1234567890...
✅ All required files found
✅ Configuration found with chat_id: -1001234567890
✅ Integration call successful!
📱 Check your Telegram chat for the test message
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Wazuh Manager Won't Start
```bash
# Check configuration syntax
sudo /var/ossec/bin/wazuh-logtest

# Common fix: ensure <name> not <n> in ossec.conf
sudo nano /var/ossec/etc/ossec.conf
```

#### 2. Messages Not Sending
```bash
# Check integration logs
sudo tail -f /var/ossec/logs/telegram_integration.log

# Test bot connectivity
curl -X GET "https://api.telegram.org/botYOUR_TOKEN/getMe"
```

#### 3. Permission Errors
```bash
# Fix file permissions
sudo chown root:wazuh /var/ossec/integrations/custom-telegram*
sudo chmod 750 /var/ossec/integrations/custom-telegram*
sudo chmod 640 /var/ossec/integrations/telegram_config.json
```

#### 4. Chat ID Issues
```bash
# Get chat ID from bot updates
curl -X GET "https://api.telegram.org/botYOUR_TOKEN/getUpdates"
```

### Log Analysis
```bash
# View recent activity
sudo tail -100 /var/ossec/logs/telegram_integration.log

# Count successful messages
grep "Message sent successfully" /var/ossec/logs/telegram_integration.log | wc -l

# Check for errors
grep "ERROR" /var/ossec/logs/telegram_integration.log
```

---

## 🔐 Security Best Practices

### Bot Token Security
- **Never commit** bot tokens to version control
- **Use environment variables** for sensitive data
- **Regularly rotate** bot tokens
- **Monitor bot usage** through Telegram's Bot API

### System Security
- **Restrict file permissions** properly
- **Monitor log files** for unauthorized access
- **Use firewalls** to control network access
- **Keep systems updated** with security patches

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Development Setup
```bash
# Fork the repository
git clone https://github.com/yourusername/wazuh-telegram-bot.git
cd wazuh-telegram-bot

# Create a feature branch
git checkout -b feature/amazing-feature

# Make changes and test
sudo python3 /var/ossec/integrations/test_integration.py YOUR_TOKEN

# Commit with clear messages
git commit -m "Add amazing feature"

# Push and create pull request
git push origin feature/amazing-feature
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support & Contact

### 🐛 Bug Reports
- **GitHub Issues**: [Report bugs here](https://github.com/aliyevmursal/wazuh-telegram-bot/issues)
- **Security Issues**: Please email directly for security vulnerabilities

### 💡 Feature Requests
- **GitHub Discussions**: [Suggest features here](https://github.com/aliyevmursal/wazuh-telegram-bot/discussions)
- **Pull Requests**: Contributions are always welcome!

---

<div align="center">

**⭐ If you find this project useful, please give it a star! ⭐**

---

[![GitHub stars](https://img.shields.io/github/stars/aliyevmursal/wazuh-telegram-bot.svg?style=social&label=Star)](https://github.com/aliyevmursal/wazuh-telegram-bot)
[![GitHub forks](https://img.shields.io/github/forks/aliyevmursal/wazuh-telegram-bot.svg?style=social&label=Fork)](https://github.com/aliyevmursal/wazuh-telegram-bot/fork)

</div>
