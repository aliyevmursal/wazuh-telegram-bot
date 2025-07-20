#!/bin/bash
# Enhanced Wazuh Telegram Integration Installer
# Author Mursal Aliyev
# GitHub: https://github.com/aliyevmursal/wazuh-telegram-bot

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

WAZUH_PATH="/var/ossec"
INTEGRATION_PATH="$WAZUH_PATH/integrations"
CONFIG_FILE="$INTEGRATION_PATH/telegram_config.json"
LOG_FILE="$WAZUH_PATH/logs/telegram_integration.log"
REPO_URL="https://raw.githubusercontent.com/aliyevmursal/wazuh-telegram-bot/main"

echo -e "${BLUE}========================================${NC}"
echo -e "${PURPLE}Enhanced Wazuh Telegram Integration${NC}"
echo -e "${PURPLE}Author Mursal Aliyev${NC}"
echo -e "${PURPLE}GitHub: github.com/aliyevmursal/wazuh-telegram-bot${NC}"
echo -e "${BLUE}========================================${NC}"

# Check root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root${NC}"
   exit 1
fi

# Check Wazuh installation
if [ ! -d "$WAZUH_PATH" ]; then
    echo -e "${RED}❌ Wazuh installation not found at $WAZUH_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Wazuh installation found${NC}"

# Check Python version
PYTHON_VERSION=$($WAZUH_PATH/framework/python/bin/python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅ Python version: $PYTHON_VERSION${NC}"

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
$WAZUH_PATH/framework/python/bin/python3 -m pip install --upgrade pip
$WAZUH_PATH/framework/python/bin/python3 -m pip install requests urllib3

# Create integration directory
mkdir -p "$INTEGRATION_PATH"
mkdir -p "$(dirname "$LOG_FILE")"

# Download integration files
echo -e "${YELLOW}📥 Downloading integration files...${NC}"

# Download custom-telegram (executable)
if curl -sSL "$REPO_URL/custom-telegram" -o /tmp/custom-telegram; then
    cp /tmp/custom-telegram "$INTEGRATION_PATH/"
    echo -e "${GREEN}✅ Downloaded custom-telegram${NC}"
else
    echo -e "${RED}❌ Failed to download custom-telegram${NC}"
    exit 1
fi

# Download custom-telegram.py
if curl -sSL "$REPO_URL/custom-telegram.py" -o /tmp/custom-telegram.py; then
    cp /tmp/custom-telegram.py "$INTEGRATION_PATH/"
    echo -e "${GREEN}✅ Downloaded custom-telegram.py${NC}"
else
    echo -e "${RED}❌ Failed to download custom-telegram.py${NC}"
    exit 1
fi

# Download telegram_config.json
if curl -sSL "$REPO_URL/telegram_config.json" -o /tmp/telegram_config.json; then
    if [ ! -f "$CONFIG_FILE" ]; then
        cp /tmp/telegram_config.json "$CONFIG_FILE"
        echo -e "${GREEN}✅ Downloaded telegram_config.json${NC}"
    else
        echo -e "${YELLOW}⚠️  Configuration file already exists, skipping...${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Could not download config, creating default...${NC}"
    # Create default config if download fails
    cat > "$CONFIG_FILE" << 'EOF'
{
  "chat_id": "",
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
    "exclude_rules": [],
    "include_only_rules": [],
    "exclude_agents": [],
    "include_only_agents": []
  },
  "message_templates": {
    "default": true,
    "custom_header": "",
    "custom_footer": "\n\n<i>🔧 Enhanced Wazuh Telegram Integration v2.0.0</i>\n<i>👨‍💻 Developed by Mursal Aliyev</i>"
  }
}
EOF
fi

# Set permissions
echo -e "${YELLOW}🔐 Setting permissions...${NC}"
chown root:wazuh "$INTEGRATION_PATH/custom-telegram"*
chmod 750 "$INTEGRATION_PATH/custom-telegram"*
chown root:wazuh "$CONFIG_FILE"
chmod 640 "$CONFIG_FILE"

# Setup logging
echo -e "${YELLOW}📝 Setting up logging...${NC}"
touch "$LOG_FILE"
chown wazuh:wazuh "$LOG_FILE"
chmod 640 "$LOG_FILE"

# Setup logrotate
cat > /etc/logrotate.d/wazuh-telegram << 'EOF'
/var/ossec/logs/telegram_integration.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su wazuh wazuh
}
EOF

# Create test script
echo -e "${YELLOW}🧪 Creating test script...${NC}"
cat > "$INTEGRATION_PATH/test_integration.py" << 'EOF'
#!/usr/bin/env python3
"""
Test script for Enhanced Wazuh Telegram Integration
Developed by Mursal Aliyev
"""

import json
import sys
import os
import tempfile
from datetime import datetime

def create_test_alert():
    """Create a test alert for testing"""
    test_alert = {
        "timestamp": datetime.now().isoformat() + "Z",
        "rule": {
            "level": 10,
            "id": "31151",
            "description": "Multiple authentication failures detected - TEST ALERT",
            "groups": ["authentication_failed", "authentication_failures"]
        },
        "agent": {
            "id": "001",
            "name": "test-server",
            "ip": "192.168.1.100"
        },
        "location": "/var/log/auth.log",
        "srcip": "192.168.1.200",
        "user": "admin",
        "program_name": "sshd",
        "full_log": "TEST: Failed password for admin from 192.168.1.200 port 22 ssh2"
    }
    return test_alert

