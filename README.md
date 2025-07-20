🚀 Enhanced Wazuh Telegram Integration

**Advanced security alert notification system for Wazuh SIEM**



> 🛡️ **Professional-grade Wazuh security alerts delivered straight to your Telegram**  

## ✨ Features

- 🎨 **Rich Visual Messages** with emoji severity indicators
- ⚙️ **JSON Configuration** for easy management  
- 🛡️ **Rate Limiting** and error handling
- 📊 **Detailed Alert Data** with network info
- 🚀 **One-Command Installation**

## 🔧 Quick Start

```bash
# Download and install
curl -sSL https://raw.githubusercontent.com/mursalaliyev/enhanced-wazuh-telegram/main/install.sh | sudo bash

# Configure your chat ID in:
sudo nano /var/ossec/integrations/telegram_config.json

# Add to Wazuh config:
<integration>
    <n>custom-telegram</n>
    <level>8</level>
    <hook_url>https://api.telegram.org/botYOUR_TOKEN/sendMessage</hook_url>
    <alert_format>json</alert_format>
</integration>

# Restart Wazuh
sudo systemctl restart wazuh-manager
📊 Sample Alert
🚨 Wazuh Security Alert 🔴

🎯 Severity: CRITICAL (Level 12)
📋 Rule: Multiple authentication failures
🔢 Rule ID: 31151
📅 Time: 2025-07-21 14:30:45 UTC

🖥️ Agent: web-server-01 (192.168.1.100)
📍 Location: /var/log/auth.log
🌐 Source IP: 192.168.1.200
👤 User: admin

🔧 Enhanced Wazuh Telegram Integration v2.0.0
👨‍💻 Developed by Mursal Aliyev
📋 Requirements

Wazuh Server 4.0+
Python 3.6+
Telegram Bot Token
Chat ID

🧪 Testing
bashsudo python3 /var/ossec/integrations/test_integration.py YOUR_BOT_TOKEN
🔍 Troubleshooting
bash# Check logs
sudo tail -f /var/ossec/logs/telegram_integration.log

# Verify permissions
sudo ls -la /var/ossec/integrations/custom-telegram*