def main():
    print("Enhanced Wazuh Telegram Integration - Test Script")
    print("Developed by Mursal Aliyev")
    print("=" * 50)
    
    if len(sys.argv) != 2:
        print("Usage: test_integration.py <bot_api_key>")
        print("Example: python3 test_integration.py 123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        sys.exit(1)
    
    bot_api_key = sys.argv[1]
    hook_url = f"https://api.telegram.org/bot{bot_api_key}/sendMessage"
    
    # Create temporary alert file
    test_alert = create_test_alert()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_alert, f)
        alert_file = f.name
    
    try:
        # Import and run the integration
        sys.path.insert(0, '/var/ossec/integrations')
        from custom_telegram import WazuhTelegramIntegration
        
        integration = WazuhTelegramIntegration()
        success = integration.process_alert(alert_file, hook_url)
        
        if success:
            print("✅ Test message sent successfully!")
            print("Check your Telegram chat for the test alert.")
        else:
            print("❌ Failed to send test message")
            print("Check the logs: sudo tail -f /var/ossec/logs/telegram_integration.log")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have configured the chat_id in telegram_config.json")
    finally:
        # Clean up
        os.unlink(alert_file)

if __name__ == "__main__":
    main()
EOF

chmod +x "$INTEGRATION_PATH/test_integration.py"
chown root:wazuh "$INTEGRATION_PATH/test_integration.py"

# Clean up temporary files
rm -f /tmp/custom-telegram /tmp/custom-telegram.py /tmp/telegram_config.json

echo -e "${GREEN}🎉 Installation completed successfully!${NC}"
echo -e ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}📋 CONFIGURATION STEPS:${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e ""
echo -e "${YELLOW}1. Configure Telegram Chat ID:${NC}"
echo -e "   ${PURPLE}sudo nano $CONFIG_FILE${NC}"
echo -e "   ${PURPLE}Add your chat_id (e.g., \"-1001234567890\")${NC}"
echo -e ""
echo -e "${YELLOW}2. Add Integration to Wazuh Configuration:${NC}"
echo -e "   ${PURPLE}sudo nano $WAZUH_PATH/etc/ossec.conf${NC}"
echo -e ""
echo -e "${YELLOW}   Add this configuration block:${NC}"
echo -e "${GREEN}<integration>${NC}"
echo -e "${GREEN}    <n>custom-telegram</n>${NC}"
echo -e "${GREEN}    <level>8</level>${NC}"
echo -e "${GREEN}    <hook_url>https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage</hook_url>${NC}"
echo -e "${GREEN}    <alert_format>json</alert_format>${NC}"
echo -e "${GREEN}</integration>${NC}"
echo -e ""
echo -e "${RED}   ⚠️  Replace <YOUR_BOT_TOKEN> with your actual bot token!${NC}"
echo -e ""
echo -e "${YELLOW}3. Test the Integration:${NC}"
echo -e "   ${PURPLE}sudo python3 $INTEGRATION_PATH/test_integration.py <YOUR_BOT_TOKEN>${NC}"
echo -e ""
echo -e "${YELLOW}4. Restart Wazuh Manager:${NC}"
echo -e "   ${PURPLE}sudo systemctl restart wazuh-manager${NC}"
echo -e "   ${PURPLE}sudo systemctl status wazuh-manager${NC}"
echo -e ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}📊 File Locations:${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "• Configuration: ${PURPLE}$CONFIG_FILE${NC}"
echo -e "• Logs: ${PURPLE}$LOG_FILE${NC}"
echo -e "• Integration files: ${PURPLE}$INTEGRATION_PATH/custom-telegram*${NC}"
echo -e "• Test script: ${PURPLE}$INTEGRATION_PATH/test_integration.py${NC}"
echo -e ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}📖 Example ossec.conf Integration Blocks:${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e ""
echo -e "${YELLOW}# For Critical Alerts (Level 12+):${NC}"
echo -e "${GREEN}<integration>${NC}"
echo -e "${GREEN}    <n>custom-telegram</n>${NC}"
echo -e "${GREEN}    <level>12</level>${NC}"
echo -e "${GREEN}    <hook_url>https://api.telegram.org/bot<TOKEN>/sendMessage</hook_url>${NC}"
echo -e "${GREEN}    <alert_format>json</alert_format>${NC}"
echo -e "${GREEN}</integration>${NC}"
echo -e ""
echo -e "${YELLOW}# For Authentication Failures:${NC}"
echo -e "${GREEN}<integration>${NC}"
echo -e "${GREEN}    <n>custom-telegram</n>${NC}"
echo -e "${GREEN}    <group>authentication_failed</group>${NC}"
echo -e "${GREEN}    <hook_url>https://api.telegram.org/bot<TOKEN>/sendMessage</hook_url>${NC}"
echo -e "${GREEN}    <alert_format>json</alert_format>${NC}"
echo -e "${GREEN}</integration>${NC}"
echo -e ""
echo -e "${GREEN}Thank you for using Enhanced Wazuh Telegram Integration!${NC}"
echo -e "${PURPLE}⭐ Star the repository: https://github.com/aliyevmursal/wazuh-telegram-bot${NC}"
echo -e "${PURPLE}🐛 Report issues: https://github.com/aliyevmursal/wazuh-telegram-bot/issues${NC}"
echo -e "${PURPLE}👨‍💻 Developed with ❤️  by Mursal Aliyev${NC}"
